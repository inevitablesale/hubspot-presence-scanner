"""
Tests for OpenAI email rewriter functionality.

These tests verify that:
1. The rewriter returns original content when OpenAI is not available
2. The rewriter handles missing API key gracefully
3. The rewriter handles OpenAI errors gracefully
4. The rewriter returns rewritten content when successful
5. The metadata tracks rewrite status correctly
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the global client before each test."""
    import prospectpilot.openai_email_rewriter as rewriter
    rewriter._client = None
    yield
    rewriter._client = None


class TestGetClient:
    """Test _get_client function."""

    def test_returns_none_when_no_api_key(self):
        """Test that None is returned when OPENAI_API_KEY is not set."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        with patch.dict(os.environ, {}, clear=True):
            # Remove OPENAI_API_KEY if present
            os.environ.pop("OPENAI_API_KEY", None)
            rewriter._client = None
            
            client = rewriter._get_client()
            assert client is None

    def test_returns_none_when_openai_not_installed(self):
        """Test that None is returned when openai package is not available."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            original_openai = rewriter.OpenAI
            rewriter.OpenAI = None
            rewriter._client = None
            
            try:
                client = rewriter._get_client()
                assert client is None
            finally:
                rewriter.OpenAI = original_openai

    def test_caches_client(self):
        """Test that the client is cached after first creation."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        mock_client = MagicMock()
        mock_openai_class = MagicMock(return_value=mock_client)
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            rewriter.OpenAI = mock_openai_class
            rewriter._client = None
            
            # First call creates client
            client1 = rewriter._get_client()
            # Second call returns cached client
            client2 = rewriter._get_client()
            
            assert client1 is client2
            assert mock_openai_class.call_count == 1


class TestRewriteEmailWithOpenai:
    """Test rewrite_email_with_openai function."""

    def test_returns_original_when_no_client(self):
        """Test that original content is returned when client is not available."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            rewriter._client = None
            
            subject, body, meta = rewriter.rewrite_email_with_openai(
                subject="Original Subject",
                body="Original Body",
                context={"domain": "example.com"},
            )
            
            assert subject == "Original Subject"
            assert body == "Original Body"
            assert meta["rewrite_used"] is False
            assert meta["rewrite_reason"] == "no_client"

    def test_returns_rewritten_content_on_success(self):
        """Test that rewritten content is returned on successful API call."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        # Create mock response
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "subject": "New Subject",
            "body": "New Body"
        })
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Set up the module with mock client
        rewriter._client = mock_client
        
        subject, body, meta = rewriter.rewrite_email_with_openai(
            subject="Original Subject",
            body="Original Body",
            context={"domain": "example.com"},
        )
        
        assert subject == "New Subject"
        assert body == "New Body"
        assert meta["rewrite_used"] is True
        assert meta["rewrite_reason"] == "success"

    def test_returns_original_on_api_error(self):
        """Test that original content is returned when API call fails."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        rewriter._client = mock_client
        
        subject, body, meta = rewriter.rewrite_email_with_openai(
            subject="Original Subject",
            body="Original Body",
            context={"domain": "example.com"},
        )
        
        assert subject == "Original Subject"
        assert body == "Original Body"
        assert meta["rewrite_used"] is False
        assert "error:" in meta["rewrite_reason"]

    def test_returns_original_on_invalid_json_response(self):
        """Test that original content is returned when API returns invalid JSON."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        mock_message = MagicMock()
        mock_message.content = "not valid json"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        rewriter._client = mock_client
        
        subject, body, meta = rewriter.rewrite_email_with_openai(
            subject="Original Subject",
            body="Original Body",
            context={"domain": "example.com"},
        )
        
        assert subject == "Original Subject"
        assert body == "Original Body"
        assert meta["rewrite_used"] is False
        assert "error:" in meta["rewrite_reason"]

    def test_metadata_includes_model_and_temperature(self):
        """Test that metadata includes model and temperature settings."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            rewriter._client = None
            
            _, _, meta = rewriter.rewrite_email_with_openai(
                subject="Test",
                body="Test",
                context={},
            )
            
            assert "rewrite_model" in meta
            assert "rewrite_temperature" in meta

    def test_falls_back_to_original_when_subject_missing(self):
        """Test fallback when API response is missing subject."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        mock_message = MagicMock()
        mock_message.content = json.dumps({"body": "New Body"})
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        rewriter._client = mock_client
        
        subject, body, meta = rewriter.rewrite_email_with_openai(
            subject="Original Subject",
            body="Original Body",
            context={},
        )
        
        assert subject == "Original Subject"
        assert body == "New Body"
        assert meta["rewrite_used"] is True

    def test_falls_back_to_original_when_body_missing(self):
        """Test fallback when API response is missing body."""
        import prospectpilot.openai_email_rewriter as rewriter
        
        mock_message = MagicMock()
        mock_message.content = json.dumps({"subject": "New Subject"})
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        rewriter._client = mock_client
        
        subject, body, meta = rewriter.rewrite_email_with_openai(
            subject="Original Subject",
            body="Original Body",
            context={},
        )
        
        assert subject == "New Subject"
        assert body == "Original Body"
        assert meta["rewrite_used"] is True


class TestEmailGeneratorIntegration:
    """Test integration with email_generator module."""

    def test_generate_persona_outreach_email_includes_metadata(self):
        """Test that generate_persona_outreach_email includes rewrite metadata."""
        from prospectpilot.email_generator import generate_persona_outreach_email
        
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            
            import prospectpilot.openai_email_rewriter as rewriter
            rewriter._client = None
            
            email = generate_persona_outreach_email(
                domain="example.com",
                main_tech="Shopify",
                supporting_techs=["Klaviyo"],
                from_email="test@example.com",
            )
            
            assert "rewrite_used" in email.metadata
            assert "rewrite_model" in email.metadata
            assert "rewrite_temperature" in email.metadata

    def test_generate_persona_outreach_email_with_mock_openai(self):
        """Test email generation with mocked OpenAI success."""
        from prospectpilot.email_generator import generate_persona_outreach_email
        import prospectpilot.openai_email_rewriter as rewriter
        
        # Create mock response
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "subject": "Rewritten Subject",
            "body": "Rewritten Body"
        })
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        rewriter._client = mock_client
        
        email = generate_persona_outreach_email(
            domain="example.com",
            main_tech="Shopify",
            supporting_techs=["Klaviyo"],
            from_email="test@example.com",
        )
        
        assert email.subject == "Rewritten Subject"
        assert email.body == "Rewritten Body"
        assert email.metadata["rewrite_used"] is True
        assert email.metadata["rewrite_reason"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
