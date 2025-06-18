import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import uvicorn

# ElevenLabs credentials
ELEVENLABS_API_KEY = "ssk_62ec3836156ea5c9de88fcdb92f5eb38ed38aaff4aaa0d0a"
VOICE_ID = "FmBhnvP58BK0vz65OOj7"
ASSISTANT_ID = "GgXCveESK4aBwmr2MawB"

# WebSocket URL
ELEVENLABS_WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ASSISTANT_ID}"

app = FastAPI()

@app.get("/")
async def health():
    return PlainTextResponse("✅ WebSocket server is live")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 TeleCMI connected")

    try:
        async with websockets.connect(
            ELEVENLABS_WS_URL,
            extra_headers={"xi-api-key": ELEVENLABS_API_KEY}
        ) as eleven_ws:
            print("🧠 Connected to ElevenLabs")

            # Step 1: Start conversation
            initial_msg = {
                "text": "Hi! I'm your assistant. How can I help you?",
                "voice_id": VOICE_ID,
                "start_conversation": True
            }
            await eleven_ws.send(json.dumps(initial_msg))

            async def receive_from_elevenlabs():
                async for msg in eleven_ws:
                    data = json.loads(msg)

                    # 🏓 Respond to ping
                    if data.get("type") == "ping":
                        await eleven_ws.send(json.dumps({
                            "type": "pong",
                            "event_id": data["ping_event"]["event_id"]
                        }))

                    # 🔊 Handle audio response
                    elif data.get("type") == "audio":
                        audio_b64 = data["audio_event"].get("audio_base_64")
                        if audio_b64:
                            await websocket.send_text(json.dumps({
                                "event": "media",
                                "media": {
                                    "payload": audio_b64
                                }
                            }))
                            print("🔊 Sent audio to TeleCMI")

                    # 🔁 Optional: clear screen or reset on interruption
                    elif data.get("type") == "interruption":
                        await websocket.send_text(json.dumps({
                            "event": "clear"
                        }))

            async def receive_from_telecmi():
                async for msg in websocket.iter_text():
                    print("📥 TeleCMI →", msg)
                    try:
                        data = json.loads(msg)
                        if data.get("event") == "media":
                            payload = data.get("media", {}).get("payload")
                            if payload:
                                await eleven_ws.send(json.dumps({
                                    "user_audio_chunk": payload
                                }))
                        elif data.get("event") == "stop":
                            await eleven_ws.close()
                    except Exception as e:
                        print("❌ TeleCMI parse error:", e)

            await asyncio.gather(receive_from_telecmi(), receive_from_elevenlabs())

    except Exception as e:
        print("❌ Error:", str(e))
        await websocket.send_text(f"Error: {str(e)}")

    finally:
        await websocket.close()
        print("🔴 WebSocket connection closed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8500, reload=True)
