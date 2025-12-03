
1. Đặt code từ file "ohstem.py" vào web app.ohstem.py

2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:MQTT_BROKER='mqtt.ohstem.vn'
$env:MQTT_PORT='1883'
$env:MQTT_USER='1234'
$env:MQTT_PASS='1234'
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Frontend

```powershell
cd frontend
npm install
npm run dev
```
