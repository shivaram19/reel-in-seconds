import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import app as flask_app


@pytest.fixture
def client():
    """Test client for Flask app."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client
