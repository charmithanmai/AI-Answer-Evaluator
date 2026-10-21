from fastapi import APIRouter

from backend.database import get_history

router = APIRouter()


@router.get("/history")
def history(limit: int = 50):
    return get_history(limit)
