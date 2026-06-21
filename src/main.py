from fastapi import FastAPI

app = FastAPI(title="Obsidian AI Clipper")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
