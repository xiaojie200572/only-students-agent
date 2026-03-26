from fastapi import APIRouter
from app.schemas.request import SyncRequest
from app.schemas.response import SyncResponse
from app.vector.ingest import NoteIngestor

router = APIRouter()
ingestor = NoteIngestor()


@router.post("/sync")
async def sync_notes(request: SyncRequest):
    count = await ingestor.sync_notes(
        full_sync=request.full_sync,
        since_id=request.since_id,
    )
    return SyncResponse(
        success=True,
        synced_count=count,
        message=f"Successfully synced {count} notes",
    )


@router.get("/status")
async def get_status():
    status = ingestor.get_sync_status()
    return status
