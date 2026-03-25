from server.application import app
from server.runtime import settings


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=settings.APP_PORT, reload=False)
