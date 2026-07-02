from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/status")
async def get_status():
    """Get system status"""
    return {"status": "operational"}
