import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

# Locate templates directory relative to app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
REACT_INDEX = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "dist", "index.html"))


def react_shell():
	return FileResponse(REACT_INDEX) if os.path.exists(REACT_INDEX) else None
