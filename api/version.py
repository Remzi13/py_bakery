APP_VERSION = "0.0.2"
DB_VERSION = "0.0.2"

def update_db_version(op, new_version: str):
    """Helper to update the database version in Alembic migrations."""
    op.execute(f"UPDATE system_settings SET value = '{new_version}' WHERE key = 'db_version'")
