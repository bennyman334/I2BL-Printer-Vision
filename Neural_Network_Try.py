import cv2
import os

# Create an output directory to save frames
output_dir = "frames"
os.makedirs(output_dir, exist_ok=True)

# Open the default camera (usually webcam at index 0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

frame_count = 0

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to grab frame")
        break

    # Save frame as PNG
    if(frame_count == 20):
        filename = os.path.join(output_dir, f"frame1_{frame_count:05d}.png")
        cv2.imwrite(filename, frame)

    frame_count += 1
    # Display the frame
    cv2.imshow('Live Feed', frame)

    # Press 'q' to break the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close all windows
cap.release()
cv2.destroyAllWindows()
