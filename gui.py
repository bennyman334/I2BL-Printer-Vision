import tkinter as tk
from tkinter import ttk
import subprocess
import camFeed
import cv2
from PIL import Image, ImageTk


venv_python = "/Users/abdulsalamraja/extrusionTargetI2BL/rfenv/bin/python"
target_script = "/Users/abdulsalamraja/extrusionTargetI2BL/target.py"

def run_target():
    subprocess.Popen([venv_python, target_script])

def run_screenshot(): 
    camFeed.main()


root = tk.Tk()
root.title("Microneedle Assembly")
root.geometry("900x450")  # Set a much larger window size

# Main frame
mainframe = ttk.Frame(root, padding=30)
mainframe.pack(fill='both', expand=True)

# Create left frame for buttons
button_frame = ttk.Frame(mainframe)
button_frame.grid(row=0, column=0, sticky='n', padx=(0, 50))  # Padding right

# Button specs
button_style = ttk.Style()
button_style.configure("Big.TButton", font=("Helvetica", 18), padding=20)

snapshot_btn = ttk.Button(button_frame, text="Take Snapshot", style="Big.TButton", command=run_screenshot)
calibrate_btn = ttk.Button(button_frame, text="Calibrate", style="Big.TButton", command=run_target)
approve_btn = ttk.Button(button_frame, text="Approve", style="Big.TButton")
print_btn = ttk.Button(button_frame, text="Print", style="Big.TButton")

snapshot_btn.grid(row=0, column=0, pady=(0, 30), sticky='ew')
calibrate_btn.grid(row=1, column=0, pady=(0, 30), sticky='ew')
approve_btn.grid(row=2, column=0, pady=(0, 30), sticky='ew')
print_btn.grid(row=3, column=0, pady=(0, 0), sticky='ew')

# Image placeholder frame (right side)
image_frame = ttk.Frame(mainframe, width=400, height=350, relief="sunken")
image_frame.grid(row=0, column=1, sticky='nsew')
image_frame.grid_propagate(False)  # Prevent shrinking

# Label in image box as a placeholder
image_label = ttk.Label(image_frame, text="Image goes here", font=("Helvetica", 16), anchor="center")
image_label.place(relx=0.5, rely=0.5, anchor="center")

# Configure grid weights for expansion
mainframe.columnconfigure(0, weight=0)
mainframe.columnconfigure(1, weight=1)
mainframe.rowconfigure(0, weight=1)

cap = cv2.VideoCapture(0)  # 0 is the default camera

def update_camera_feed():
    ret, frame = cap.read()
    if ret:
        # Convert color (BGR to RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize if needed (optional)
        frame = cv2.resize(frame, (400, 350))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        image_label.imgtk = imgtk  # Keep reference!
        image_label.config(image=imgtk)
    # Call again after 15ms
    root.after(15, update_camera_feed)

# Start the camera feed loop
update_camera_feed()

def on_closing():
    cap.release()
    root.destroy()

root.mainloop()
