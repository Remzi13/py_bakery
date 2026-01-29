import uvicorn
import multiprocessing
import os
import sys

# Add the current directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

if __name__ == "__main__":
    multiprocessing.freeze_support()
    # Run uvicorn programmatically
    # reload=False is important for frozen app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=False)
