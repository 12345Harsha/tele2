from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse

import os

app = FastAPI()

@app.get("/")
async def root():
    return PlainTextResponse("Hello from Python!")

# Simple WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Hello from Python WebSocket!")
    await websocket.close()
