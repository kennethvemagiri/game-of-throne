from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health():
    return {"ok": True, "stack": "fastapi", "app": "Game of Throne"}
