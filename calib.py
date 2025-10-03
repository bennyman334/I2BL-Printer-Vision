import cv2
import numpy as np
import glob

# -----------------------------
# Charuco/AprilTag board setup
# -----------------------------
# Define the Charuco board (adjust these if you used a different size)
squares_x = 6  # number of squares along X
squares_y = 5  # number of squares along Y
square_length = 0.008  # meters
marker_length = 0.006  # meters

# Use 4x4_50 AprilTag dictionary (adjust based on your pattern)
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
board = cv2.aruco.CharucoBoard_create(
    squares_x, squares_y, square_length, marker_length, aruco_dict
)

# -----------------------------
# Read calibration images
# -----------------------------
image_dir = "calibpics/*.jpg"  # Update to your folder path
images = glob.glob(image_dir)

all_corners = []
all_ids = []
img_size = None

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_size = gray.shape[::-1]

    corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict)

    if ids is not None and len(ids) > 4:
        _, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            corners, ids, gray, board
        )
        if charuco_corners is not None and len(charuco_corners) > 4:
            all_corners.append(charuco_corners)
            all_ids.append(charuco_ids)

# -----------------------------
# Calibrate camera
# -----------------------------
if len(all_corners) > 0:
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
        charucoCorners=all_corners,
        charucoIds=all_ids,
        board=board,
        imageSize=img_size,
        cameraMatrix=None,
        distCoeffs=None
    )

    print("Camera matrix:\n", camera_matrix)
    print(f"\nOptical center (cx, cy): ({camera_matrix[0,2]:.2f}, {camera_matrix[1,2]:.2f})")
    print(f"Focal lengths (fx, fy): ({camera_matrix[0,0]:.2f}, {camera_matrix[1,1]:.2f})")
else:
    print("Not enough valid detections for calibration.")
