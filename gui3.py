import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import camFeed
import subprocess
import ast
import livefeed_measurements
import numpy as np
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

venv_python = "rfenv/bin/python"
target_script = "locateCircles.py"


class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Microneedle Assembly - Dashboard (Camera Only)")
        self.geometry("1100x650")
        self.resizable(True, True)

        self.centers = []
        self.extrusion_num = 0
        self.calavg = 0.0663
        self.imageCenter = (960, 540)
        self.pause_camera = False  # Prevent camera lag during interactions

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(
            self.sidebar,
            text="   Microneedle Assembly Assistant   ",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 40))

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

        # Main camera area
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

    # ---------- Kept functions ----------
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
                        distances = [
                            euclidean_distance(coord, other)
                            for j, other in enumerate(self.centers) if i != j
                        ]
                        min_two = sorted(distances)[:2]
                        print(f"Coord {coord} -> two smallest distances: {min_two}")

                except Exception as e:
                    self.show_toast("Error decoding output!", duration=3000)
                    print("Error decoding JSON from subprocess:", result.stdout, e)
                    self.centers = []
            else:
                self.show_toast("Error running target.py!", duration=3000)
                print("Error running target.py:", result.stderr)
                self.centers = []
        # Run in a thread to avoid freezing GUI
        threading.Thread(target=calibration_task, daemon=True).start()

    def run_screenshot(self):
        self.show_toast("Snapshot Taken")
        threading.Thread(target=camFeed.main, daemon=True).start()

    def run_conversion(self):
        self.show_toast("Running Conversion")
        # self.calavg = livefeed_measurements.main()  # If needed
        print("SELF", self.calavg)

    # ---------- UI helpers & camera loop ----------
    def show_toast(self, message, duration=2000):
        width = 320
        height = 60
        x = self.winfo_x() + 20
        y = self.winfo_y() + self.winfo_height() - height - 40

        toast = ctk.CTkToplevel(self)
        toast.geometry(f"{width}x{height}+{x}+{y}")
        toast.overrideredirect(True)
        toast.configure(fg_color="#34d399", bg_color="#34d399")
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
                # draw detected centers (from calibration)
                for center in self.centers:
                    try:
                        x, y = int(center[0]), int(center[1])
                        cv2.circle(frame, (x, y), radius=1, color=(0, 0, 255), thickness=3)
                    except Exception as e:
                        print("Error drawing center:", center, e)

                # draw image center
                h, w = frame.shape[:2]
                center_x, center_y = w // 2, h // 2
                self.imageCenter = (center_x, center_y)
                cv2.circle(frame, (self.imageCenter[0], self.imageCenter[1]), radius=1, color=(255, 0, 0), thickness=3)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.img_label.configure(image=imgtk, text="")
                self.img_label.image = imgtk

        self.after(30, self.update_camera_feed)

    def on_closing(self):
        self.cap.release()
        self.destroy()


if __name__ == "__main__":
    app = DashboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
