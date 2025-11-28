# Backend (FastAPI) for Smart Irrigation System

This backend connects to an MQTT broker (default: `mqtt.ohstem.vn`) and subscribes to topics `V1`, `V2`, `V3`, `V4`. It exposes:

- `GET /api/status` — returns latest values by topic
- `GET /api/history` — returns recent messages
- `WebSocket /ws` — real-time updates pushed to clients

Requirements

- Python 3.9+
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run

```powershell
# from backend folder
$env:MQTT_BROKER='mqtt.ohstem.vn'
$env:MQTT_PORT='1883'
$env:MQTT_USER='1234'
$env:MQTT_PASS='1234'
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Notes

- The code uses `asyncio-mqtt` to subscribe and forward messages to connected WebSocket clients.
- If your device publishes to different topics, update `TOPICS` in `main.py` or set appropriate subscriptions.
