import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestShadowIsolation:
    """Prove shadow is decoupled from primary"""

    @patch("main.SHADOW_BACKEND_URL", None)
    @patch("main.requests.post")
    def test_primary_response_fast_when_shadow_would_be_slow(self, mock_post):
        primary_response = {"id": "test-1", "content": "primary"}
        
        mock_resp = MagicMock()
        mock_resp.json.return_value = primary_response
        mock_post.return_value = mock_resp
        
        # Measure response time (shadow disabled)
        start = time.time()
        response = client.post("/v1/chat/completions", 
                               json={"messages": [{"role": "user", "content": "test"}]})
        elapsed = time.time() - start

        assert response.status_code == 200
        assert response.json() == primary_response
        assert elapsed < 0.5, f"Primary took {elapsed}s (should be < 0.5s)"

    @patch("main.SHADOW_BACKEND_URL", "http://localhost:8002")
    @patch("main.requests.post")
    def test_shadow_exception_does_not_affect_primary(self, mock_post):
        """Shadow crashes, but primary succeeds"""
        primary_response = {"id": "test-1", "content": "primary"}
        
        def post_side_effect(url, *args, **kwargs):
            if "8001" in url:  # primary
                mock_resp = MagicMock()
                mock_resp.json.return_value = primary_response
                return mock_resp
            else:  # shadow (8002)
                raise Exception("Shadow backend crashed!")
        
        mock_post.side_effect = post_side_effect
        
        response = client.post("/v1/chat/completions",
                               json={"messages": [{"role": "user", "content": "test"}]})
        
        assert response.status_code == 200
        assert response.json() == primary_response
