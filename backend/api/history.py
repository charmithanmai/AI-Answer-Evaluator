from fastapi import APIRouter

from backend.database import clear_history, get_history

router = APIRouter()


@router.get("/history")
def history(limit: int = 50):
    return get_history(limit)


@router.delete("/history")
def delete_history():
    deleted = clear_history()
    return {"deleted": deleted}

