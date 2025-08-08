import cv2
import numpy as np
import glob

# === USER PARAMETERS ===
CHECKERBOARD = (4, 5)  # number of inner corners per chessboard row and column
SQUARE_SIZE = 0.0800    # size of a square in meters (change to your actual)

# Termination criteria for corner refinement
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Prepare object points: (0,0,0), (1,0,0), (2,0,0), ...
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

# Arrays to store points
objpoints = []  # 3D points in real world
imgpoints = []  # 2D points in image plane

images = glob.glob('checkerboard_imgs/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        objpoints.append(objp)

        corners_refined = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1), criteria
        )
        imgpoints.append(corners_refined)

        cv2.drawChessboardCorners(img, CHECKERBOARD, corners_refined, ret)
        cv2.imshow('Chessboard', img)
        cv2.waitKey(500)
    else:
        print(f"{fname}: Chessboard NOT detected")

cv2.destroyAllWindows()

# Calibration
if len(objpoints) > 0:
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )
    print("\nCalibration successful.")
    print("Camera matrix:\n", mtx)
    print("Distortion coefficients:\n", dist.ravel())
else:
    print("No valid chessboard detections found.")
