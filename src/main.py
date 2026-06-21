from fastapi import FastAPI
from src.api.routes import router as api_router
from src.web.routes import router as web_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)
app.include_router(web_router)


@app.get("/health")
def health():
    return {"status": "ok"}
