# DFS-02: Image Generation Layer — Technology Deep-Dive

**Date:** 2026-05-02
**Scope:** Critical evaluation of image creation technologies for restaurant Instagram content
**Research Phase:** Depth-First Technology Evaluation
**Author:** Research Assembly for Sabrika Brand Manager

---

## 1. The "Organic" Constraint

The user repeatedly emphasizes: **"It has to be completely organic."**

This means:
- Not obviously AI-generated (no extra fingers, weird text, surreal artifacts)
- Restaurant-branded (consistent colors, fonts, logo placement)
- Contextually appropriate (food, ambiance, offers that match the actual restaurant)
- Varied (not identical templates every day)

We evaluate four generation paradigms.

---

## 2. Paradigm A: Template-Based Generation (Pillow/HTML)

### 2.1 Technical Implementation

```python
from PIL import Image, ImageDraw, ImageFont

# 1080x1920 for Stories, 1080x1080 for Posts
img = Image.new('RGB', (1080, 1920), color='#FF6B35')
draw = ImageDraw.Draw(img)

# Gradient background
draw_gradient(draw, width, height, color1, color2)

# Branded text
draw.text((center_x, y), restaurant_name, font=title_font, fill='white')
draw.text((center_x, y+120), event_text, font=event_font, fill='white')
draw.text((center_x, y+300), offer_text, font=offer_font, fill='white')

# Save
img.save('story_restaurant_001.png')
```

### 2.2 Advanced Techniques (2025-2026)

| Technique | Implementation | Visual Impact |
|-----------|---------------|---------------|
| **Perlin Noise Overlay** | `PIL.ImageFilter` + random noise | Subtle texture, organic feel |
| **Gradient Mesh** | Multi-stop color interpolation | Premium, modern look |
| **Dynamic Typography** | Font scaling based on text length | Always readable, never clipped |
| **Emoji Integration** | Unicode rendering via Segoe UI Emoji | Visual shortcuts (🍕📍🎉) |
| **QR Code Injection** | `qrcode` library for offers | Scannable discounts |
| **Photo Overlay** | Blend actual restaurant photos with template | Authenticity + branding |

### 2.3 Real-World Precedent: FoodGenius

FoodGenius Labs (Germany) auto-generates **weekly lunch menus, promotional offers, social media posts, and WhatsApp updates** using template-based automation [^1]:

> "Customers get their data — like a lunch plan or weekly menu — and we automatically fill in the template variables. Then we create outputs for different channels: images, PDFs, digital displays, and website content." [^1]

**Result:** Restaurant chain with multiple locations eliminated manual InDesign/Figma work. Local teams now feel ownership while central management maintains brand consistency.

### 2.4 Evaluation

| Dimension | Score | Notes |
|-----------|-------|-------|
| Speed | 10/10 | <1 second per image |
| Cost | 10/10 | Zero marginal cost |
| Brand Consistency | 10/10 | Templates enforce brand rules |
| "Organic" Feel | 7/10 | Clean but obviously designed, not photographed |
| Variety | 5/10 | Same templates; requires many templates to feel fresh |
| Maintenance | 9/10 | Add new templates as needed |
| **Weighted Total** | **8.5/10** | |

---

## 3. Paradigm B: AI Diffusion Models (Stable Diffusion / ComfyUI)

### 3.1 Technical Stack

```
[Text Prompt] → [ComfyUI Node Graph] → [Stable Diffusion XL/Flux] → [Generated Image]
                      ↓
              [ControlNet for structure]
                      ↓
              [LoRA for food/restaurant style]
                      ↓
              [Inpainting for text overlay]
```

### 3.2 State of the Art (2026)

| Model | Parameters | Best For | VRAM Required |
|-------|-----------|----------|---------------|
| **Stable Diffusion XL** | 3.5B | General purpose, well-documented | 6-8GB |
| **SDXL Turbo** | 3.5B | Real-time generation (4 steps) | 6GB |
| **Flux.1 [dev]** | 12B | Highest quality, text rendering | 16-24GB |
| **SD 3.5 Medium** | 2B | Balanced quality/speed | 5-6GB |
| **PixArt-Σ** | 600M | Efficient, good for product shots | 4GB |

### 3.3 ComfyUI: The Production Interface

ComfyUI is the dominant open-source interface for diffusion models in 2025-2026 [^2][^3]:

- **Node-based workflow:** Visual programming of image pipelines
- **Reproducibility:** Save and share workflows as JSON files
- **Extensibility:** 2000+ custom nodes via ComfyUI Manager
- **API Mode:** Headless server for programmatic generation
- **Deployment Options:** Local, RunPod, Vast.ai, Google Colab

### 3.4 Restaurant-Specific Workflows

A typical ComfyUI workflow for restaurant content:

```
[Prompt: "Professional food photography of biryani on 
          terracotta plate, warm lighting, restaurant table,
          shallow depth of field, 50mm lens"]
          ↓
    [KSampler] → [VAE Decode] → [Save Image]
          ↓
    [ControlNet OpenPose] — optional for composition
          ↓
    [LoRA: Indian-Food-Style-v2] — style consistency
```

### 3.5 The "Organic" Problem with Pure AI

| Issue | Example | Mitigation |
|-------|---------|------------|
| Hallucinated food | 7-fingered chicken wing | Use img2img with real photos |
| Nonsense text | "Srpeicla Offre!" | Generate image without text, overlay via Pillow |
| Inconsistent branding | Random colors each time | Use ControlNet + brand color palette post-processing |
| Uncanny ambiance | Floating chairs | Add depth ControlNet, human-in-loop review |

### 3.6 Evaluation

| Dimension | Score | Notes |
|-----------|-------|-------|
| Speed | 4/10 | 5-30 seconds per image (GPU); minutes on CPU |
| Cost | 6/10 | Free if local GPU; $0.50-2/hr on cloud GPU |
| Brand Consistency | 5/10 | Requires fine-tuning or LoRA training |
| "Organic" Feel | 8/10 | Can look photorealistic when done right |
| Variety | 10/10 | Infinite variation from prompts |
| Maintenance | 5/10 | Model updates, workflow debugging |
| **Weighted Total** | **6.3/10** | |

---

## 4. Paradigm C: Hybrid — AI Background + Template Overlay (RECOMMENDED)

### 4.1 Concept

Combine the **visual richness of AI** with the **brand safety of templates**:

```
Step 1: Generate background image via ComfyUI/Stable Diffusion
        ["Cozy Indian restaurant interior, warm lighting,
          decorative elements, blurred background"]
                      ↓
Step 2: Overlay branded template via Pillow
        - Restaurant name (consistent font)
        - Event text
        - Offer highlight box
        - Contact info
                      ↓
Step 3: Output final image
        1080×1920 story or 1080×1080 post
```

### 4.2 Why This Works

| Problem | Pure Template | Pure AI | Hybrid |
|---------|--------------|---------|--------|
| Looks generic | ❌ Yes | ✅ No | ✅ No |
| Brand consistent | ✅ Yes | ❌ No | ✅ Yes |
| Fast generation | ✅ Yes | ❌ Slow | ✅ Yes (bg cacheable) |
| Text readable | ✅ Yes | ❌ Often garbled | ✅ Yes (Pillow overlay) |
| Cost-effective | ✅ Yes | ⚠️ Variable | ✅ Yes (batch bg generation) |

### 4.3 Caching Strategy

For 2 restaurants × 3 posts/day = 6 images/day:

```
Pre-generate 20 background images per restaurant per month
→ Store in S3/local storage
→ Daily: select random background + overlay fresh text
→ Total AI compute: once per month, not per post
```

This brings marginal cost to near-zero after initial generation.

### 4.4 Evaluation

| Dimension | Score | Notes |
|-----------|-------|-------|
| Speed | 9/10 | <2 seconds per image (cached bg + overlay) |
| Cost | 9/10 | One-time GPU cost, then free |
| Brand Consistency | 9/10 | Templates enforce branding |
| "Organic" Feel | 9/10 | AI backgrounds look real; text is perfect |
| Variety | 8/10 | 20 backgrounds per month = high variety |
| Maintenance | 8/10 | Refresh backgrounds monthly |
| **Weighted Total** | **8.7/10** | |

---

## 5. Paradigm D: Real Photo Enhancement (FoodShot-style)

### 5.1 Concept

Upload actual photos from the restaurant → AI enhances → Template overlay.

### 5.2 Open-Source Alternatives to FoodShot AI

FoodShot AI ($15-99/mo) enhances phone food photos to studio quality [^4]. Open-source equivalents:

| Tool | Capability | License |
|------|-----------|---------|
| **GFPGAN** | Face restoration (for staff photos) | Apache 2.0 |
| **Real-ESRGAN** | 4x super-resolution | BSD-3 |
| **CodeFormer** | Image restoration | CC-BY-NC |
| **Rembg** | Background removal | MIT |
| **Img2img (SD)** | Style transfer, lighting correction | Various |

### 5.3 Workflow

```
[Phone photo of today's special] → [Real-ESRGAN upscale] → [Rembg remove bg]
                                          ↓
                              [Replace background with branded gradient]
                                          ↓
                              [Pillow overlay: text, offers, logo]
                                          ↓
                              [Final Instagram-ready image]
```

### 5.4 Evaluation

| Dimension | Score | Notes |
|-----------|-------|-------|
| Speed | 6/10 | Multi-step pipeline |
| Cost | 8/10 | Free tools, requires setup |
| Brand Consistency | 8/10 | Depends on overlay quality |
| "Organic" Feel | 10/10 | Real photos = maximum authenticity |
| Variety | 10/10 | Every photo is unique |
| Maintenance | 6/10 | Requires daily photo uploads |
| **Weighted Total** | **8.0/10** | |

---

## 6. Comparative Summary

| Paradigm | Speed | Cost | Organic Feel | Brand Consistency | Variety | Overall |
|----------|-------|------|-------------|-------------------|---------|---------|
| A: Pure Template (Pillow) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | **8.5** |
| B: Pure AI (ComfyUI/SD) | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | **6.3** |
| **C: Hybrid (AI BG + Template)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **8.7** |
| D: Photo Enhancement | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **8.0** |

---

## 7. Recommendation

> **Phase 1 (Immediate): Hybrid C — AI Background + Template Overlay**
> 
> - Generate 20 ambient restaurant backgrounds per month using ComfyUI with a simple prompt
> - Cache backgrounds locally
> - Daily: random background + Pillow overlay with event/context text
> - Output: Professional, branded, organic-looking content in <2 seconds
>
> **Phase 2 (Future): Photo Enhancement D**
> 
> - When restaurants start sharing daily phone photos, integrate Real-ESRGAN + Rembg pipeline
> - Enhances real content while maintaining brand overlay
> - Maximum authenticity for special events, new dishes, etc.

---

## 8. References

[^1]: CHILI Publish. "FoodGenius: Bringing Automated Marketing to Hospitality with CHILI GraFx." Case Study, March 2026. https://www.chili-publish.com/customer-foodgenius-bringing-automated-marketing-to-hospitality-with-chili-grafx/

[^2]: ComfyUI Blog. "ComfyUI V1 Release & 2024 Sitemap." ComfyOrg, 2024. https://blog.comfy.org/sitemap/2024

[^3]: BentoML. "The Best Open-Source Image Generation Models in 2026." March 2026. https://www.bentoml.com/blog/a-guide-to-open-source-image-generation-models

[^4]: FoodShot AI. "15 Best Restaurant Marketing Tools for 2026." February 2026. https://foodshot.ai/blog/best-restaurant-marketing-tools

[^5]: Playbook3D. "What is ComfyUI? Understanding Open Source AI Image Generation." July 2025. https://www.playbook3d.com/blog/what-is-comfyui-understanding-open-source-image-generation
