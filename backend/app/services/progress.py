from __future__ import annotations

from fastapi import WebSocket


class ProgressManager:
    """In-memory pub/sub for case processing progress."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.latest: dict[str, dict] = {}

    async def connect(self, case_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(case_id, []).append(websocket)
        if case_id in self.latest:
            await websocket.send_json(self.latest[case_id])

    def disconnect(self, case_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(case_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(case_id, None)

    async def publish(self, case_id: str, status: str, progress: int, message: str) -> None:
        payload = {
            "case_id": case_id,
            "status": status,
            "progress": progress,
            "message": message,
        }
        self.latest[case_id] = payload
        disconnected: list[WebSocket] = []
        for websocket in self.active_connections.get(case_id, []):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(case_id, websocket)


progress_manager = ProgressManager()
