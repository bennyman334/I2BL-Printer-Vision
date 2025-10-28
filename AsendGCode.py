import serial
import time

# === CONFIG ===
PORT = '/dev/tty.usbmodem3446395A32311'  # <-- change to your port
BAUD = 115200                            # or 250000 for Marlin
TIMEOUT = 1
FILENAME = 'CFFFP_2mm_Diameter_3x3_4mm_Dist_Trace_2 v2.gcode'                   # <-- change to your file

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

    # Wait for motion to complete if it's a move command
    if cmd.startswith('G0') or cmd.startswith('G1'):
        ser.write(('M400\n').encode())
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"<< {line}")
            if 'ok' in line.lower():
                break

# step = 2
# retract = -2

# step = 2
# retract = -1.95
# # === MAIN LOOP ===
# send_gcode("G92 X0 Y0 Z0")
# send_gcode("G91")
# send_gcode("G1 Z-1 F100")
# send_gcode(f"G1 B{step} F100")
# send_gcode(f"G1 B{retract} F350")
# time.sleep(1)
# send_gcode("G1 Z2 F100")
with open(FILENAME, 'r', encoding='utf-8', errors='ignore') as f:
    for raw in f:
        line = raw.strip()
        # skip blanks & comments
        if not line or line.startswith(';'):
            continue
        send_gcode(line)

print("Done sending G-code.")
ser.close()