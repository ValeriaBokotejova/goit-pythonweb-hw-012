import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static folder for serving static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join("app", "static", "favicon.ico"))


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}
