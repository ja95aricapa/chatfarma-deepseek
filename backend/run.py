import uvicorn
from fastapi import FastAPI

if __name__ == "__main__":
    uvicorn.run("backend_main:app", host="127.0.0.1", port=8000, log_level="info")
