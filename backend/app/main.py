from fastapi import FastAPI

from app.routers import auth

# Todo vive bajo /api: el frontend (nginx o el proxy de `ng serve`) reenvía /api al backend,
# así navegador y API comparten origen y no hace falta CORS.
app = FastAPI(
    title="Bodeguita API", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None
)

app.include_router(auth.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
