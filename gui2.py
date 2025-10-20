import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import camFeed
import subprocess
import ast
import livefeed_measurements
import numpy as np
from sendPython import sendToPoints
import serial.tools.list_ports
import time
import math

def list_serial_ports():
    """Returns a list of available serial port device names."""
    return [port.device for port in serial.tools.list_ports.comports()]

#PORT = '/dev/tty.usbmodem3446395A32311'  # <-- Replace with your port
PORT = '/dev/cu.usbmodem3446395A32311'  # <-- Replace with your port
BAUD = 115200                      # Or 250000 depending on your firmware
TIMEOUT = 1

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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

venv_python = "rfenv/bin/python"
target_script = "locateCircles.py"


class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Microneedle Assembly - Dashboard")
        self.geometry("1100x650")
        self.resizable(True, True)

        self.centers = []
        self.extrusion_num = 0
        self.calavg = 0.0663
        self.imageCenter = (960,540)
        #self.imageCenter = (955,504)
        self.pause_camera = False  # Prevent camera lag during dropdown interaction

        self.displacements = []
        self.syringeOffsets = np.array([0.6, -24.3, -60])
        #self.syringeOffsets = np.array([0.4, -24.5, -60])
        #self.syringeOffsets = np.array([-3.6, -25.7, -60]) #x, y, z offsets to bring syringe to top right hole
        #np.array([-0.6, -30.7, -61]) #displacements to get to the top right corner
        #24.5

        # Sidebar
                # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(
            self.sidebar,
            text="   Microneedle Assembly Assistant   ",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 40))

        # Port Dropdown + Refresh
        # self.port_var = ctk.StringVar()
        # self.port_dropdown = ctk.CTkComboBox(
        #     self.sidebar,
        #     variable=self.port_var,
        #     values=list_serial_ports(),
        #     width=180,
        #     state="readonly",
        #     font=ctk.CTkFont(size=14),
        # )
        # self.port_dropdown.pack(pady=(0, 18), padx=20)

        # self.refresh_ports_button = ctk.CTkButton(
        #     self.sidebar,
        #     text="🔄 Refresh Ports",
        #     height=28,
        #     fg_color="#23272e",
        #     font=ctk.CTkFont(size=14),
        #     command=self.refresh_ports
        # )
        # self.refresh_ports_button.pack(fill="x", padx=20, pady=(0, 16))

        # === First Control Group (Snapshot, Calibrate, Run Conversion) ===
        self.control_group_1 = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e")
        self.control_group_1.pack(fill="x", padx=14, pady=(0, 20))

        ctk.CTkButton(
            self.control_group_1,
            text="Snapshot",
            height=40,
            fg_color="#23272e",
            command=self.run_screenshot,
        ).pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkButton(
            self.control_group_1,
            text="Calibrate Holes",
            height=40,
            fg_color="#23272e",
            command=self.run_target,
        ).pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.control_group_1,
            text="Run Conversion",
            height=40,
            fg_color="#23272e",
            command=self.run_conversion,
        ).pack(fill="x", padx=10, pady=(0, 10))

        # === Second Control Group (Home, Extrude) ===
        self.control_group_2 = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e")
        self.control_group_2.pack(fill="x", padx=14, pady=(0, 20))

        ctk.CTkButton(
            self.control_group_1,
            text="Home (Top Right)",
            height=40,
            fg_color="#23272e",
            command=self.find_top_right,
        ).pack(fill="x", padx=10, pady=(10, 10))

        # ctk.CTkButton(
        #     self.control_group_2,
        #     text="Home (Center)",
        #     height=40,
        #     fg_color="#23272e",
        #     command=self.find_top_right,
        # ).pack(fill="x", padx=10, pady=(10, 10))

        # ctk.CTkButton(
        #     self.control_group_2,
        #     text="Extrude All Points",
        #     height=40,
        #     fg_color="#23272e",
        #     command=self.extrude_points,
        # ).pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.control_group_2,
            text="Test Extrusions",
            height=40,
            fg_color="#23272e",
            command=self.test_extrusions,
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            self.control_group_2,
            text="Lower Syringe",
            height=40,
            fg_color="#23272e",
            command=self.moveSyringe,
        ).pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.control_group_2,
            text="Next Extrusion",
            height=40,
            fg_color="#23272e",
            command=self.next_extrusion,
        ).pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.control_group_2,
            text="Extrude All",
            height=40,
            fg_color="#23272e",
            command=self.extrude_all,
        ).pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.control_group_2,
            text="Home Z-Axis",
            height=40,
            fg_color="#23272e",
            command= self.home_z,
        ).pack(fill="x", padx=10, pady=(0, 10))


        # === XYZ Controls ===
        self.xyz_controls = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e")
        self.xyz_controls.pack(fill="x", padx=14, pady=(0, 10))

        # XY movement buttons
        xy_grid = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        xy_grid.pack(pady=8)

        self.z_step_var = ctk.StringVar(value="1")

        # ↑
        ctk.CTkButton(xy_grid, text="↑", width=50, height=30,command= lambda: self.GUI_move("Y", -float(self.z_step_var.get()))
                      #sendToPoints(0, 0, points=[[0, -float(self.z_step_var.get())]],homing=True)
                      ).grid(row=0, column=1, pady=2)
        # ← ↓ →
        ctk.CTkButton(xy_grid, text="←", width=50, height=30,command=lambda: self.GUI_move("X", float(self.z_step_var.get()))
                      #sendToPoints(0, 0, points=[[float(self.z_step_var.get()),0]],homing=True))
                      ).grid(row=1, column=0, padx=2)
        
        ctk.CTkButton(xy_grid, text="→", width=50, height=30,command=lambda: self.GUI_move("X", -float(self.z_step_var.get()))
                      #sendToPoints(0, 0, points=[[-float(self.z_step_var.get()),0]],homing=True)).grid(row=1, column=2, padx=2)
                      ).grid(row=1, column=2, padx=2)
        # ↓
        ctk.CTkButton(xy_grid, text="↓", width=50, height=30,command=lambda: self.GUI_move("Y", float(self.z_step_var.get()))
                      #sendToPoints(0, 0, points=[[0, float(self.z_step_var.get())]],homing=True)).grid(row=2, column=1, pady=2)
                      ).grid(row=2, column=1, pady=2)

        # Z-axis label with dropdown
        # z_frame = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        # z_frame.pack(fill="x", padx=10, pady=(8, 4))

        # ctk.CTkLabel(z_frame, text="Z Axis").pack(side="left")

        # # Granularity dropdown in top-right of box
        # self.z_step_var = ctk.StringVar(value="1")
        # z_dropdown = ctk.CTkComboBox(
        #     z_frame,
        #     values=["0.1", "1", "10"],
        #     variable=self.z_step_var,
        #     width=60,
        #     height=24,
        #     font=ctk.CTkFont(size=12),
        #     state="readonly"
        # )
        # z_dropdown.pack(side="right")

        z_frame = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        z_frame.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(z_frame, text="Z Axis").pack(side="left")

        z_entry = ctk.CTkEntry(
            z_frame,
            textvariable=self.z_step_var,
            width=60,
            height=24,
            font=ctk.CTkFont(size=12),
            justify="right"
        )
        z_entry.pack(side="right")


        # Pause camera feed while dropdown is open
        # z_dropdown.bind("<FocusIn>", lambda e: self.set_camera_pause(True))
        # z_dropdown.bind("<FocusOut>", lambda e: self.set_camera_pause(False))


        # Z up/down buttons
        zb_buttons = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        zb_buttons.pack(pady=(4, 10))
        ctk.CTkButton(
            zb_buttons,
            text="Z ↑",
            width=80,
            height=30,
            command=lambda: self.GUI_move("Z", float(self.z_step_var.get()))
        ).grid(row=0, column=0, padx=5, pady=4)

        ctk.CTkButton(
            zb_buttons,
            text="Z ↓",
            width=80,
            height=30,
            command=lambda: self.GUI_move("Z", -float(self.z_step_var.get()))
        ).grid(row=1, column=0, padx=5, pady=4)

        # b_buttons = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        # b_buttons.pack(pady=(4, 10))
        ctk.CTkButton(
            zb_buttons,
            text="B ↑",
            width=80,
            height=30,
            command=lambda: self.GUI_move("B", -float(self.z_step_var.get()))
        ).grid(row=0, column=1, padx=5, pady=4)

        ctk.CTkButton(
            zb_buttons,
            text="B ↓",
            width=80,
            height=30,
            command=lambda: self.GUI_move("B", float(self.z_step_var.get()))
        ).grid(row=1, column=1, padx=5, pady=4)


        # Main camera area (fills almost all the right side)
        self.camera_panel = ctk.CTkFrame(
            self, fg_color="#23272e", corner_radius=15, width=830, height=630
        )
        self.camera_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self.camera_panel,
            text="Live Camera Feed",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="n", pady=(14, 4))

        self.img_label = ctk.CTkLabel(self.camera_panel, text="Camera feed here")
        self.img_label.pack(pady=(8, 0), expand=True)

        # Start camera feed
        self.cap = cv2.VideoCapture(0)
        self.update_camera_feed()


    def test_extrusions(self):
        send_gcode("G92 X0 Y0 Z0 B0")
        send_gcode("G90")
        B_previous = 4
        B_step = 0.1
        B_retract = -4
        X_move = 0

        for i in range(3):
            send_gcode(f"G1 X{X_move} F100")
            X_move += 4
            time.sleep(1)

            send_gcode(f"G1 Z-1.5 F100")
            send_gcode(f"G1 B{B_step + B_previous} F100")
            time.sleep(2)

            # Retraction first, slow
            send_gcode(f"G1 B{B_step + B_previous + B_retract} F300")
            time.sleep(0.15)

            # Small XY wipe
            #send_gcode(f"G1 X{X_move + 0.5} F150")

            # Slow lift
            send_gcode(f"G1 Z0 F80")

            B_previous += B_step
            time.sleep(0.5)

        send_gcode("G1 X0 Y0 Z0 F100")


    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_dropdown.configure(values=ports)
        # Optional: select the first port automatically
        if ports:
            self.port_var.set(ports[0])
        else:
            self.port_var.set('')
    
    def home_z(self):
        send_gcode("G28 Z")
    
    def GUI_move(self, direction, amount):
        send_gcode("G91")
        send_gcode(f"G1 {direction}{amount} F200")


    def run_target(self):
        self.show_toast("Calibrating ...")
        def calibration_task():
            result = subprocess.run(
                [venv_python, target_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                try:
                    self.centers = ast.literal_eval(result.stdout.strip())
                    print(self.centers)
                    self.show_toast("Calibration Complete!", duration=2000)

                    def euclidean_distance(p1, p2):
                        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

                    for i, coord in enumerate(self.centers):
                        # Compute distances to all other coordinates
                        distances = [euclidean_distance(coord, other) for j, other in enumerate(self.centers) if i != j]
                        # Sort distances and take the two smallest
                        min_two = sorted(distances)[:2]
                        print(f"Coord {coord} -> two smallest distances: {min_two}")

                except Exception as e:
                    self.show_toast("Error decoding output!", duration=3000)
                    print("Error decoding JSON from subprocess:", result.stdout, e)
                    self.centers = []
            else:
                self.show_toast("Error running target.py!", duration=3000)
                print("Error running target.py:", result.stderr)
                self.centers = [                                                                                                                                                                                                                                                                                                                                                                                                                        ]
        # Run in a thread to avoid freezing GUI
        threading.Thread(target=calibration_task, daemon=True).start()

    def run_screenshot(self):
        self.show_toast("Snapshot Taken")
        threading.Thread(target=camFeed.main, daemon=True).start()

    def run_conversion(self):
        self.show_toast("Running Conversion")
        #self.calavg = livefeed_measurements.main()  # Just call directly, no thread
        print("SELF", self.calavg)

    


    # def run_conversion(self):
    #     ret, frame = self.cap.read()
    #     self.show_toast("Running Conversion")
    #     calConst = threading.Thread(target=detect_green_region(frame,25.6,6.96), daemon=True).start()
    #     print(calConst)

    def show_toast(self, message, duration=2000):
        # Dimensions
        width = 320
        height = 60
        # Position at bottom left of main window
        x = self.winfo_x() + 20
        y = self.winfo_y() + self.winfo_height() - height - 40

        toast = ctk.CTkToplevel(self)
        toast.geometry(f"{width}x{height}+{x}+{y}")
        toast.overrideredirect(True)  # Remove window bar
        toast.configure(fg_color="#34d399", bg_color="#34d399")  # Light green
        ctk.CTkLabel(
            toast,
            text=message,
            text_color="#fff",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(expand=True)
        toast.lift()
        self.after(duration, toast.destroy)

    def set_camera_pause(self, state: bool):
        self.pause_camera = state


    def update_camera_feed(self):
        if not self.pause_camera:
            ret, frame = self.cap.read()
            if ret:
                for center in self.centers:
                    try:
                        x, y = int(center[0]), int(center[1])
                        cv2.circle(frame, (x, y), radius=1, color=(0, 0, 255), thickness=3)
                    except Exception as e:
                        print("Error drawing center:", center, e)

                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                self.imageCenter = (center_x, center_y)
                #self.imageCenter = (center_x, center_y)
                cv2.circle(frame, (self.imageCenter[0], self.imageCenter[1]), radius=1, color=(255, 0, 0), thickness=3)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.img_label.configure(image=imgtk, text="")
                self.img_label.image = imgtk

        self.after(30, self.update_camera_feed)

    # def pixel_to_mm(self, pt):
    #     """Convert a single pixel (x, y) point to mm using homography H."""
    #     px = np.array([pt[0], pt[1], 1.0])
    #     mm = self.H @ px
    #     mm /= mm[2]
    #     return mm[:2]

    # def find_top_right(self):
    #     # Step 1: Find the top 3 points with the largest X (right-most)
    #     top_three = sorted(self.centers, key=lambda c: c[0], reverse=True)[:3]
        
    #     # Step 2: From those, pick the one with smallest Y (top-most)
    #     top_right_px = min(top_three, key=lambda c: c[1])

    #     # Step 3: Convert image center and top-right to mm using homography
    #     top_right_mm = self.pixel_to_mm(top_right_px)
    #     image_center_mm = self.pixel_to_mm(self.imageCenter)

    #     # Step 4: Compute mm vector from center to top-right
    #     vect_mm = top_right_mm - image_center_mm

    #     # Step 5: Compute displacements from top-right to all other centers (in mm)
    #     self.displacements = []
    #     for hole in self.centers:
    #         hole_mm = self.pixel_to_mm(hole)
    #         dist = top_right_mm - hole_mm
    #         dist[0] *= -1  # reverse X for your printer coordinate system if needed
    #         self.displacements.append(dist)

    #     print("Displacement vectors (mm):", self.displacements)
    #     print("Vector to top-right (mm):", vect_mm)

    #     sendToPoints(x_center=vect_mm[0], y_center=-vect_mm[1], homing=True)




    def find_top_right(self):
        # Sort centers by x value in descending order and take the top 3
        top_three = sorted(self.centers, key=lambda c: c[0], reverse=True)[:3]
        minimum = top_three[0]
        for i in top_three: 
            if i[1]<minimum[1]: 
                minimum = i 
        
        num_min = np.array(minimum, dtype=float)
        image_center = np.array(self.imageCenter)
        vect = num_min-image_center
        print("Vector", vect)
        vect_normalized = vect*self.calavg

        self.displacements = []
        self.extrusion_num = 0
        for holes in self.centers:
            coord = np.array(holes, dtype=float)
            dist = num_min - coord
            dist*=self.calavg
            dist[0] *= -1
            #dist[1]*= -1

            self.displacements.append(dist)
            #print(dist)

        print(self.displacements)
        print(vect, vect_normalized)
        x_center = vect_normalized[0]
        y_center = -1*vect_normalized[1]
        send_gcode("G91")
        send_gcode(f"G1 X{x_center} F200")
        send_gcode(f"G1 Y{y_center} F200")
        send_gcode("G92 X0 Y0") #home

        #sendToPoints(x_center = vect_normalized[0], y_center = -1*vect_normalized[1], homing=True)


    def find_center(self):
        try:
            print("[INFO] Running find_center_point...")
            print(f"[INFO] Detected {len(self.centers)} center points: {self.centers}")

            image_center = np.array(self.imageCenter, dtype=float)

            # Step 1: Find the point closest to the image center
            closest = min(self.centers, key=lambda pt: np.linalg.norm(np.array(pt, dtype=float) - image_center))
            closest_np = np.array(closest, dtype=float)
            print(f"[DEBUG] Closest point to image center: {closest}")

            # Step 2: Vector from image center to this point
            vect = closest_np - image_center
            vect_normalized = vect * self.calavg  # use homography here if available

            # Step 3: Displacement vectors from center point to all others
            self.displacements = []
            for i, pt in enumerate(self.centers):
                pt_np = np.array(pt, dtype=float)
                dist = closest_np - pt_np
                dist *= self.calavg
                dist[0] *= -1  # flip X if needed
                self.displacements.append(dist)
                print(f"[DEBUG] Displacement from center to point {i}: {dist}")

            print("[RESULT] Center displacement vector (mm):", vect_normalized)
            sendToPoints(x_center=vect_normalized[0], y_center=-vect_normalized[1], homing=True)

        except Exception as e:
            print(f"[ERROR] find_center_point failed: {e}")

    def extrude_points(self):
        #adjust Z-axis HERE FIRST!!! <------------------
        print("hello!!!")
        print(len(self.displacements))

        toPoints = self.displacements
        sendToPoints(points = toPoints)
    
    def next_extrusion(self):
        #adjust Z-axis HERE FIRST!!! <------------------
        if(self.extrusion_num == 0):
            send_gcode("G92 X0 Y0")
            send_gcode("G90")
            print(self.displacements)
        if(self.extrusion_num < len(self.displacements)):
            send_gcode("G90")
            print("Extrusion Number:", self.extrusion_num)
            coord = self.displacements[self.extrusion_num]
            x_move = coord[0]
            y_move = coord[1]
            send_gcode(f"G1 X{x_move} F100")
            send_gcode(f"G1 Y{y_move} F100")
            self.extrusion_num += 1
        else:
            print("Already Extruded All Points!")

    def extrude_all(self):
        #adjust Z-axis HERE FIRST!!! <------------------
        send_gcode("G92 X0 Y0 Z0 B0")
        send_gcode("G90")
        count = 0
        B_previous = 4
        B_step = 0.1
        B_retract = -4
        for move_dist in self.displacements:
            x_move = move_dist[0]
            y_move = move_dist[1]
            send_gcode(f"G1 X{x_move} F100")
            send_gcode(f"G1 Y{y_move} F100")
            time.sleep(1)

            #Extrude
            send_gcode(f"G1 Z-1.5 F100")
            send_gcode(f"G1 B{B_step + B_previous} F100")
            time.sleep(2)

            # Retraction first, slow
            send_gcode(f"G1 B{B_step + B_previous + B_retract} F300")
            time.sleep(0.15)

            # Slow lift
            send_gcode(f"G1 Z0 F80")
            B_previous += B_step
            time.sleep(0.5)
            print("Extruded Hole: ", count)
        send_gcode("G1 X0 Y0 Z0")
        print("Extruded All Holes: ", count)


    def moveSyringe(self):
        send_gcode("G28 Z");
        send_gcode("G91")

        print(self.syringeOffsets[0], self.syringeOffsets[1], self.syringeOffsets[2])
        send_gcode(f"G1 X{self.syringeOffsets[0]}")
        send_gcode(f"G1 Y{self.syringeOffsets[1]}")
        send_gcode(f"G1 Z{self.syringeOffsets[2]}")
        #sendToPoints(z_homing=True)
        #sendToPoints(x_center = self.syringeOffsets[0], y_center = self.syringeOffsets[1], z_dist = self.syringeOffsets[2])

    def toggle_mode(self):
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if mode == "Dark" else "dark")

    def on_closing(self):
        self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = DashboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
