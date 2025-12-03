## app.ohstem.py
# Chạy trên app.ohstem.vn để đọc dữ liệu MQTT và điều khiển bơm thông qua ML model
from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from event_manager import *
import time
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20
import requests
import json

event_manager.reset()
aiot_dht20 = DHT20()

# Pin điều khiển bơm (relay) - kết nối vào P1
pump_pin = Pin('P1', Pin.OUT)

# Lưu trữ giá trị cảm biến mới nhất
sensor_data = {
    'V1': 0,  # Nhiệt độ
    'V2': 0,  # Độ ẩm không khí
    'V3': 0,  # Độ ẩm đất
}

def on_event_timer_callback_K_z_e_A_R():
    """
    1. Đọc cảm biến (nhiệt độ, độ ẩm không khí, độ ẩm đất)
    2. Publish lên MQTT (V1, V2, V3)
    3. Gọi API /api/predict của backend để lấy quyết định điều khiển bơm
    4. Điều khiển relay bơm dựa trên kết quả dự đoán
    """
    try:
        # Đọc dữ liệu cảm biến
        temp = temperature()  # V1: Nhiệt độ từ DHT20
        humidity = aiot_dht20.dht20_humidity()  # V2: Độ ẩm không khí từ DHT20
        moisture_raw = pin1.read_analog()  # V3: Độ ẩm đất (0-1023)
        
        # Normalize độ ẩm đất từ 0-1023 sang 0-100%
        moisture_percent = (moisture_raw / 1023.0) * 100
        
        # Cập nhật giá trị cảm biến
        sensor_data['V1'] = temp
        sensor_data['V2'] = humidity
        sensor_data['V3'] = moisture_percent
        
        # Publish dữ liệu cảm biến lên MQTT broker
        mqtt.publish('V1', str(temp))
        mqtt.publish('V2', str(humidity))
        mqtt.publish('V3', str(int(moisture_percent)))
        
        # Gọi API backend để dự đoán trạng thái bơm
        # URL backend (thay localhost bằng IP/hostname của server chạy backend)
        backend_url = 'http://localhost:8000/api/predict'
        
        payload = {
            'moisture': moisture_percent,
            'temp': temp
        }
        
        try:
            response = requests.post(backend_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                pump_state = result.get('pump_control', 'OFF')
                
                # Điều khiển relay bơm
                if pump_state == 'ON':
                    pump_pin.write_digital(1)
                    display.scroll('PUMP ON')
                else:
                    pump_pin.write_digital(0)
                    display.scroll('PUMP OFF')
            else:
                print(f"API error: {response.status_code}")
                pump_pin.write_digital(0)  # Tắt bơm nếu có lỗi
                
        except Exception as e:
            print(f"Request error: {e}")
            pump_pin.write_digital(0)  # Tắt bơm nếu có lỗi kết nối
            
    except Exception as e:
        print(f"Sensor read error: {e}")
        pump_pin.write_digital(0)  # Tắt bơm nếu có lỗi đọc cảm biến

# Thêm event timer: gọi callback mỗi 10 giây
event_manager.add_timer_event(10000, on_event_timer_callback_K_z_e_A_R)

# Khởi tạo kết nối
if True:
    display.scroll('IOT')
    mqtt.connect_wifi('iPhone_2028', '0989108848')
    mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='1234', password='1234')
    display.scroll('OK')

# Vòng lặp chính
while True:
    event_manager.run()
    mqtt.check_message()
    time.sleep_ms(5000)
    time.sleep_ms(10)
