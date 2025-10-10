import serial
import time

# === CONFIG ===
PORT = '/dev/tty.usbmodem3446395A32311'  # <-- change to your port
BAUD = 115200                            # or 250000 for Marlin
TIMEOUT = 1
FILENAME = 'CFFFP_spiral copy.gcode'                   # <-- change to your file

print(f"Connecting to {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
time.sleep(2)  # give Marlin time to reset

# flush any startup messages
ser.reset_input_buffer()

def send_gcode(cmd):
    """Send a single line of G-code and wait for 'ok'."""
    print(f">> {cmd}")
    ser.write((cmd + '\n').encode())

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print(f"<< {line}")
        if 'ok' in line.lower():
            break

# === MAIN LOOP ===
send_gcode("G92 X0 Y0 Z0");
with open(FILENAME, 'r', encoding='utf-8', errors='ignore') as f:
    for raw in f:
        line = raw.strip()
        # skip blanks & comments
        if not line or line.startswith(';'):
            continue
        send_gcode(line)

print("Done sending G-code.")
ser.close()