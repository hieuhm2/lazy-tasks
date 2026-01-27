"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status indicating the service is healthy.
    """
    return {"status": "healthy"}


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.

    Returns:
        Welcome message.
    """
    return {"message": "PAEA - Personal AI Executive Assistant"}
