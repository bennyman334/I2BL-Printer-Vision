import numpy as np
import cv2
import glob

# Settings
chessboard_size = (4, 5)  # 6 inner corners per row/column
square_size = 8.00         # millimeters

# Prepare object points
objp = np.zeros((chessboard_size[0]*chessboard_size[1],3), np.float32)
objp[:,:2] = np.mgrid[0:chessboard_size[0],0:chessboard_size[1]].T.reshape(-1,2)
objp = objp * square_size

objpoints = []
imgpoints = []

images = glob.glob('charuco_imgs/*.jpg')  # Adjust path if needed

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)
        # Optional: draw and display
        cv2.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv2.imshow('img', img)
        cv2.waitKey(100)
cv2.destroyAllWindows()

# Calibrate
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
print("Camera matrix:\n", mtx)
print("Distortion coefficients:\n", dist)
print("Reprojection error:", ret)

# Save to file
np.savez('calibration_data.npz', cameraMatrix=mtx, distCoeffs=dist)
