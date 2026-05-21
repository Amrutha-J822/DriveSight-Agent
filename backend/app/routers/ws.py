from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.progress import progress_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/progress/{case_id}")
async def progress_socket(websocket: WebSocket, case_id: str) -> None:
    await progress_manager.connect(case_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.disconnect(case_id, websocket)
