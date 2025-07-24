import numpy as np
import cv2

def detect_green_region(frame: np.ndarray, real_length: float, real_width: float, debug_draw: np.ndarray = None) -> float | None:
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

        edge1 = np.linalg.norm(box[0] - box[1])
        edge2 = np.linalg.norm(box[1] - box[2])

        width = min(edge1, edge2)
        length = max(edge1, edge2)

        w_cal = real_width/width
        l_cal = real_length/length
        
        print("Two calibrations:", w_cal, l_cal)

        cal_avg = (w_cal + l_cal)/2

        if debug_draw is not None:
            cv2.drawContours(debug_draw, [box], 0, (0, 0, 255), 2)
        return cal_avg
    return None


r_length = 25.6
r_width = 6.96
image = cv2.imread("calibrationBox.jpg")
debug_draw = image.copy()

cal_value = detect_green_region(image, r_length, r_width, debug_draw=debug_draw)

print(cal_value, "mm/pixel")
cv2.imshow("Debug Draw", debug_draw)
cv2.waitKey(0)
cv2.destroyAllWindows()
