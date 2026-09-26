from pathlib import Path
import uvicorn
from config import APP_HOST, APP_PORT

if __name__ == "__main__":
    uvicorn.run("api.main:app", host=APP_HOST, port=APP_PORT, app_dir=str(Path(__file__).parent))
