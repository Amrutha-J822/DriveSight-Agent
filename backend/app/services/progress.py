from __future__ import annotations

from fastapi import WebSocket


class ProgressManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.latest: dict[str, dict] = {}

    async def connect(self, report_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(report_id, []).append(websocket)
        if report_id in self.latest:
            await websocket.send_json(self.latest[report_id])

    def disconnect(self, report_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(report_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(report_id, None)

    async def publish(self, report_id: str, status: str, progress: int, message: str) -> None:
        payload = {
            "report_id": report_id,
            "status": status,
            "progress": progress,
            "message": message,
        }
        self.latest[report_id] = payload
        disconnected: list[WebSocket] = []
        for websocket in self.active_connections.get(report_id, []):
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(report_id, websocket)


progress_manager = ProgressManager()
