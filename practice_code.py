import cv2
import numpy as np
import os
import sendPython 
from datetime import datetime 
#12
CAPTURE_DIR = "captures"
if not os.path.exists(CAPTURE_DIR):
    os.makedirs(CAPTURE_DIR)

captured_file_paths = []

# Define physical size of calibration square in mm
SQUARE_SIZE_MM = 70.03

# Define ideal square in mm (anchored at origin)
real_world_pts_mm = np.array([
    [0, 0],
    [SQUARE_SIZE_MM, 0],
    [SQUARE_SIZE_MM, SQUARE_SIZE_MM],
    [0, SQUARE_SIZE_MM]
], dtype=np.float32)

def show_side_by_side(windows, start_x=100, start_y=50, spacing=20, custom_positions={}):
    current_x = start_x
    for name, image in windows:
        if image is not None:
            cv2.imshow(name, image)
            if name in custom_positions:
                x, y = custom_positions[name]
                cv2.moveWindow(name, x, y)
            else:
                cv2.moveWindow(name, current_x, start_y)
                current_x += image.shape[1] + spacing

def generate_center_to_dot_overlay(frame: np.ndarray, dot: np.ndarray | None) -> np.ndarray:
    if frame is None or dot is None:
        return None

    zoom_scale = 1.5
    h, w = frame.shape[:2]

    # Resize (zoom slightly into frame while keeping full image)
    overlay = cv2.resize(frame, (0, 0), fx=zoom_scale, fy=zoom_scale, interpolation=cv2.INTER_LINEAR)
    
    # Center crop back to original size
    zh, zw = overlay.shape[:2]
    x_start = (zw - w) // 2
    y_start = (zh - h) // 2
    overlay = overlay[y_start:y_start + h, x_start:x_start + w]

    # Draw line from center to dot
    center = (w // 2, h // 2)
    target = tuple(np.round(dot).astype(int))
    cv2.circle(overlay, center, 5, (0, 0, 255), -1)
    cv2.circle(overlay, target, 5, (255, 0, 0), -1)
    cv2.line(overlay, center, target, (0, 255, 255), 2)

    # Show pixel distance
    distance = np.linalg.norm(np.array(center) - np.array(target))
    mid_point = ((center[0] + target[0]) // 2, (center[1] + target[1]) // 2)
    cv2.putText(overlay, f"{distance:.1f} px", mid_point, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    return overlay



def sort_clockwise(pts: np.ndarray) -> np.ndarray:
    center = np.mean(pts, axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    return pts[np.argsort(angles)]

def detect_dots(frame: np.ndarray, debug_draw: np.ndarray = None) -> np.ndarray | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    #Set up the detector with parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True 
    params.minArea = 100 
    params.maxArea = 200000 

    params.filterByCircularity = True 
    params.minCircularity = 0.6 

    params.filterByColor = False #Detect both dark and bright blobs 

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

    return sort_clockwise(centers)


def show_zoomed_dots_window(frame: np.ndarray, points: np.ndarray, inset_size=150, scale=4) -> np.ndarray | None:
    h, w = frame.shape[:2]
    zoomed_tiles = []

    for i, pt in enumerate(points):
        cx, cy = int(pt[0]), int(pt[1])
        x1 = max(cx - inset_size // 2, 0)
        y1 = max(cy - inset_size // 2, 0)
        x2 = min(cx + inset_size // 2, w)
        y2 = min(cy + inset_size // 2, h)

        cropped = frame[y1:y2, x1:x2]
        if cropped.size == 0:
            continue

        zoomed = cv2.resize(cropped, (inset_size * scale, inset_size * scale), interpolation=cv2.INTER_CUBIC)

        #Sharpen 
        blurred = cv2.GaussianBlur(zoomed, (7, 7), 1.5)
        zoomed = cv2.addWeighted(zoomed, 1.6, blurred, -0.6, 0)

        center_cross = (inset_size * scale) // 2
        cv2.rectangle(zoomed,
                      (center_cross - 2, center_cross - 2),
                      (center_cross + 2, center_cross + 2),
                      (0, 0, 255), 1)

        cv2.putText(zoomed, f"Dot {i+1}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        zoomed_tiles.append(zoomed)
    
    if zoomed_tiles:
        #Ensure we have 4 tiles for 2x2 layout 
        while len(zoomed_tiles) < 4:
            blank = np.zeros_like(zoomed_tiles[0])
            zoomed_tiles.append(blank)
        
        top_row = cv2.hconcat(zoomed_tiles[:2])
        bottom_row = cv2.hconcat(zoomed_tiles[2:])
        combined = cv2.vconcat([top_row, bottom_row])

        return ("Zoomed Dots", combined)  # return the image so it can be saved
    else:
        return None

def show_center_to_origin_distance_window(frame: np.ndarray, center_pt: np.ndarray, origin_pt: np.ndarray, inset_size=200, scale=4):
    h, w = frame.shape[:2]

    # Compute bounding box that includes both points
    min_x = int(min(center_pt[0], origin_pt[0]) - inset_size // 2)
    min_y = int(min(center_pt[1], origin_pt[1]) - inset_size // 2)
    max_x = int(max(center_pt[0], origin_pt[0]) + inset_size // 2)
    max_y = int(max(center_pt[1], origin_pt[1]) + inset_size // 2)

    # Clamp to image bounds
    x1 = max(min_x, 0)
    y1 = max(min_y, 0)
    x2 = min(max_x, w)
    y2 = min(max_y, h)

    cropped = frame[y1:y2, x1:x2]
    if cropped.size == 0:
        return None

    zoomed = cv2.resize(cropped, (cropped.shape[1]*scale, cropped.shape[0]*scale), interpolation=cv2.INTER_CUBIC)

    # Scale coordinates for drawing
    offset = np.array([x1, y1])
    center_scaled = ((center_pt - offset) * scale).astype(int)
    origin_scaled = ((origin_pt - offset) * scale).astype(int)

    # Draw center and origin dots
    cv2.circle(zoomed, tuple(center_scaled), 10, (0, 0, 255), -1)  # red center
    cv2.circle(zoomed, tuple(origin_scaled), 10, (255, 0, 0), -1)  # blue origin

    # Draw yellow line between them
    cv2.line(zoomed, tuple(center_scaled), tuple(origin_scaled), (0, 255, 255), 2)

    # Compute and display distance
    dist_px = np.linalg.norm(center_pt - origin_pt)
    label_pos = ((center_scaled + origin_scaled) // 2).astype(int)
    if CALIBRATED and PIXELS_PER_MM:
        dist_mm = dist_px / PIXELS_PER_MM
        label = f"{dist_mm:.2f} mm"
    else:
        label = f"{dist_px:.1f} px"

    cv2.putText(zoomed, label, tuple(label_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return zoomed



def warp_image(image: np.ndarray, rect: np.ndarray, pixels_per_mm: float) -> np.ndarray:
    width_px = int(SQUARE_SIZE_MM * pixels_per_mm)
    height_px = int(SQUARE_SIZE_MM * pixels_per_mm)
    dst = np.array([
        [0, 0],
        [width_px - 1, 0],
        [width_px - 1, height_px - 1],
        [0, height_px - 1]
    ], dtype=np.float32)
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (width_px, height_px))
    draw_mm_grid(warped, np.eye(3), max_x=SQUARE_SIZE_MM, max_y=SQUARE_SIZE_MM, step=10, pixels_per_mm=pixels_per_mm)
    cv2.polylines(warped, [np.array([[0,0],[width_px-1,0],[width_px-1,height_px-1],[0,height_px-1]], np.int32)], isClosed=True, color=(255,0,255), thickness=3)
    return warped

def draw_overlay_with_mm_labels(frame: np.ndarray, pts: np.ndarray, pixels_per_mm: float, color: tuple, label: str) -> None:
    for i in range(4):
        pt1 = np.array(pts[i % 4])
        pt2 = np.array(pts[(i + 1) % 4])
        dist_px = np.linalg.norm(pt1 - pt2)
        dist_mm = dist_px / pixels_per_mm if pixels_per_mm else 1.0
        p1 = tuple(pt1.astype(int))
        p2 = tuple(pt2.astype(int))
        mid = tuple(((pt1 + pt2) / 2).astype(int))
        cv2.line(frame, p1, p2, color, 2)
        cv2.putText(frame, f"{dist_mm:.1f}mm", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    y_offset = 20 if color == (0, 255, 0) else 40
    cv2.putText(frame, label, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_mm_grid(image: np.ndarray, H_real2img: np.ndarray, max_x=140, max_y=140, step=10, pixels_per_mm=None):
    for x in range(0, int(max_x)+1, step):
        pt1 = (int(x * pixels_per_mm), 0)
        pt2 = (int(x * pixels_per_mm), int(max_y * pixels_per_mm))
        cv2.line(image, pt1, pt2, (100, 100, 100), 1)
    for y in range(0, int(max_y)+1, step):
        pt1 = (0, int(y * pixels_per_mm))
        pt2 = (int(max_x * pixels_per_mm), int(y * pixels_per_mm))
        cv2.line(image, pt1, pt2, (100, 100, 100), 1)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 150) # Optional brightness boost
cap.set(cv2.CAP_PROP_CONTRAST, 50)    # Optional contrast boost
cap.set(cv2.CAP_PROP_SHARPNESS, 3)    # Some cameras support this
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cv2.namedWindow("Alignment", cv2.WINDOW_NORMAL)

PIXELS_PER_MM = None
CALIBRATED = False
PENDING_CALIBRATION = None
stable_detections = []
STABLE_FRAMES = 5
last_calibration_points = None
last_frame_for_capture = None
show_capture = False
captured_image = None
last_detected_points = None

zoom_image = None 
showing_zoom_viewer = False 

zoom_captures = []
ZOOM_CAPTURE_DIR = "zoom_captures"
if not os.path.exists(ZOOM_CAPTURE_DIR):
    os.makedirs(ZOOM_CAPTURE_DIR)
else:
    # Load previously saved zoom captures
    for f in sorted(os.listdir(ZOOM_CAPTURE_DIR)):
        if f.endswith(".png"):
            zoom_captures.append(os.path.join(ZOOM_CAPTURE_DIR, f))

zoom_factor = 1.0
ZOOM_STEP = 0.1
MIN_ZOOM = 0.1
MAX_ZOOM = 6.0


def on_mouse(event, x, y, flags, param):
    pass

cv2.setMouseCallback("Alignment", on_mouse)

h = 1920
w = 1080
while True:

    #print("HELLO FUCK U DUMBFUCK!")
    if not show_capture:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        #frame = frame[0:1920, 0:700]
        #h, w = frame.shape[:2]

        #print("Height:", h, "Width:", w)

        # --- ZOOM CROP ---
        crop_w = int(w / zoom_factor)
        crop_h = int(h / zoom_factor)
        x1 = max((w - crop_w) // 2, 0)
        y1 = max((h - crop_h) // 2, 0)
        x2 = min(x1 + crop_w, w)
        y2 = min(y1 + crop_h, h)
        cropped = frame[y1:y2, x1:x2]
        frame_zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)
        raw_clean_frame = frame_zoomed.copy() #store clean copy before any edits

        # --- CONTRAST / BRIGHTNESS ADJUSTMENT ---
        alpha = 1.3 #Contrast (1.0 = no change)
        beta = 10 #Brightness (0 = no change)
        frame_zoomed = cv2.convertScaleAbs(frame_zoomed, alpha=alpha, beta=beta)

        lab = cv2.cvtColor(frame_zoomed, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        merged = cv2.merge((cl, a, b))
        frame_zoomed = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


        # --- SHARPENING ---
        # First pass
        blurred1 = cv2.GaussianBlur(frame_zoomed, (5, 5), 1.2)
        sharpened1 = cv2.addWeighted(frame_zoomed, 1.7, blurred1, -0.7, 0)
        
        # Second pass
        blurred2 = cv2.GaussianBlur(sharpened1, (3, 3), 0.8)
        display_frame = cv2.addWeighted(sharpened1, 1.5, blurred2, -0.5, 0)


        last_frame_for_capture = display_frame.copy()

        # --- DOT DETECTION ---
        detected = detect_dots(display_frame, display_frame)
        zoom_result = show_zoomed_dots_window(raw_clean_frame, detected) if detected is not None else None
        if zoom_result:
            zoom_window_name, zoom_image = zoom_result 
        else:
            zoom_window_name, zoom_image = None, None 
        
        #Center-to-dot overlay zoom 
        zoom_overlay_image = None 
        if detected is not None and len(detected) > 0:
            zoom_overlay_image = generate_center_to_dot_overlay(raw_clean_frame, detected[0]) #pick first dot 
        last_detected_points = detected if detected is not None else last_detected_points

        # -- Stability Tracking for Calibration ---
        if detected is not None:
            if stable_detections and stable_detections[-1].shape != detected.shape:
                stable_detections.clear()
                PENDING_CALIBRATION = None

            stable_detections.append(detected)
            if len(stable_detections) > STABLE_FRAMES:
                stable_detections.pop(0)

            if len(stable_detections) == STABLE_FRAMES and all(
                det.shape == stable_detections[0].shape for det in stable_detections
            ):
                if all(np.allclose(stable_detections[0], det, atol=2.5) for det in stable_detections):
                    PENDING_CALIBRATION = stable_detections[0]
                else:
                    PENDING_CALIBRATION = None
            else:
                PENDING_CALIBRATION = None
        else:
            stable_detections.clear()
            PENDING_CALIBRATION = None
        
        # --- Draw Points + Grid ---
        if detected is not None:
            for pt in detected:
                center = tuple(np.round(pt).astype(int))
                cv2.circle(display_frame, center, 8, (0, 0, 255), -1)
                cv2.circle(display_frame, center, 5, (0, 255, 0), -1)
            draw_overlay_with_mm_labels(display_frame, detected, PIXELS_PER_MM if PIXELS_PER_MM else 1.0, (0, 255, 0), "Detected Points (Green)")
            #Draw center of detected square 
            # center_point = np.mean(detected, axis=0).astype(int)
            center_point = np.array([w / 2, h / 2]).astype(int)
            cv2.circle(display_frame, center_point, 10, (0, 0, 255), -1)  # big red center dot
            
            
            #Find and mark the origin (top-right dot)
            scores = detected[:, 0] - detected[:, 1]     # x - y for Top-Right
            origin_index = np.argmax(scores)
            origin_point = detected[origin_index].astype(int)

            br_index = np.argmax(detected[:, 0] + detected[:, 1])  # Bottom-Right
            bottom_right = detected[br_index].astype(int)

            tl_index = np.argmin(detected[:, 0] + detected[:, 1])  # Top-Left
            top_left = detected[tl_index].astype(int)

            bl_index = np.argmin(detected[:, 0] - detected[:, 1])  # Bottom-Left
            bottom_left = detected[bl_index].astype(int)


            # scores = detected[:, 0] - detected[:, 1] #x - y score 
            # origin_index = np.argmax(scores)
            # origin_point = detected[origin_index].astype(int)

            # #Find and mark the bottom right dot
            # scores = detected[:, 0] + detected[:, 1]  # x + y score
            # bottom_right_index = np.argmax(scores)
            # bottom_right_point = detected[bottom_right_index].astype(int)
            cv2.circle(display_frame, tuple(origin_point), 12, (255, 0, 0), 3) #big blue circle

            vec1 = np.array([-(origin_point[0] - center_point[0]), origin_point[1] - center_point[1]])
            vec2 = -(bottom_right - center_point)

            dist_top_bottom = np.linalg.norm(bottom_right - origin_point)
            dist_left_right = np.linalg.norm(top_left - origin_point)

            measured_top_bottom = 23.5 #in millimeters (Measured manually)
            measured_left_right = 21.1 #in millimeters (Measured manually)

            calibration_y = measured_top_bottom/dist_top_bottom # Measured in MM/Pixel
            calibration_x = measured_left_right/dist_left_right # Measured in MM/Pixel

            calibration = (calibration_x + calibration_y)/2

            real_vec = calibration*vec1

            print("Origin:", origin_point)
            print("Center: ", center_point)
            print("Top Left:", top_left)
            print("Bottom Right:", bottom_right)
            print("Calibration Conversion:", calibration)


            print("Vector to origin:", vec1)
            print("Real Vector:", real_vec)

            dist_px = np.linalg.norm(center_point - origin_point)


            #Line from center to origin
            cv2.line(display_frame, tuple(center_point), tuple(origin_point), (0, 255, 255), 2)

            zoom_center_origin_image = show_center_to_origin_distance_window(raw_clean_frame, center_point, origin_point)
            if CALIBRATED and PIXELS_PER_MM:
                dist_mm = dist_px / PIXELS_PER_MM
                label = f'{dist_mm:.2f} mm'
            else:
                label = f'{dist_px:.1f} px'
            
            midpoint = ((center_point + origin_point // 2).astype(int))


        if CALIBRATED and last_calibration_points is not None and PIXELS_PER_MM is not None:
            width_px = int(SQUARE_SIZE_MM * PIXELS_PER_MM)
            height_px = int(SQUARE_SIZE_MM * PIXELS_PER_MM)
            center_detected = np.mean(last_calibration_points, axis=0)
            center_ideal_px = np.array([width_px/2, height_px/2])
            offset = center_detected - center_ideal_px
            ideal_pts_px = real_world_pts_mm * PIXELS_PER_MM + offset
            draw_overlay_with_mm_labels(display_frame, ideal_pts_px, PIXELS_PER_MM, (255, 0, 255), "Ideal Shape (Magenta)")
            for pt in ideal_pts_px:
                cv2.circle(display_frame, tuple(pt.astype(int)), 6, (255, 0, 255), -1)
            draw_mm_grid(display_frame, np.eye(3), max_x=SQUARE_SIZE_MM, max_y=SQUARE_SIZE_MM, step=10, pixels_per_mm=PIXELS_PER_MM)
        
        # --- UI Text ---
        msg = "Calibrated ✅ (press 'r' to reset)" if CALIBRATED else "Waiting for Calibration... Press 'c' to confirm"
        cv2.putText(display_frame, msg, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0) if CALIBRATED else (0, 0, 255), 1)
        cv2.putText(display_frame, "Press 'q' to quit | 'c' to calibrate | 'r' to reset | 's' to capture | 'b' to back", (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Zoom: {zoom_factor:.1f}x", (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        #Show side-by-side zoom windows
        zoom_windows = []
        if zoom_image is not None:
            zoom_windows.append(("Zoomed Dots", zoom_image))
        if zoom_overlay_image is not None:
            zoom_windows.append(("Center --> Origin", zoom_overlay_image))
        
        custom_positions = {
            "Center --> Origin": (1100, 50) #Move it anywhere you want
        }
        show_side_by_side(
            zoom_windows, 
            start_x=500, 
            start_y=50, 
            spacing=30,
            custom_positions=custom_positions
        )
        #cv2.resizeWindow("Cropped Frame", 1920, 700)
        cv2.imshow("Alignment", display_frame)

    else:
        cv2.putText(captured_image, "Captured Calibration Image (press 'b' to go back)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Captured", captured_image)


    key = cv2.waitKey(1) & 0xFF

    if key == ord('c') and PENDING_CALIBRATION is not None:
        print("[INFO] Calibrating using 4 points")
        last_calibration_points = PENDING_CALIBRATION.copy()
        side_lengths = [
            np.linalg.norm(last_calibration_points[i] - last_calibration_points[(i + 1) % 4])
            for i in range(4)
        ]
        avg_side_px = np.mean(side_lengths)
        PIXELS_PER_MM = avg_side_px / SQUARE_SIZE_MM
        CALIBRATED = True
        print("[INFO] Calibration completed.")

    elif key == ord('s'):
        if last_frame_for_capture is not None:
            os.makedirs("captures", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if CALIBRATED and last_calibration_points is not None:
            captured_image = warp_image(last_frame_for_capture, last_calibration_points, PIXELS_PER_MM)
            filename = f"captures/capture_calibrated_{timestamp}.png"
            cv2.imwrite(filename, captured_image)
            print(f"[INFO] Saved calibrated capture as {filename}")
        
        else:
            captured_image = last_frame_for_capture.copy()
            if last_detected_points is not None and len(last_detected_points) == 4:
                pts = np.array(last_detected_points, dtype=np.int32)
                cv2.polylines(captured_image, [pts], isClosed=True, color=(0, 255, 0), thickness=3)
                draw_overlay_with_mm_labels(captured_image, last_detected_points, 1.0, (0, 255, 0), "Detected Outline (Green)")
                print("[INFO] Captured raw image with green detection overlay.")
            else:
                print("[INFO] Captured raw image (no detection overlay).")
            
            filename = f"captures/capture_raw_{timestamp}.png"
            cv2.imwrite(filename, captured_image)
            print(f"[INFO] Saved raw capture as {filename}")


    elif key == ord('b'):
        if show_capture:
            show_capture = False
            captured_image = None
            cv2.destroyWindow("Captured")
            PIXELS_PER_MM = None
            CALIBRATED = False
            PENDING_CALIBRATION = None
            stable_detections.clear()
            last_calibration_points = None
            last_frame_for_capture = None
            print("[INFO] Returned to live feed and reset calibration.")
        
        if showing_zoom_viewer:
            cv2.destroyWindow("Zoom Viewer")
            showing_zoom_viewer = False
            print("[INFO] Closed Zoom Viewer")
        
        if 'showing_raw_viewer' in locals() and showing_raw_viewer:
            cv2.destroyWindow("Raw Viewer")
            showing_raw_viewer = False
            print("[INFO] Closed Raw Viewer")

    elif key == ord('r'):
        PIXELS_PER_MM = None
        CALIBRATED = False
        PENDING_CALIBRATION = None
        stable_detections.clear()
        last_calibration_points = None
        last_frame_for_capture = None
        show_capture = False
        print("[INFO] Calibration reset.")
    
    elif key == ord('v'):
        print("[INFO] Displaying all saved captures...")
        images = [f for f in os.listdir(CAPTURE_DIR) if f.endswith(".png")]
        if not images:
            print("[WARN] No images to display.")
        else:
            for img_name in sorted(images):
                img_path = os.path.join(CAPTURE_DIR, img_name)
                img = cv2.imread(img_path)
                if img is not None:
                    window_name = f"Capture - {img_name}"
                    cv2.imshow(window_name, img)
                    cv2.moveWindow(window_name, 500, 20)  # Offset each window vertically
                    cv2.waitKey(500)  # wait 500ms before showing next, or press any key
            print("[INFO] All captures displayed. Press any key to continue.")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    elif key == ord('z'):
        if zoom_image is not None:
            os.makedirs("zoom_captures", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zoom_captures/zoom_capture_{timestamp}.png"
            cv2.imwrite(filename, zoom_image)
            zoom_captures.append(filename)
            print(f"[INFO] Zoom window saved as {filename}")
        else:
            print("[WARN] No zoomed image to save.")
    
    elif key == ord('x'):
        if zoom_captures:
            zoom_images = [cv2.imread(path) for path in zoom_captures if cv2.imread(path) is not None]
            if zoom_images:
                max_height = max(img.shape[0] for img in zoom_images)
                zoom_images_resized = [cv2.resize(img, (int(img.shape[1] * max_height / img.shape[0]), max_height)) for img in zoom_images]
                combined_zoom_view = cv2.hconcat(zoom_images_resized)
                showing_zoom_viewer = True
                cv2.imshow("Zoom Viewer", combined_zoom_view)
                print(f"[INFO] Displaying {len(zoom_images)} zoom captures.")
            else:
                print("[WARN] Could not load zoom images.")
        else:
            print("[WARN] No zoom captures to display.")


    
    elif key == ord('+') or key == ord('='):  # '+' to zoom in
        zoom_factor = min(zoom_factor + ZOOM_STEP, MAX_ZOOM)
        print(f"[INFO] Zoom factor increased to {zoom_factor:.1f}x")
    
    elif key == ord('-') or key == ord('_'):  # '-' to zoom out
        zoom_factor = max(zoom_factor - ZOOM_STEP, MIN_ZOOM)
        print(f"[INFO] Zoom factor decreased to {zoom_factor:.1f}x")


    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()