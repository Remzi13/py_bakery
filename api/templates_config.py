from fastapi.templating import Jinja2Templates
from api.utils import get_resource_path
from api.version import APP_VERSION
import os

def get_db_version():
    from sql_model.database import SessionLocal
    from sql_model.entities import SystemSettings
    db = SessionLocal()
    try:
        version = db.query(SystemSettings).filter(SystemSettings.key == 'db_version').first()
        return version.value if version else "unknown"
    except Exception:
        return "error"
    finally:
        db.close()

templates = Jinja2Templates(directory=get_resource_path("templates"))
templates.env.globals["app_version"] = APP_VERSION
templates.env.globals["get_db_version"] = get_db_version
