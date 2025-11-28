## app.ohstem.py
from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from event_manager import *
import time
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20
event_manager.reset()

aiot_dht20 = DHT20()

def on_event_timer_callback_K_z_e_A_R():

  mqtt.publish('V1', (temperature()))
  mqtt.publish('V2', (aiot_dht20.dht20_humidity()))
  mqtt.publish('V3', (pin1.read_analog()))

event_manager.add_timer_event(10000, on_event_timer_callback_K_z_e_A_R)

if True:
  display.scroll('IOT')
  mqtt.connect_wifi('iPhone_2028', '0989108848')
  mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='1234', password='1234')
  display.scroll('OK')

while True:
  event_manager.run()
  mqtt.check_message()
  time.sleep_ms(5000)
  time.sleep_ms(10)
