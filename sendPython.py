import serial
import time

# === CONFIGURATION ===
PORT = '/dev/tty.usbmodem3446395A32311'  # <-- Replace with your port
BAUD = 115200                      # Or 250000 depending on your firmware
TIMEOUT = 1

def sendToPoints(x_center = 0, y_center = 0, points = [], z_dist = 0, z_homing = False, homing = False, extrusion = False):
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

    if(extrusion):
        send_gcode("G91")
        send_gcode("G1 B0.33 F200")
        time.sleep(1)
        send_gcode("G1 B-0.2 F300")
        send_gcode("G1 Z0.2 F100")

        for i in range (10):
            send_gcode("G3 X0 Y0 I{} J0 F200".format(0.2+i*0.03))
            send_gcode("G1 Z0.15 F100")
        time.sleep(2)
        send_gcode("G1 Z3 F100")
        return None

    if(homing):
        send_gcode("G91")
    elif (z_homing):
        send_gcode("G28 Z")           # Relative positioning
    else:
        send_gcode("G92 X0 Y0 Z0")
        send_gcode("G90")
    #print(x_center, y_center, z_dist)
    if(x_center != 0 or y_center != 0 or z_dist != 0):
        send_gcode("G1 X{} F200".format(x_center))   # Move X to the origin's point
        send_gcode("G1 Y{} F200".format(y_center))
        send_gcode("G1 Z{} F200".format(z_dist))

    for coord in points:
        if (len(coord)==3):
            send_gcode("G1 X{} F200".format(coord[0]))
            send_gcode("G1 Y{} F200".format(coord[1]))
            send_gcode("G1 Z{} F200".format(coord[2]))
        else:
            send_gcode("G1 X{} F200".format(coord[0]))
            send_gcode("G1 Y{} F200".format(coord[1]))
    # X_origin = x_center
    # Y_origin = y_center
    # Z_dist = z_dist

    # send_gcode("G1 X{} F200".format(X_origin))   # Move X to the origin's point
    # send_gcode("G1 Y{} F200".format(Y_origin))  #Move Y to the origin's point
    # send_gcode("G1 Z{} F200".format(Z_dist)) #Move to specified Z-distance
    if (homing): #only home if specifically specified
        send_gcode("G92 X0 Y0") #home x and y coordinates at the new origin
    # === CLEAN UP ===
    ser.close()
    print("Done.")

# def extrude():
#     print("Work in Progress!")

#sendToPoints(extrusion=True)