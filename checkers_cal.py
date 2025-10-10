# import cv2
# import numpy as np
# import glob

# # Define chessboard size (inner corners!)
# chessboard_size = (9, 9)
# square_size = 0.0465  # in meters or whatever

# objp = np.zeros((np.prod(chessboard_size), 3), np.float32)
# objp[:, :2] = np.mgrid[0:chessboard_size[0],
#                        0:chessboard_size[1]].T.reshape(-1, 2)
# objp *= square_size

# objpoints = []  # 3D real-world points
# imgpoints = []  # 2D image points

# images = glob.glob("chessBoards/*.jpg")

# for fname in images:
#     img = cv2.imread(fname)

#     # --- Preprocessing with HSV segmentation ---
#     hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

#     # Adjust these values depending on your board/lighting!
#     lwr = np.array([0, 0, 170])
#     upr = np.array([179, 165, 255])
#     msk = cv2.inRange(hsv, lwr, upr)

#     krn = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
#     dlt = cv2.dilate(msk, krn, iterations=3)

#     res = 255 - cv2.bitwise_and(dlt, msk)

#     # cv2.imshow("Checkerboard", res)
#     # cv2.waitKey(0)
#     # --- Chessboard detection ---
#     ret, corners = cv2.findChessboardCorners(
#         res, chessboard_size,
#         flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
#               cv2.CALIB_CB_FAST_CHECK +
#               cv2.CALIB_CB_NORMALIZE_IMAGE
#     )

#     if ret:
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         corners2 = cv2.cornerSubPix(
#             gray, corners, (11, 11), (-1, -1),
#             criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
#         )
#         objpoints.append(objp)
#         imgpoints.append(corners2)

#         fnl = cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
#         cv2.imshow("corners", fnl)
#         cv2.waitKey(0)
#     else:
#         print(f"Chessboard not found in {fname}")

# cv2.destroyAllWindows()


import cv2
import numpy as np
import glob

# --- Calibration settings ---
chessboard_size = (9, 9)   # inner corners
square_size = 0.0465       # in meters (or any unit, just be consistent)

# Prepare object points (0,0,0), (1,0,0), (2,0,0), ...
objp = np.zeros((np.prod(chessboard_size), 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0],
                       0:chessboard_size[1]].T.reshape(-1, 2)
objp *= square_size

objpoints = []  # 3D points in real world
imgpoints = []  # 2D points in image plane

images = glob.glob("chessBoards/*.jpg")

for fname in images:
    img = cv2.imread(fname)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # --- Simple HSV preprocessing (tweak these thresholds!) ---
    lwr = np.array([0, 0, 170])
    upr = np.array([179, 165, 255])
    msk = cv2.inRange(hsv, lwr, upr)
    krn = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    dlt = cv2.dilate(msk, krn, iterations=3)
    res = 255 - cv2.bitwise_and(dlt, msk)

    # --- Detect corners ---
    ret, corners = cv2.findChessboardCorners(
        res, chessboard_size,
        flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
              cv2.CALIB_CB_FAST_CHECK +
              cv2.CALIB_CB_NORMALIZE_IMAGE
    )

    if ret:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        corners2 = cv2.cornerSubPix(
            gray, corners, (11, 11), (-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        )
        objpoints.append(objp)
        imgpoints.append(corners2)

        fnl = cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
        cv2.imshow("corners", fnl)
        cv2.waitKey(500)  # show briefly
    else:
        print(f"⚠️ Chessboard not found in {fname}")

cv2.destroyAllWindows()

# --- Calibration ---
if len(objpoints) > 0:
    print("\nRunning calibration...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    print("\n✅ Calibration successful")
    print("Camera matrix (intrinsics):\n", mtx)
    print("\nDistortion coefficients:\n", dist.ravel())

    # --- Reprojection error ---
    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error
    print("\nMean reprojection error:", total_error / len(objpoints))

    # --- Save calibration ---
    np.savez("calibration_data.npz",
             camera_matrix=mtx,
             dist_coeffs=dist,
             rvecs=rvecs,
             tvecs=tvecs)

    print("\n📁 Saved to calibration_data.npz")
else:
    print("❌ No chessboards detected — calibration aborted.")

