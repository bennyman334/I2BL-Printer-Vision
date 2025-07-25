import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import camFeed
import subprocess
import ast
import livefeed_measurements
import numpy as np

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

venv_python = "/Users/abdulsalamraja/extrusionTargetI2BL/rfenv/bin/python"
target_script = "/Users/abdulsalamraja/extrusionTargetI2BL/locateCircles.py"

class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Microneedle Assembly - Dashboard")
        self.geometry("1100x650")
        self.resizable(True, True)

        self.centers = []
        self.calavg = 0.0
        self.imageCenter = (0, 0)

        # ---- Sidebar ----
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=18, fg_color="#181c20")
        self.sidebar.pack(side="left", fill="y", padx=(18, 0), pady=18)

        ctk.CTkLabel(
            self.sidebar,
            text="🧬\nMicroneedle Assembly Assistant",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#fff"
        ).pack(pady=(26, 44))

        # Buttons with more padding and icons
        self._sidebar_button("📸  Snapshot", self.run_screenshot).pack(fill="x", padx=20, pady=(0, 16))
        self._sidebar_button("🎯  Calibrate", self.run_target).pack(fill="x", padx=20, pady=(0, 16))
        self._sidebar_button("🔄  Run Conversion", self.run_conversion).pack(fill="x", padx=20, pady=(0, 16))
        self._sidebar_button("🏠  Home (Top Right)", self.find_top_right).pack(fill="x", padx=20, pady=(0, 16))

        # ---- Main Content Area ----
        self.content = ctk.CTkFrame(self, fg_color="#23272e", corner_radius=22)
        self.content.pack(side="left", fill="both", expand=True, padx=18, pady=18)

        # Stats Cards at top
        self.stats_frame = ctk.CTkFrame(self.content, fg_color="#23272e", corner_radius=20)
        self.stats_frame.pack(fill="x", padx=14, pady=(14, 0))

        self.stat_card_1 = self._stat_card("Calibration Status", "Ready", "#6366f1", 0)
        self.stat_card_1.pack(side="left", padx=(0, 18), pady=8)
        self.stat_card_2 = self._stat_card("Average", f"{self.calavg:.2f}", "#34d399", 1)
        self.stat_card_2.pack(side="left", padx=(0, 18), pady=8)
        self.stat_card_3 = self._stat_card("Centers", f"{len(self.centers)}", "#f59e42", 2)
        self.stat_card_3.pack(side="left", pady=8)

        # Camera feed in a rounded frame
        self.camera_panel = ctk.CTkFrame(self.content, fg_color="#21242b", corner_radius=24, width=800, height=500)
        self.camera_panel.pack(padx=24, pady=(18, 8), expand=True)

        ctk.CTkLabel(
            self.camera_panel,
            text="Live Camera Feed",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#fff"
        ).pack(anchor="n", pady=(14, 4))

        self.img_label = ctk.CTkLabel(self.camera_panel, text="Camera feed here")
        self.img_label.pack(pady=(8, 0), expand=True)

        # Start camera feed
        self.cap = cv2.VideoCapture(0)
        self.update_camera_feed()

    # --- Helper to create sidebar button ---
    def _sidebar_button(self, text, command):
        return ctk.CTkButton(
            self.sidebar,
            text=text,
            height=46,
            fg_color="#23272e",
            hover_color="#6366f1",  # Accent on hover
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e5e7eb",
            corner_radius=16,
            command=command,
        )

    # --- Helper to create a stat card ---
    def _stat_card(self, label, value, color, index):
        card = ctk.CTkFrame(self.stats_frame, fg_color="#252c38", corner_radius=18, width=160, height=70)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=14), text_color="#cbd5e1").pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=20, weight="bold"), text_color=color).pack(anchor="w", padx=16)
        return card

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
                self.centers = []
            self.update_stats()
        # Run in a thread to avoid freezing GUI
        threading.Thread(target=calibration_task, daemon=True).start()

    def run_screenshot(self):
        self.show_toast("Snapshot Taken")
        threading.Thread(target=camFeed.main, daemon=True).start()

    def run_conversion(self):
        self.show_toast("Running Conversion")
        self.calavg = livefeed_measurements.main()  # Just call directly, no thread
        print("SELF", self.calavg)
        self.update_stats()

    def show_toast(self, message, duration=2000):
        width = 320
        height = 60
        x = self.winfo_x() + 30
        y = self.winfo_y() + self.winfo_height() - height - 46
        toast = ctk.CTkToplevel(self)
        toast.geometry(f"{width}x{height}+{x}+{y}")
        toast.overrideredirect(True)
        toast.configure(fg_color="#34d399", bg_color="#34d399")
        toast.attributes("-topmost", True)
        # Add a white border for "drop shadow"
        border = ctk.CTkFrame(toast, fg_color="#e5e7eb", corner_radius=18)
        border.place(relx=0, rely=0, relwidth=1, relheight=1)
        label = ctk.CTkLabel(border, text=message, text_color="#222", font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(expand=True)
        toast.lift()
        self.after(duration, toast.destroy)

    def update_camera_feed(self):
        ret, frame = self.cap.read()
        if ret:
            # Draw red dots for each center (if any)
            for center in self.centers:
                try:
                    x, y = int(center[0]), int(center[1])
                    cv2.circle(frame, (x, y), radius=1, color=(0, 0, 255), thickness=3)
                except Exception as e:
                    print("Error drawing center:", center, e)

            # Draw a blue dot in the center of the frame
            h, w = frame.shape[:2]
            center_x, center_y = w // 2, h // 2
            self.imageCenter = (center_x, center_y)
            cv2.circle(frame, (center_x, center_y), radius=1, color=(255, 0, 0), thickness=3)  # Blue dot

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.img_label.configure(image=imgtk, text="")  # Update the image
            self.img_label.image = imgtk  # Store reference!

        self.after(30, self.update_camera_feed)

    def find_top_right(self):
        # Sort centers by x value in descending order and take the top 3
        top_three = sorted(self.centers, key=lambda c: c[0], reverse=True)[:3]
        minimum = top_three[0]
        for i in top_three:
            if i[1] < minimum[1]:
                minimum = i

        num_min = np.array(minimum)
        image_center = np.array(self.imageCenter)
        vect = num_min - image_center
        vect_normalized = vect * self.calavg
        print(vect, vect_normalized)

    def update_stats(self):
        # Update your stat cards with the latest values
        for widget in self.stat_card_2.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.stat_card_2, text="Average", font=ctk.CTkFont(size=14), text_color="#cbd5e1").pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(self.stat_card_2, text=f"{self.calavg:.2f}", font=ctk.CTkFont(size=20, weight="bold"), text_color="#34d399").pack(anchor="w", padx=16)

        for widget in self.stat_card_3.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.stat_card_3, text="Centers", font=ctk.CTkFont(size=14), text_color="#cbd5e1").pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(self.stat_card_3, text=f"{len(self.centers)}", font=ctk.CTkFont(size=20, weight="bold"), text_color="#f59e42").pack(anchor="w", padx=16)

    def on_closing(self):
        self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = DashboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
