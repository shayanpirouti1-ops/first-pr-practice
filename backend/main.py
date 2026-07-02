from fastapi import FastAPI
from contextlib import asynccontextmanager

app = FastAPI(title="Copytrading API", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Copytrading API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
