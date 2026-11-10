
import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, text

# Local SQLite database
local_db = Path(__file__).resolve().parent / "incident_platform.db"
sqlite_engine = create_engine(f"sqlite:///{local_db}")

# Neon PostgreSQL database
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is missing. Set it in this terminal first.")

neon_engine = create_engine(database_url)

tables_to_migrate = [
    "users",
    "incidents",
    "ai_analyses",
    "audit_logs",
]

source_metadata = MetaData()
target_metadata = MetaData()

source_metadata.reflect(bind=sqlite_engine)
target_metadata.reflect(bind=neon_engine)

with sqlite_engine.connect() as source, neon_engine.begin() as target:

    # Check that both databases contain the required tables.
    for name in tables_to_migrate:
        if name not in source_metadata.tables or name not in target_metadata.tables:
            raise RuntimeError(f"Missing table: {name}")

    # Confirm that the existing Neon administrator is safe to preserve.
    local_admin = source.execute(
        text("SELECT id, username FROM users WHERE id = 1")
    ).first()

    neon_admin = target.execute(
        text("SELECT id, username FROM users WHERE id = 1")
    ).first()

    if not local_admin or local_admin.username != "admin":
        raise RuntimeError("Local administrator check failed.")

    if not neon_admin or neon_admin.username != "admin":
        raise RuntimeError("Neon administrator check failed.")

    # Do not accidentally duplicate previously migrated records.
    for name in ["incidents", "audit_logs", "ai_analyses"]:
        count = target.execute(
            text(f"SELECT COUNT(*) FROM {name}")
        ).scalar_one()

        if count != 0:
            raise RuntimeError(
                f"Neon {name} is not empty. Migration stopped safely."
            )

    user_count = target.execute(
        text("SELECT COUNT(*) FROM users")
    ).scalar_one()

    if user_count != 1:
        raise RuntimeError("Neon users table has changed. Migration stopped.")

    # Copy users, preserving Neon administrator ID 1.
    for name in tables_to_migrate:
        source_table = source_metadata.tables[name]
        target_table = target_metadata.tables[name]

        rows = source.execute(source_table.select()).mappings().all()

        for row in rows:
            data = {
                key: value
                for key, value in row.items()
                if key in target_table.c
            }

            if name == "users" and data["id"] == 1:
                continue

            target.execute(target_table.insert().values(**data))

    # Reset PostgreSQL ID sequences after copying explicit IDs.
    for name in tables_to_migrate:
        target.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{name}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {name}), 1),
                    true
                )
                """
            )
        )

    print("Migration completed successfully!")

print("Your Neon database now contains the migrated records.")

sqlite_engine.dispose()
neon_engine.dispose()
