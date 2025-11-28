import asyncio
import json
import os
import time
from collections import deque
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
try:
    # prefer the original asyncio-mqtt package
    from asyncio_mqtt import Client, MqttError
    _MQTT_LIB = 'asyncio-mqtt'
except Exception:
    try:
        # newer package/name
        from aiomqtt import Client, MqttError
        _MQTT_LIB = 'aiomqtt'
    except Exception:
        # give a clearer error later if no mqtt lib is available
        Client = None
        MqttError = Exception
        _MQTT_LIB = None

BROKER = os.getenv('MQTT_BROKER', 'mqtt.ohstem.vn')
PORT = int(os.getenv('MQTT_PORT', '1883'))
USERNAME = os.getenv('MQTT_USER', '1234')
PASSWORD = os.getenv('MQTT_PASS', '1234')
TOPICS = ["V1", "V2", "V3", "V4"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest: Dict[str, Any] = {}
history = deque(maxlen=1000)

# Simple connection registry for websockets
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active.discard(websocket)

    async def broadcast(self, message: str):
        to_remove = []
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(ws)

manager = ConnectionManager()

async def mqtt_worker():
    reconnect_interval = 5
    while True:
        try:
            if Client is None:
                raise RuntimeError('No supported MQTT client library (install "asyncio-mqtt" or "aiomqtt")')

            async with Client(BROKER, PORT, username=USERNAME, password=PASSWORD) as client:
                # subscribe to topics (try common subscribe API signatures)
                for t in TOPICS:
                    try:
                        await client.subscribe(t)
                    except Exception:
                        try:
                            # some libs expect a sequence of tuples
                            await client.subscribe([(t, 0)])
                        except Exception:
                            pass

                # Acquire an async iterator for incoming messages. Support different client APIs.
                messages_ctx = None
                if hasattr(client, 'unfiltered_messages'):
                    messages_ctx = client.unfiltered_messages()
                elif hasattr(client, 'messages'):
                    # aiomqtt exposes `messages()` as the messages context manager
                    messages_ctx = client.messages()
                elif hasattr(client, 'filtered_messages'):
                    # as a last resort, subscribe to wildcard and use filtered_messages
                    try:
                        await client.subscribe('#')
                        messages_ctx = client.filtered_messages('#')
                    except Exception:
                        messages_ctx = None

                if messages_ctx is None:
                    raise RuntimeError('MQTT client does not provide a compatible message iterator')

                async with messages_ctx as messages:
                    async for message in messages:
                        # message objects differ slightly across libs; handle common cases
                        topic = getattr(message, 'topic', None)
                        payload_raw = getattr(message, 'payload', None)
                        # aiomqtt may provide (topic, payload) tuples in some versions
                        if topic is None and isinstance(message, (list, tuple)) and len(message) >= 2:
                            topic, payload_raw = message[0], message[1]

                        if isinstance(topic, bytes):
                            try:
                                topic = topic.decode()
                            except Exception:
                                topic = str(topic)

                        if isinstance(payload_raw, bytes):
                            try:
                                payload = payload_raw.decode(errors='ignore')
                            except Exception:
                                payload = str(payload_raw)
                        else:
                            payload = str(payload_raw)
                        ts = time.time()
                        # store latest
                        latest[topic] = {
                            "value": payload,
                            "topic": topic,
                            "ts": ts,
                        }
                        # append to history
                        history.append({"topic": topic, "value": payload, "ts": ts})
                        # broadcast to websockets
                        try:
                            await manager.broadcast(json.dumps({"topic": topic, "value": payload, "ts": ts}))
                        except Exception:
                            pass
        except MqttError as me:
            print(f"MQTT error: {me}, reconnecting in {reconnect_interval}s")
            await asyncio.sleep(reconnect_interval)
        except Exception as e:
            print(f"Unexpected error in mqtt_worker: {e}")
            await asyncio.sleep(reconnect_interval)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(mqtt_worker())
    print(f"Started mqtt_worker background task (mqtt lib: {_MQTT_LIB})")

@app.get("/api/status")
async def get_status():
    # return latest values keyed by topic
    return {k: v for k, v in latest.items()}

@app.get("/api/history")
async def get_history(limit: int = 200):
    # return the most recent messages (up to `limit`)
    items = list(history)[-limit:]
    return items

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # on connect, send the current latest values so frontend can populate UI
        for topic, payload in latest.items():
            await websocket.send_text(json.dumps({"topic": topic, "value": payload["value"], "ts": payload["ts"]}))
        while True:
            # keep connection alive; we don't expect messages from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
