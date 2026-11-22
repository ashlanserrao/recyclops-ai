"""Liveness check for Render's health probe and the deploy smoke test."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
