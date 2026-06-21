from fastapi import FastAPI, Request
from fastapi.responses import Response
from src.api.routes import router as api_router
from src.web.routes import router as web_router

app = FastAPI(title="Obsidian AI Clipper")
app.include_router(api_router)
app.include_router(web_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
