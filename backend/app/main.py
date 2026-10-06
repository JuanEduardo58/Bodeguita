from app.routers import auth
from fastapi import FastAPI

app = FastAPI(title="SysCol API")

app.include_router(auth.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}