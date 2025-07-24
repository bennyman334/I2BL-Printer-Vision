import customtkinter as ctk
from PIL import Image, ImageTk
import cv2

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Microneedle Assembly - Dashboard")
        self.geometry("1100x650")
        self.resizable(False, False)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(
            self.sidebar,
            text="   Microneedle Assembly Assistant   ",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 40))

        sidebar_btns = ["Snapshot", "Calibrate", "Approve", "Print"]
        for btn in sidebar_btns:
            ctk.CTkButton(
                self.sidebar,
                text=btn,
                height=40,
                fg_color="#23272e"
            ).pack(fill="x", padx=20, pady=(0, 12))

        # ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self.toggle_mode).pack(
        #     side="bottom", pady=30, padx=20
        # )

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

    def update_camera_feed(self):
        ret, frame = self.cap.read()
        if ret:
            # Fit to panel width, maintain aspect ratio (modify as needed)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 480))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.img_label.configure(image=imgtk, text="")
            self.img_label.image = imgtk
        self.after(30, self.update_camera_feed)

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
