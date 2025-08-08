import numpy as np
import cv2

def detect_green_region(frame: np.ndarray, real_length: float, real_width: float, debug_draw: np.ndarray = None) -> float | None:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define green color range (tweak as needed for lighting conditions)
    lower_green = np.array([40, 80, 40])
    upper_green = np.array([70, 255, 255])

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
        box = np.round(cv2.boxPoints(rect)).astype(int) #Convert to integer coordinates

        edge1 = np.linalg.norm(box[0] - box[1])
        edge2 = np.linalg.norm(box[1] - box[2])

        width = min(edge1, edge2)
        length = max(edge1, edge2)

        w_cal = real_width / width
        l_cal = real_length / length
        
        print("Two calibrations:", w_cal, l_cal)

        cal_avg = (w_cal + l_cal) / 2

        if debug_draw is not None:
            cv2.drawContours(debug_draw, [box], 0, (0, 0, 255), 2)
        print("Calibration average:", cal_avg)
        return cal_avg
    return None

def detect_green_circles(frame: np.ndarray, w_real: float, l_real: float, debug_draw: np.ndarray = None) -> list[tuple[int, int]]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # HSV range for green
    lower_green = np.array([40, 70, 75])
    upper_green = np.array([70, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Morphological cleanup
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Blob detector parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 255

    params.filterByArea = True
    params.minArea = 20
    params.maxArea = 5000

    params.filterByCircularity = True
    params.minCircularity = 0.5

    params.filterByInertia = False
    params.filterByConvexity = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(mask)

    centers = [(int(k.pt[0]), int(k.pt[1])) for k in keypoints]

    if debug_draw is not None:
        cv2.drawKeypoints(debug_draw, keypoints, debug_draw, (0, 255, 0),
                          flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        cv2.imshow("Detected Circles", debug_draw)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
    
    if(len(centers) == 4):
        pts = np.array(centers, dtype=np.float32)
        # Sort by y (ascending)
        sorted_by_y = pts[np.argsort(pts[:, 1])]
        # Top two points (smallest y)
        top_two = sorted_by_y[:2]
        # Bottom two points (largest y)
        bottom_two = sorted_by_y[2:]

        # Now sort each pair by x (ascending)
        tl, tr = top_two[np.argsort(top_two[:, 0])]
        bl, br = bottom_two[np.argsort(bottom_two[:, 0])]

        width_top = np.linalg.norm(tl - tr)
        width_bottom = np.linalg.norm(bl - br)
        height_left = np.linalg.norm(tl - bl)
        height_right = np.linalg.norm(tr - br)

        width = (width_top + width_bottom) / 2
        height = (height_left + height_right) / 2

        print("Avg Width:", width)
        print("Avg height:", height)

        cal_width = w_real/width
        cal_height = l_real/height

        print("Calibration Width:", cal_width)
        print("Calibration Length:", cal_height)

        avg = float(cal_width + cal_height) / 2
        return avg
    else:
        print("Four Points Not detected")
    return 0.06


def main():
    r_length = 10
    r_width = 5
    image_path = "frames/screenshot_33_seconds.png"
    image = cv2.imread(image_path)
    show_image = image.copy()

    result = detect_green_circles(image, w_real = 23, l_real = 20, debug_draw=show_image)
    print(result, "mm/pixel")

    return result

    # if image is None:
    #     print(f"Error: Could not load image from {image_path}")
    #     return None

    # cal_value = detect_green_region(image, r_length, r_width)

    # if cal_value is not None:
    #     print(f"Calibration value: {cal_value:.4f} mm/pixel")
    # else:
    #     print("No green region detected for calibration.")

   #return cal_value
   #return 0

if __name__ == "__main__":
    main()
