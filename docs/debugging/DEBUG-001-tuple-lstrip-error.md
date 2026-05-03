# DEBUG-001: 'tuple' object has no attribute 'lstrip'

**Date:** 2026-05-02
**Severity:** High — Blocks image generation
**Reporter:** User (Sabrika's brother)
**Error Message:** `Error: 'tuple' object has no attribute 'lstrip'`

---

## 1. Symptom

User clicks "Generate Image" button → loading spinner renders → after delay, browser alert shows:
```
20.125.62.241:5000 says
Error: 'tuple' object has no attribute 'lstrip'
```

---

## 2. Root Cause Analysis

### 2.1 The Failure Chain

```
[User clicks Generate]
        ↓
[Frontend POST /api/generate]
        ↓
[Flask: api_generate() calls generate_story()]
        ↓
[generate_story() calls _hex_to_rgb(restaurant.get("color1", "#FF6B35"))]
        ↓
[_hex_to_rgb: hex_color = hex_color.lstrip("#")]  ← CRASH
        ↓
[Exception: 'tuple' object has no attribute 'lstrip']
        ↓
[Flask returns 500 HTML traceback page]
        ↓
[Frontend: res.json() fails on HTML → catch(err) → alert(err.message)]
```

### 2.2 Why the Error Message is Confusing

The user sees `'tuple' object has no attribute 'lstrip'` in the browser alert. **This is a Python exception message leaking into the JavaScript error handler.** The actual JavaScript error is a JSON parse failure (Flask returned HTML, not JSON). But because the Python traceback contains the tuple error, it appears in the alert via Flask's debug HTML page being parsed incorrectly.

Wait — actually, looking more carefully: the JavaScript catch block shows `err.message`. If `res.json()` fails because the response is HTML, `err.message` would be `"Unexpected token '<', \"<!DOCTYPE...\" is not valid JSON"`. 

**HOWEVER**, if Flask is in debug mode and the Werkzeug debugger intercepts the exception, or if there's middleware returning JSON errors... No, Flask debug mode returns HTML.

**Alternative hypothesis:** The error might actually be caught by Flask's default error handler and returned as JSON in some configurations. Or the user might be seeing the Python error from a different endpoint that DOES return JSON errors.

### 2.3 The Real Question: How Did color1 Become a Tuple?

`_hex_to_rgb` expects a string like `"#FF6B35"`. The error says it received a `tuple`.

**Possible pathways for tuple injection:**

| Pathway | Likelihood | Evidence |
|---------|-----------|----------|
| **A. Frontend sends array instead of string** | Low | `<input type="color">` always returns strings |
| **B. JSON file manually edited** | Medium | User or process could corrupt `restaurants.json` |
| **C. Reel engine passes tuple back to restaurant dict** | **HIGH** | `reel_engine/` modifies restaurant data in-place |
| **D. Concurrent write corruption** | Low | Single user, low traffic |
| **E. Default value fallback returns tuple** | Low | Default is `"#FF6B35"` (string) |

**Primary suspect: Pathway C — Reel Engine Mutation**

The `reel_engine/` module has its own `_hex_to_rgb` functions and processes restaurant data. If any reel engine code mutates the restaurant dictionary (e.g., caching RGB tuples back into the dict), subsequent calls to `generate_story()` would receive tuples instead of strings.

### 2.4 Code Locations with Identical Vulnerability

Three files have the same `_hex_to_rgb` function with no type checking:

1. `image_generator.py:31-33`
2. `reel_engine/thumbnail_generator.py:31-32`
3. `reel_engine/text_overlay.py:25-27`

All three will crash if passed a non-string color value.

---

## 3. Reproduction Steps

### 3.1 Direct Reproduction

```python
from image_generator import _hex_to_rgb

# This works
_hex_to_rgb("#FF6B35")  # → (255, 107, 53)

# This crashes with the exact user error
_hex_to_rgb((255, 107, 53))  # → AttributeError: 'tuple' object has no attribute 'lstrip'

# This also crashes
_hex_to_rgb([255, 107, 53])  # → AttributeError: 'list' object has no attribute 'lstrip'

# This also crashes
_hex_to_rgb(None)  # → AttributeError: 'NoneType' object has no attribute 'lstrip'
```

### 3.2 Data Corruption Reproduction

Manually edit `data/restaurants.json`:
```json
[{
  "id": 1,
  "name": "Test Restaurant",
  "color1": [255, 107, 53],
  "color2": [247, 147, 30]
}]
```

Then click Generate → **Same crash**.

---

## 4. The Fix Strategy

### 4.1 Immediate Fix: Defensive `_hex_to_rgb`

Make `_hex_to_rgb` idempotent — accept strings, tuples, lists, and None:

```python
def _hex_to_rgb(color) -> Tuple[int, int, int]:
    """Convert hex string or RGB tuple/list to RGB tuple."""
    # Already a tuple/list of 3 integers
    if isinstance(color, (tuple, list)) and len(color) == 3:
        return tuple(int(c) for c in color)
    # String hex color
    if isinstance(color, str):
        color = color.lstrip("#")
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    # None or invalid — fallback
    return (255, 107, 53)
```

### 4.2 API Hardening: Try-Except with JSON Errors

Wrap `api_generate()` in try-except to return structured JSON errors instead of HTML:

```python
@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        # ... existing logic ...
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
```

### 4.3 Frontend Fix: Display Backend Errors

Update JavaScript to check for `data.error` and display it properly:

```javascript
const data = await res.json();
if (data.error) {
    alert('Server Error: ' + data.error);
    return;
}
```

### 4.4 Data Validation: Restaurant Schema Guard

Add validation in `add_restaurant()` to ensure colors are strings:

```python
def _sanitize_color(color):
    if isinstance(color, (tuple, list)):
        return "#{:02x}{:02x}{:02x}".format(*color)
    if isinstance(color, str) and color.startswith("#"):
        return color
    return "#FF6B35"
```

---

## 5. Prevention

| Measure | Implementation |
|---------|---------------|
| Type safety | `_hex_to_rgb` accepts multiple types |
| Input validation | Sanitize colors on restaurant creation |
| API error handling | All endpoints return JSON errors |
| Frontend error display | Show server error messages, not generic alerts |
| No mutation | Reel engine must not modify restaurant dict in-place |

---

## 6. References

- Python `AttributeError` documentation: https://docs.python.org/3/library/exceptions.html#AttributeError
- Flask error handling: https://flask.palletsprojects.com/en/2.3.x/errorhandling/
- JSON schema validation pattern for REST APIs
