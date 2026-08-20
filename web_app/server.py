import serial
import time
import threading
from flask import Flask, jsonify, render_template
from flask_cors import CORS

SERIAL_PORT = 'COM7'  # Change to your port (e.g., 'COM3', 'COM4' or '/dev/ttyUSB0')
BAUD_RATE = 9600

app = Flask(__name__, template_folder='templates')
CORS(app)

latest_telemetry = {
    "temperature": 0.0,
    "humidity": 0.0,
    "predicted_heat_index": 0.0,
    "timestamp": ""
}

def read_serial_worker():
    global latest_telemetry
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)
        print(f"[SUCCESS] Serial connected to {SERIAL_PORT}")
        
        while True:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            if raw_line and not raw_line.startswith("ERROR") and not raw_line.startswith("EcoPulse"):
                parts = raw_line.split(',')
                if len(parts) == 3:
                    try:
                        latest_telemetry = {
                            "temperature": float(parts[0]),
                            "humidity": float(parts[1]),
                            "predicted_heat_index": float(parts[2]),
                            "timestamp": time.strftime("%H:%M:%S")
                        }
                    except ValueError:
                        pass
    except Exception as e:
        print(f"[ERROR] Serial connection failed: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/telemetry')
def get_telemetry():
    return jsonify(latest_telemetry)

if __name__ == '__main__':
    # Start serial reading in a background thread
    threading.Thread(target=read_serial_worker, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)