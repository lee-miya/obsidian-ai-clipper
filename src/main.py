from fastapi import FastAPI
from src.api.routes import router as api_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
