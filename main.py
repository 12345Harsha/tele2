from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
import uvicorn
import asyncio
import websockets
import json
import base64

# CONFIG
ELEVENLABS_API_KEY = "ssk_62ec3836156ea5c9de88fcdb92f5eb38ed38aaff4aaa0d0a"
VOICE_ID = "FmBhnvP58BK0vz65OOj7"
ASSISTANT_ID = "GgXCveESK4aBwmr2MawB"
ELEVENLABS_WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ASSISTANT_ID}"

app = FastAPI()

@app.get("/")
async def root():
    return PlainTextResponse("Hello from Python with ElevenLabs AI!")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 WebSocket client connected")

    try:
        # Connect to ElevenLabs WebSocket
        async with websockets.connect(
            ELEVENLABS_WS_URL,
            extra_headers={"xi-api-key": ELEVENLABS_API_KEY},
        ) as eleven_ws:

            # ✅ Initial greeting message
            initial_msg = {
                "text": "Hello! How can I help you today?",
                "voice_id": VOICE_ID,
                "start_conversation": True
            }
            await eleven_ws.send(json.dumps(initial_msg))
            print("📤 Sent initial text to ElevenLabs")

            # Listen to messages from ElevenLabs
            async for message in eleven_ws:
                data = json.loads(message)

                # Respond to pings
                if data.get("type") == "ping":
                    await eleven_ws.send(json.dumps({
                        "type": "pong",
                        "event_id": data["ping_event"]["event_id"]
                    }))
                    print("🔁 Pong sent")

                # Send audio to client
                elif data.get("type") == "audio":
                    audio_b64 = data["audio_event"].get("audio_base_64")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        await websocket.send_bytes(audio_bytes)
                        print("🔊 Sent audio to WebSocket client")

    except Exception as e:
        print("❌ Error:", e)
        await websocket.send_text(f"❌ Error: {str(e)}")

    finally:
        await websocket.close()
        print("🔴 WebSocket closed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8500, reload=True)
