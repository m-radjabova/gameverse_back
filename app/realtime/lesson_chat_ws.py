from typing import Dict, Set
from fastapi import WebSocket
from uuid import UUID
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, thread_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(thread_id, set()).add(websocket)

    def disconnect(self, thread_id: UUID, websocket: WebSocket):
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]

    async def broadcast(self, thread_id: UUID, message: dict):
        if thread_id not in self.active_connections:
            return

        dead_connections = []
        text_data = json.dumps(message, default=str)

        for connection in self.active_connections[thread_id]:
            try:
                await connection.send_text(text_data)
            except:
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(thread_id, conn)


manager = ConnectionManager()