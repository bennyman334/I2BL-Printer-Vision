import serial
import time

# === CONFIGURATION ===
PORT = '/dev/tty.usbmodem3446395A32311'  # <-- Replace with your port
BAUD = 115200                      # Or 250000 depending on your firmware
TIMEOUT = 1

def sendToPoints(x_center, y_center):
    # === CONNECT TO BOARD ===
    print("Connecting to {}...".format(PORT))
    ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
    time.sleep(2)  # Wait for board to auto-reset

    # === FLUSH INITIAL MESSAGES ===
    ser.reset_input_buffer()

    def send_gcode(cmd):
        print(">> {}".format(cmd))
        ser.write((cmd + '\n').encode())

        while True:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print("<< {}".format(line))
            if 'ok' in line.lower():
                break

    # === SEND TEST COMMANDS ===
    #getOrigin() ==> outputs x and y displacement coordinates

    #assign them to X_origin and Y_origin
    
    # clamp_distance = 20
    # send_gcode("G28 C")
    # send_gcode("G1 C{} F100".format(clamp_distance))   # Move X to the origin's point
    # send_gcode("G92 C0")   # Home 

    X_origin = x_center
    Y_origin = y_center

    send_gcode("G91")           # Relative positioning
    send_gcode("G1 X{} F200".format(X_origin))   # Move X to the origin's point
    send_gcode("G1 Y{} F200".format(Y_origin))  #Move Y to the origin's point

    send_gcode("G92 X0 Y0") #home x and y coordinates at the new origin

    # === CLEAN UP ===
    ser.close()
    print("Done.")

#sendToPoints(-15, -15)