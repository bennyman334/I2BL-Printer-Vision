import cv2
import numpy as np
import time

def detect_green_tape_centers(image, debug=True):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([40, 100, 100])
    upper = np.array([80, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    if debug:
        cv2.imshow("Green Mask", mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    centers = []
    debug_frame = image.copy()

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50:  # Filter out small specks
            continue
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            centers.append((cx, cy))
            if debug:
                cv2.drawContours(debug_frame, [cnt], -1, (0, 255, 0), 1)
                cv2.circle(debug_frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(debug_frame, f"{len(centers)}", (cx+5, cy-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    if debug:
        cv2.imshow("Detected Contours", debug_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if len(centers) != 4:
        raise ValueError(f"Expected 4 markers, found {len(centers)}. Try adjusting lighting or HSV range.")

    # Sort: top-left, top-right, bottom-right, bottom-left
    centers = sorted(centers, key=lambda c: (c[1], c[0]))  # sort by y then x
    top = sorted(centers[:2], key=lambda c: c[0])
    bottom = sorted(centers[2:], key=lambda c: c[0])
    return [top[0], top[1], bottom[1], bottom[0]]

def compute_homography(pixels, real_world_mm):
    pixels = np.array(pixels, dtype=np.float32)
    real_world_mm = np.array(real_world_mm, dtype=np.float32)
    H, _ = cv2.findHomography(pixels, real_world_mm)
    return H

def main():
    print("Running debug green detection test...")
    cap = cv2.VideoCapture(0)
    time.sleep(2)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Failed to capture frame.")
        return

    try:
        centers = detect_green_tape_centers(frame, debug=True)

        # Define real-world mm positions (make sure this matches your physical setup)
        real_mm = [
            (0.0, 47.5),    # top-left
            (50.0, 47.5),   # top-right
            (50.0, 0.0),    # bottom-right
            (0.0, 0.0)      # bottom-left
        ]

        H = compute_homography(centers, real_mm)
        print("Homography matrix:\n", H)

        np.save("homography.npy", H)
        print("Saved to homography.npy")

    except Exception as e:
        print("Error:", e)





if __name__ == "__main__":
    main()
