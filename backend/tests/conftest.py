"""
FORTIVEX AI Sales Agent – Test Configuration
Sets up an isolated in-memory database for each test session.
"""

import os
import pytest

# Force demo mode so tests never need a real Gemini API key
os.environ.setdefault("GEMINI_API_KEY", "dummy-test-key")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_fortivex.db")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables before tests and clean up after."""
    from app.database.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown: drop test DB file
    import os as _os
    db_path = "./test_fortivex.db"
    if _os.path.exists(db_path):
        _os.remove(db_path)
