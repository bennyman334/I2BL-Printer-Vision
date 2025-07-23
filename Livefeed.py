import cv2
import numpy as np
import os
from datetime import datetime 

CAPTURE_DIR = "captures"
if not os.path.exists(CAPTURE_DIR):
    os.makedirs(CAPTURE_DIR)

captured_file_paths = []

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
cap.set(cv2.CAP_PROP_CONTRAST, 50)
cap.set(cv2.CAP_PROP_SHARPNESS, 3)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cv2.namedWindow("Alignment", cv2.WINDOW_NORMAL)

zoom_factor = 1.0
ZOOM_STEP = 0.1
MIN_ZOOM = 0.1
MAX_ZOOM = 6.0

steady_detection_count = 0 #How many frames dots were detected in a row 
STEADY_THRESHOLD = 5 #Number of consecutive detetctions before capturing
auto_capture_done = False #Avoid repeated captures

last_frame_for_capture = None
show_capture = False
captured_image = None
last_detected_points = None

def calibration(box: np.ndarray, known_mm: float) -> float:
    # Ensure box is sorted (not strictly necessary for this)
    if box.shape != (4, 2):
        raise ValueError("Expected a 4-point box array of shape (4, 2)")

    # Compute side lengths
    def euclidean(pt1, pt2):
        return np.linalg.norm(pt1 - pt2)

    side_lengths = [
        euclidean(box[0], box[1]),
        euclidean(box[1], box[2]),
        euclidean(box[2], box[3]),
        euclidean(box[3], box[0]),
    ]

    # Average the two opposite sides (choose short side)
    short_sides = sorted(side_lengths)[:2]
    avg_pixel_length = np.mean(short_sides)

    # Calculate pixels per mm
    pixels_per_mm = avg_pixel_length / known_mm

    print(f"[CALIBRATION] Measurement in mm: {pixels_per_mm:.2f}")
    
    return pixels_per_mm

def detect_dots(frame: np.ndarray, debug_draw: np.ndarray = None) -> np.ndarray | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True 
    params.minArea = 100 
    params.maxArea = 200000 
    params.filterByCircularity = True 
    params.minCircularity = 0.6 
    params.filterByColor = False 
    params.filterByInertia = False 
    params.filterByConvexity = False 

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)

    if len(keypoints) != 4:
        return None 
    
    centers = np.array([kp.pt for kp in keypoints], dtype=np.float32)

    if debug_draw is not None:
        for i, kp in enumerate(keypoints):
            x, y = int(kp.pt[0]), int(kp.pt[1])
            cv2.circle(debug_draw, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(debug_draw, f'{x}, {y}', (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return centers

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # Top-left has smallest sum
    rect[2] = pts[np.argmax(s)]  # Bottom-right has largest sum

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right has smallest difference
    rect[3] = pts[np.argmax(diff)]  # Bottom-left has largest difference

    return rect

def detect_green_region(frame: np.ndarray, debug_draw: np.ndarray = None) -> tuple[int, int, int, int] | None:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define green color range (tweak as needed for lighting conditions)
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([90, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Morphology to clean up
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest) #(center(x, y), (width, height), angle)
        box = cv2.boxPoints(rect)
        box = np.round(cv2.boxPoints(rect)).astype(int) #Convert to integer coordinates

        if debug_draw is not None:
            cv2.drawContours(debug_draw, [box], 0, (0, 0, 255), 2)

        return box 
    return None

cv2.setMouseCallback("Alignment", lambda *args : None)

h = 1920
w = 1080

while True:
    if not show_capture:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        crop_w = int(w / zoom_factor)
        crop_h = int(h / zoom_factor)
        x1 = max((w - crop_w) // 2, 0)
        y1 = max((h - crop_h) // 2, 0)
        x2 = min(x1 + crop_w, w)
        y2 = min(y1 + crop_h, h)
        cropped = frame[y1:y2, x1:x2]
        frame_zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        raw_clean_frame = frame_zoomed.copy()

        alpha = 1.3
        beta = 10
        frame_zoomed = cv2.convertScaleAbs(frame_zoomed, alpha=alpha, beta=beta)

        lab = cv2.cvtColor(frame_zoomed, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        frame_zoomed = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        blurred1 = cv2.GaussianBlur(frame_zoomed, (5, 5), 1.2)
        sharpened1 = cv2.addWeighted(frame_zoomed, 1.7, blurred1, -0.7, 0)
        blurred2 = cv2.GaussianBlur(sharpened1, (3, 3), 0.8)
        display_frame = cv2.addWeighted(sharpened1, 1.5, blurred2, -0.5, 0)

        last_frame_for_capture = None
        detected = detect_dots(display_frame, display_frame)

        if detected is not None:
            ordered = order_points(detected)

            for pt in ordered:
                center = tuple(np.round(pt).astype(int))
                cv2.circle(display_frame, center, 8, (0, 0, 255), -1)
                cv2.circle(display_frame, center, 5, (0, 255, 0), -1)
            
            pts = ordered.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            
            #Draw pixel distance between each pair of points
            for i in range(4):
                pt1 = ordered[i]
                pt2 = ordered[(i + 1) % 4]
                mid = ((pt1 + pt2) / 2).astype(int)
                dist_px = np.linalg.norm(pt1 - pt2)
                cv2.putText(display_frame, f'{dist_px:.1f} px', tuple(mid), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            #Steady detection logic 
            steady_detection_count += 1 
            if steady_detection_count >= STEADY_THRESHOLD and not auto_capture_done:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                captured_image = display_frame.copy()
                green_box = detect_green_region(captured_image, captured_image)
                filename = f"{CAPTURE_DIR}/auto_capture_{timestamp}.png"
                cv2.imwrite(filename, captured_image)
                print(f"[AUTO] Saved auto-capture as {filename}")

                #Detect and draw green tape box 
                green_box = detect_green_region(display_frame, display_frame)
                if green_box is not None:
                    PIXELS_PER_MM = calibration(green_box, 23.5)
                
                auto_capture_done = True 
        else:
            steady_detection_count = 0
            auto_capture_done = False 

        cv2.putText(display_frame, "Press 'q' to quit | 's' to capture | '+'/'-' to zoom", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Zoom: {zoom_factor:.1f}x", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        last_frame_for_capture = display_frame.copy()
        cv2.imshow("Alignment", display_frame)

    else:
        cv2.putText(captured_image, "Captured Image (press 'b' to go back)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        if last_frame_for_capture is not None:
            os.makedirs("captures", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            captured_image = last_frame_for_capture.copy()
            filename = f"captures/capture_raw_{timestamp}.png"
            cv2.imwrite(filename, captured_image)
            print(f"[INFO] Saved raw capture as {filename}")
            show_capture = True

    elif key == ord('b'):
        if show_capture:
            show_capture = False
            captured_image = None
            cv2.destroyWindow("Captured")
            print("[INFO] Returned to live feed.")

    elif key == ord('+') or key == ord('='):
        zoom_factor = min(zoom_factor + ZOOM_STEP, MAX_ZOOM)
        print(f"[INFO] Zoom factor increased to {zoom_factor:.1f}x")

    elif key == ord('-') or key == ord('_'):
        zoom_factor = max(zoom_factor - ZOOM_STEP, MIN_ZOOM)
        print(f"[INFO] Zoom factor decreased to {zoom_factor:.1f}x")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
