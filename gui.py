import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import camFeed
import cv2
from PIL import Image, ImageTk
import json
import ast

# --- PATHS ---
venv_python = "/Users/abdulsalamraja/extrusionTargetI2BL/rfenv/bin/python"
target_script = "/Users/abdulsalamraja/extrusionTargetI2BL/locateCircles.py"

# --- GLOBALS ---
centers = []

# --- FUNCTIONS ---

def run_target():
    global centers
    result = subprocess.run(
        [venv_python, target_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode == 0:
        try:
            centers = ast.literal_eval(result.stdout.strip())
            print(centers)
        except Exception as e:
            print("Error decoding JSON from subprocess:", result.stdout, e)
            centers = []
    else:
        print("Error running target.py:", result.stderr)
        centers = []

def threaded_run_target():
    # Run calibration in a thread so the GUI doesn't freeze
    threading.Thread(target=run_target, daemon=True).start()

def run_screenshot():
    # Run camFeed.main() in a thread so the GUI doesn't freeze
    threading.Thread(target=camFeed.main, daemon=True).start()

# --- TKINTER GUI SETUP ---

root = tk.Tk()
root.title("Microneedle Assembly")
root.geometry("900x450")

mainframe = ttk.Frame(root, padding=30)
mainframe.pack(fill='both', expand=True)

button_frame = ttk.Frame(mainframe)
button_frame.grid(row=0, column=0, sticky='n', padx=(0, 50))

button_style = ttk.Style()
button_style.configure("Big.TButton", font=("Helvetica", 18), padding=20)

snapshot_btn = ttk.Button(button_frame, text="Take Snapshot", style="Big.TButton", command=run_screenshot)
calibrate_btn = ttk.Button(button_frame, text="Calibrate", style="Big.TButton", command=threaded_run_target)
approve_btn = ttk.Button(button_frame, text="Approve", style="Big.TButton")
print_btn = ttk.Button(button_frame, text="Print", style="Big.TButton")

snapshot_btn.grid(row=0, column=0, pady=(0, 30), sticky='ew')
calibrate_btn.grid(row=1, column=0, pady=(0, 30), sticky='ew')
approve_btn.grid(row=2, column=0, pady=(0, 30), sticky='ew')
print_btn.grid(row=3, column=0, pady=(0, 0), sticky='ew')

image_frame = ttk.Frame(mainframe, width=400, height=350, relief="sunken")
image_frame.grid(row=0, column=1, sticky='nsew')
image_frame.grid_propagate(False)

image_label = ttk.Label(image_frame, text="Image goes here", font=("Helvetica", 16), anchor="center")
image_label.place(relx=0.5, rely=0.5, anchor="center")

mainframe.columnconfigure(0, weight=0)
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(0, weight=1)

cap = cv2.VideoCapture(0)  # 0 is the default camera

def update_camera_feed():
    ret, frame = cap.read()
    if ret:
        # Draw red dots for each center (if any)
        for center in centers:
            try:
                x, y = int(center[0]), int(center[1])
                # Draw a red dot: after cvtColor!
                cv2.circle(frame, (x, y), radius=1, color=(0, 0, 255), thickness=3)  # BGR for OpenCV
            except Exception as e:
                print("Error drawing center:", center, e)
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize to match GUI
       # frame = cv2.resize(frame, (400, 350))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        image_label.imgtk = imgtk  # Keep reference!
        image_label.config(image=imgtk)
    root.after(15, update_camera_feed)

update_camera_feed()

def on_closing():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
