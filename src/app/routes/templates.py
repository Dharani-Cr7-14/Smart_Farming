import os
from fastapi.templating import Jinja2Templates

# Locate templates directory relative to app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
