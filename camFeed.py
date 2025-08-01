import cv2
import time
import os
import numpy as np

def main():
    # Load calibration data
    calib_file = "calibration_data.npz"
    if not os.path.exists(calib_file):
        print("Error: Calibration file not found!")
        return

    with np.load(calib_file) as X:
        cameraMatrix, distCoeffs = [X[i] for i in ('cameraMatrix','distCoeffs')]

    # Create an output directory to save the screenshot
    output_dir = "frames"
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    start_time = time.time()
    screenshot_taken = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Take screenshot after 3 seconds and save
        if not screenshot_taken and (time.time() - start_time) >= 3:
            filename = os.path.join(output_dir, "screenshot_3_seconds.png")
            cv2.imwrite(filename, frame)

            # Undistort and save
            frame_undist = cv2.undistort(frame, cameraMatrix, distCoeffs)
            filename_undist = os.path.join(output_dir, "screenshot_33_seconds.png")
            cv2.imwrite(filename_undist, frame_undist)

            print(f"Screenshot saved as {filename}")
            print(f"Undistorted screenshot saved as {filename_undist}")

            screenshot_taken = True
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
