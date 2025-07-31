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

def list_serial_ports():
    """Returns a list of available serial port device names."""
    return [port.device for port in serial.tools.list_ports.comports()]


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
        self.calavg = 0.0
        self.imageCenter = (0,0)
        self.pause_camera = False  # Prevent camera lag during dropdown interaction

        self.displacements = []

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
            text="Calibrate",
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
            self.control_group_2,
            text="Home (Top Right)",
            height=40,
            fg_color="#23272e",
            command=self.find_top_right,
        ).pack(fill="x", padx=10, pady=(10, 10))

        ctk.CTkButton(
            self.control_group_2,
            text="Extrude All Points",
            height=40,
            fg_color="#23272e",
            command=self.extrude_points,
        ).pack(fill="x", padx=10, pady=(0, 10))

        # === XYZ Controls ===
        self.xyz_controls = ctk.CTkFrame(self.sidebar, fg_color="#1e1e1e")
        self.xyz_controls.pack(fill="x", padx=14, pady=(0, 10))

        # XY movement buttons
        xy_grid = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        xy_grid.pack(pady=8)

        self.z_step_var = ctk.StringVar(value="1")

        # ↑
        ctk.CTkButton(xy_grid, text="↑", width=50, height=30,command= lambda: 
                      sendToPoints(0, 0, points=[[0, -float(self.z_step_var.get())]],homing=True)
                      ).grid(row=0, column=1, pady=2)
        # ← ↓ →
        ctk.CTkButton(xy_grid, text="←", width=50, height=30,command=lambda: 
                      sendToPoints(0, 0, points=[[float(self.z_step_var.get()),0]],homing=True)).grid(row=1, column=0, padx=2)
        
        ctk.CTkButton(xy_grid, text="→", width=50, height=30,command=lambda: 
                      sendToPoints(0, 0, points=[[-float(self.z_step_var.get()),0]],homing=True)).grid(row=1, column=2, padx=2)
        # ↓
        ctk.CTkButton(xy_grid, text="↓", width=50, height=30,command=lambda: 
                      sendToPoints(0, 0, points=[[0, float(self.z_step_var.get())]],homing=True)).grid(row=2, column=1, pady=2)

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
        z_buttons = ctk.CTkFrame(self.xyz_controls, fg_color="transparent")
        z_buttons.pack(pady=(4, 10))

        ctk.CTkButton(z_buttons, text="Z ↑", width=80, height=30, command= lambda: 
                      sendToPoints(0, 0, points=[[0, 0, int(self.z_step_var.get())]],homing=True)).pack(pady=4)
        ctk.CTkButton(z_buttons, text="Z ↓", width=80, height=30, command = lambda: 
                      sendToPoints(0, 0, points=[[0, 0, -int(self.z_step_var.get())]],homing=True)).pack()


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

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_dropdown.configure(values=ports)
        # Optional: select the first port automatically
        if ports:
            self.port_var.set(ports[0])
        else:
            self.port_var.set('')


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
        self.calavg = livefeed_measurements.main()  # Just call directly, no thread
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
                cv2.circle(frame, (center_x, center_y), radius=1, color=(255, 0, 0), thickness=3)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.img_label.configure(image=imgtk, text="")
                self.img_label.image = imgtk

        self.after(30, self.update_camera_feed)


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
        vect_normalized = vect*self.calavg

        self.displacements = []
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
        sendToPoints(x_center = vect_normalized[0], y_center = -1*vect_normalized[1], homing=True)

    def extrude_points(self):
        #adjust Z-axis HERE FIRST!!! <------------------
        print("hello!!!")
        print(len(self.displacements))

        toPoints = self.displacements
        sendToPoints(points = toPoints)

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
