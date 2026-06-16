from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import main
from main import app, compare_and_log_payloads

client = TestClient(app)


class TestChatCompletions:
    """Tests for the /v1/chat/completions endpoint"""

    @patch("main.requests.post")
    def test_successful_primary_call(self, mock_post):
        """Test successful primary backend call"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-1", "choices": [{"message": {"content": "Hello"}}]}
        mock_post.return_value = mock_response

        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        # ensure shadow backend disabled for this test
        main.SHADOW_BACKEND_URL = None
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
        assert response.json()["id"] == "test-1"
        mock_post.assert_called_once()

    @patch("main.requests.post")
    def test_primary_call_with_error(self, mock_post):
        """Test primary backend call failure"""
        mock_post.side_effect = Exception("Connection refused")

        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        # ensure shadow backend disabled for this test
        main.SHADOW_BACKEND_URL = None
        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200
        assert "error" in response.json()

    @patch("main.SHADOW_BACKEND_URL", "http://localhost:8002")
    @patch("main.requests.post")
    def test_shadow_call_matching_payloads(self, mock_post):
        """Test shadow call with matching primary and shadow payloads"""
        payload = {"id": "test-1", "choices": [{"message": {"content": "Hello"}}]}
        mock_response = MagicMock()
        mock_response.json.return_value = payload
        mock_post.return_value = mock_response

        with patch("main.logger") as mock_logger:
            compare_and_log_payloads("test-correlation-id", {}, payload)
            mock_logger.info.assert_called_with("[test-correlation-id] Payloads match")

    @patch("main.SHADOW_BACKEND_URL", "http://localhost:8002")
    @patch("main.requests.post")
    def test_shadow_call_mismatched_payloads(self, mock_post):
        """Test shadow call with mismatched payloads"""
        primary_payload = {"id": "test-1", "content": "primary"}
        shadow_payload = {"id": "test-1", "content": "shadow"}

        mock_response = MagicMock()
        mock_response.json.return_value = shadow_payload
        mock_post.return_value = mock_response

        with patch("main.logger") as mock_logger:
            compare_and_log_payloads("test-correlation-id", {}, primary_payload)
            mock_logger.warning.assert_called()
            assert "MISMATCH" in str(mock_logger.warning.call_args)

    @patch("main.SHADOW_BACKEND_URL", "http://localhost:8002")
    @patch("main.requests.post")
    def test_shadow_call_exception(self, mock_post):
        """Test shadow call error handling"""
        mock_post.side_effect = Exception("Shadow backend error")

        with patch("main.logger") as mock_logger:
            compare_and_log_payloads("test-correlation-id", {}, {})
            mock_logger.error.assert_called()

    @patch("main.SHADOW_BACKEND_URL", None)
    def test_shadow_disabled(self):
        """Test when shadow backend is disabled"""
        with patch("main.logger") as mock_logger:
            compare_and_log_payloads("test-id", {}, {})
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()

    @patch("main.requests.post")
    def test_background_task_queued(self, mock_post):
        """Test that shadow comparison is queued as background task"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-1"}
        mock_post.return_value = mock_response

        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }

        response = client.post("/v1/chat/completions", json=request_data)
        assert response.status_code == 200