import cv2

# List to store clicked points
points = []
center_point = None  # store center separately

# Mouse callback function
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point added: ({x}, {y})")

# Open webcam
cap = cv2.VideoCapture(0)

# Grab one frame to get size
ret, frame = cap.read()
if not ret:
    print("Failed to read from camera.")
    cap.release()
    exit()

# Add center point
h, w = frame.shape[:2]
center_point = (w // 2, h // 2)
print(f"Center point added: {center_point}")

# Create window & set mouse callback
cv2.namedWindow("Live Feed")
cv2.setMouseCallback("Live Feed", click_event)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw center point in blue
    cv2.circle(frame, center_point, 5, (0, 255, 0), -1)  # green filled circle

    # Draw user-clicked points in red
    for (px, py) in points:
        cv2.circle(frame, (px, py), 5, (0, 0, 255), -1)  # red filled circle

    cv2.imshow("Live Feed", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
