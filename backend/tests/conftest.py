import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_import_db_directory = tempfile.TemporaryDirectory(prefix="cybersoc-import-test-")
_import_db_path = Path(_import_db_directory.name) / "import.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_import_db_path.as_posix()}"

from app.database import Base, engine as import_engine, get_db
from app.main import app
from app.crud import ensure_seed_data


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestSessionLocal() as db:
        ensure_seed_data(db)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def remove_import_database():
    yield
    import_engine.dispose()
    _import_db_directory.cleanup()
