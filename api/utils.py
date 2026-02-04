import sys
import os
from pathlib import Path

def get_base_path() -> Path:
    """
    Get the base path of the application.
    If running as a PyInstaller bundle, returns the directory of the executable.
    Otherwise, returns the current working directory (or project root).
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS.
        
        # However, for accessing external files (like database next to exe),
        # we usually want sys.executable directory.
        # But if we bundle resources (templates/static) INSIDE the exe/dir (using --add-data),
        # they might be in sys._MEIPASS (onefile) or sys.executable dir (onedir).
        
        # Strategy:
        # If we use --onedir, sys._MEIPASS is not always used unless we use --onefile.
        # But commonly, with --onedir the files are just next to the exe.
        
        # Let's support both. If sys._MEIPASS exists, checking there for internal resources might be needed.
        # But for "run locally from folder", usually we want the folder containing the executable.
        
        return Path(sys.executable).parent
    else:
        # Normal python run
        return Path(os.getcwd())

def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, working for both development
    and PyInstaller builds.
    
    If bundled with --add-data, resources might be in sys._MEIPASS (onefile).
    If using --onedir, they are likely in the base path.
    """
    if getattr(sys, 'frozen', False):
        # Look in _MEIPASS first if it exists (for onefile bundled resources)
        if hasattr(sys, '_MEIPASS'):
             base_path = Path(sys._MEIPASS)
             full_path = base_path / relative_path
             if full_path.exists():
                 return str(full_path)
        
        # Fallback to executable directory (onedir or external resources)
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(os.getcwd())
        
    return str(base_path / relative_path)

def get_database_url() -> str:
    """
    Get the database URL, ensuring it points to a file next to the executable
    when frozen.
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")

    db_name = "bakery_management.db"
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
        db_path = base_path / db_name
        return f"sqlite:///{db_path}"
    else:
        return f"sqlite:///./{db_name}"
