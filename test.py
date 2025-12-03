import pickle
import pandas as pd

MODEL_FILENAME = 'model.pkl'

def map_pump_status(pred):
    return 'ON' if pred == 1 else 'OFF'

# Nhập dữ liệu
moisture = float(input("Độ ẩm đất (moisture): "))
temp = float(input("Nhiệt độ (temp): "))

# Tải mô hình
try:
    with open(MODEL_FILENAME, 'rb') as file:
        model = pickle.load(file)
except FileNotFoundError:
    print(f"Lỗi: Không tìm thấy file '{MODEL_FILENAME}'")
    exit()

X_new = pd.DataFrame([[moisture, temp]], columns=['moisture', 'temp'])
pred = model.predict(X_new)[0]
result = map_pump_status(pred)
print(f"\nTrạng thái: {result}")
