import cv2
import numpy as np

#Load the image
img = cv2.imread("chessBoards/WIN_20250827_16_07_32_Pro.jpg")

# Color-segmentation to get binary mask
lwr = np.array([0, 0, 176])
upr = np.array([179, 160, 255]) #165
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
msk = cv2.inRange(hsv, lwr, upr)

# Extract chess-board
krn = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 30))
dlt = cv2.dilate(msk, krn, iterations=5)
res = 255 - cv2.bitwise_and(dlt, msk)

cv2.imshow("Chessboard", res)
cv2.waitKey(0)

# Displaying chess-board features
res = np.uint8(res)
ret, corners = cv2.findChessboardCorners(res, (9, 9),
                                         flags=cv2.CALIB_CB_ADAPTIVE_THRESH +
                                               cv2.CALIB_CB_FAST_CHECK +
                                               cv2.CALIB_CB_NORMALIZE_IMAGE)
if ret:
    print(corners)
    fnl = cv2.drawChessboardCorners(img, (9, 9), corners, ret)
    cv2.imshow("fnl", fnl)
    cv2.waitKey(0)
else:
    print("No Checkerboard Found")


# import cv2
# import numpy as np

# def nothing(x):
#     pass

# # Load your image
# img = cv2.imread("chessBoards/WIN_20250827_16_07_32_Pro.jpg")
# if img is None:
#     raise FileNotFoundError("Image not found. Check the filename/path.")

# # Convert to HSV
# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# # Create window for trackbars
# cv2.namedWindow("Trackbars")

# # Create HSV trackbars
# cv2.createTrackbar("H_low", "Trackbars", 0, 179, nothing)
# cv2.createTrackbar("H_high", "Trackbars", 179, 179, nothing)
# cv2.createTrackbar("S_low", "Trackbars", 0, 255, nothing)
# cv2.createTrackbar("S_high", "Trackbars", 255, 255, nothing)
# cv2.createTrackbar("V_low", "Trackbars", 0, 255, nothing)
# cv2.createTrackbar("V_high", "Trackbars", 255, 255, nothing)

# while True:
#     # Get trackbar positions
#     hL = cv2.getTrackbarPos("H_low", "Trackbars")
#     hH = cv2.getTrackbarPos("H_high", "Trackbars")
#     sL = cv2.getTrackbarPos("S_low", "Trackbars")
#     sH = cv2.getTrackbarPos("S_high", "Trackbars")
#     vL = cv2.getTrackbarPos("V_low", "Trackbars")
#     vH = cv2.getTrackbarPos("V_high", "Trackbars")

#     lower = np.array([hL, sL, vL])
#     upper = np.array([hH, sH, vH])

#     # Threshold HSV image
#     mask = cv2.inRange(hsv, lower, upper)
#     result = cv2.bitwise_and(img, img, mask=mask)

#     # Show windows
#     cv2.imshow("Original", img)
#     cv2.imshow("Mask", mask)
#     cv2.imshow("Result", result)

#     # Press ESC to exit
#     key = cv2.waitKey(1) & 0xFF
#     if key == 27:
#         print("Final Lower HSV:", lower)
#         print("Final Upper HSV:", upper)
#         break

# cv2.destroyAllWindows()
