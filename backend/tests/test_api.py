"""
Core backend tests for FORTIVEX AI Sales Agent.
Run with: pytest tests/ -v
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_fortivex.db"


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    return engine


@pytest.fixture(scope="session")
def test_client(test_db_engine):
    """Create a test client with a fresh test database."""
    from app.database.database import Base, get_db
    from app.main import app

    Base.metadata.create_all(bind=test_db_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Cleanup
    Base.metadata.drop_all(bind=test_db_engine)
    import os
    if os.path.exists("test_fortivex.db"):
        os.remove("test_fortivex.db")


# ============================================================
# Health Tests
# ============================================================

class TestHealth:
    def test_root_endpoint(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "FORTIVEX" in data["message"]
        assert data["status"] == "running"

    def test_health_endpoint(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data


# ============================================================
# Agent Tests
# ============================================================

class TestAgent:
    @patch("app.services.gemini_service.gemini_service.initialized", False)
    def test_chat_demo_mode(self, test_client):
        """Test chat endpoint works in demo mode."""
        response = test_client.post("/api/agent/chat", json={
            "message": "Hello, I'm interested in your products.",
            "session_id": "test-session-001",
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert "conversation_id" in data

    def test_agent_status(self, test_client):
        response = test_client.get("/api/agent/status")
        assert response.status_code == 200

    @patch("app.services.gemini_service.gemini_service.initialized", False)
    def test_chat_creates_conversation(self, test_client):
        """Verify chat creates a conversation in DB."""
        response = test_client.post("/api/agent/chat", json={
            "message": "Tell me about your pricing.",
            "session_id": "test-session-002",
        })
        assert response.status_code == 200
        data = response.json()
        conv_id = data["conversation_id"]
        assert conv_id is not None

        # Verify conversation exists
        conv_response = test_client.get(f"/api/conversations/{conv_id}")
        assert conv_response.status_code == 200

    @patch("app.services.gemini_service.gemini_service.initialized", False)
    def test_chat_session_history(self, test_client):
        """Verify multiple messages in same session work."""
        session_id = "test-session-history"
        response1 = test_client.post("/api/agent/chat", json={
            "message": "My name is John.",
            "session_id": session_id,
        })
        assert response1.status_code == 200
        conv_id = response1.json()["conversation_id"]

        response2 = test_client.post("/api/agent/chat", json={
            "message": "What products do you offer?",
            "session_id": session_id,
            "conversation_id": conv_id,
        })
        assert response2.status_code == 200

    def test_sentiment_analysis(self, test_client):
        """Test sentiment analysis endpoint."""
        with patch("app.services.gemini_service.gemini_service.analyze_sentiment") as mock:
            mock.return_value = {
                "sentiment": "POSITIVE",
                "buying_intent": "high",
                "satisfaction": "satisfied",
                "urgency": "medium",
                "objections": None,
                "confidence": 0.9,
            }
            response = test_client.post("/api/agent/sentiment", json={
                "text": "This looks amazing! I want to buy it right away."
            })
            assert response.status_code == 200
            data = response.json()
            assert data["sentiment"] == "POSITIVE"


# ============================================================
# Lead Tests
# ============================================================

class TestLeads:
    def test_create_lead(self, test_client):
        response = test_client.post("/api/leads", json={
            "name": "Jane Smith",
            "email": "jane@testcorp.com",
            "phone": "+1-555-0123",
            "company": "TestCorp",
            "industry": "Technology",
            "requirements": "Need CRM integration",
            "product_interest": "Enterprise Suite",
            "budget": "50000-100000",
            "timeline": "Q1 2026",
            "intent": "high",
            "lead_score": 85.0,
            "status": "HOT",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane Smith"
        assert data["status"] == "HOT"
        assert data["id"] is not None

    def test_list_leads(self, test_client):
        response = test_client.get("/api/leads")
        assert response.status_code == 200
        leads = response.json()
        assert isinstance(leads, list)

    def test_get_lead(self, test_client):
        # Create then get
        create_resp = test_client.post("/api/leads", json={
            "name": "Bob Test",
            "email": "bob@example.com",
            "status": "WARM",
            "lead_score": 55.0,
        })
        lead_id = create_resp.json()["id"]

        get_resp = test_client.get(f"/api/leads/{lead_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == lead_id

    def test_update_lead(self, test_client):
        create_resp = test_client.post("/api/leads", json={
            "name": "Update Test",
            "status": "COLD",
        })
        lead_id = create_resp.json()["id"]

        update_resp = test_client.put(f"/api/leads/{lead_id}", json={
            "status": "HOT",
            "lead_score": 90.0,
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "HOT"

    def test_lead_not_found(self, test_client):
        response = test_client.get("/api/leads/nonexistent-id")
        assert response.status_code == 404

    def test_filter_leads_by_status(self, test_client):
        response = test_client.get("/api/leads?status=HOT")
        assert response.status_code == 200


# ============================================================
# Appointment Tests
# ============================================================

class TestAppointments:
    def test_get_available_slots(self, test_client):
        response = test_client.get("/api/appointments/available-slots")
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert len(data["slots"]) > 0

    def test_create_appointment(self, test_client):
        response = test_client.post("/api/appointments", json={
            "customer_name": "Alice Johnson",
            "customer_email": "alice@company.com",
            "appointment_date": "2026-12-15",
            "appointment_time": "10:00",
            "purpose": "Product Demo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == "Alice Johnson"
        assert data["appointment_date"] == "2026-12-15"

    def test_duplicate_appointment_prevention(self, test_client):
        """Ensure the same slot cannot be double-booked."""
        slot_data = {
            "customer_name": "First Customer",
            "customer_email": "first@example.com",
            "appointment_date": "2026-12-16",
            "appointment_time": "14:00",
        }
        # First booking should succeed
        resp1 = test_client.post("/api/appointments", json=slot_data)
        assert resp1.status_code == 200

        # Second booking for same slot should fail
        slot_data["customer_name"] = "Second Customer"
        slot_data["customer_email"] = "second@example.com"
        resp2 = test_client.post("/api/appointments", json=slot_data)
        assert resp2.status_code == 409  # Conflict

    def test_cancel_appointment(self, test_client):
        create_resp = test_client.post("/api/appointments", json={
            "customer_name": "Cancel Test",
            "customer_email": "cancel@test.com",
            "appointment_date": "2026-12-20",
            "appointment_time": "11:00",
        })
        appt_id = create_resp.json()["id"]

        cancel_resp = test_client.delete(f"/api/appointments/{appt_id}")
        assert cancel_resp.status_code == 200


# ============================================================
# Dashboard Tests
# ============================================================

class TestDashboard:
    def test_analytics(self, test_client):
        response = test_client.get("/api/dashboard/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "total_conversations" in data
        assert "sentiment_distribution" in data
        assert "conversion_rate" in data


# ============================================================
# Voice Tests (mocked)
# ============================================================

class TestVoice:
    def test_voice_status(self, test_client):
        response = test_client.get("/api/voice/status")
        assert response.status_code == 200
        data = response.json()
        assert "whisper_available" in data
        assert "piper_available" in data

    @patch("app.services.voice_service.piper_service.synthesize")
    def test_tts_endpoint(self, mock_synth, test_client):
        """Test TTS with mocked Piper."""
        mock_synth.return_value = (b"RIFF" + b"\x00" * 100, True, False)  # (bytes, success, is_demo)
        response = test_client.post(
            "/api/voice/speak",
            data={"text": "Hello, this is a test."},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
