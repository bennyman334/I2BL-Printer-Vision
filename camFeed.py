import cv2
import time
import os



def main():
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

        #cv2.imshow('Live Feed', frame)

        # Take screenshot after 3 seconds, rotate it, and save
        if not screenshot_taken and (time.time() - start_time) >= 3:
            #rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            filename = os.path.join(output_dir, "screenshot_3_seconds.png")
            cv2.imwrite(filename, frame)
            # filename_two= os.path.join(output_dir,"undistorted_screenshot.png")
            # frame_two=cv2.undistort(frame)
            # cv2.imwrite(filename_two,frame_two)
            print(f"Screenshot saved as {filename} (rotated 90 degrees right)")
            screenshot_taken = True
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
