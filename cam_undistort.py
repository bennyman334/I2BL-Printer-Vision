import cv2
import numpy as np

# Load calibration (or use mtx, dist from memory)
data = np.load("calibration_data.npz")
K = data["camera_matrix"]
dist = data["dist_coeffs"]
rvecs = data["rvecs"]
tvecs = data["tvecs"]

fx = K[0,0]
fy = K[1,1]
cx = K[0,2]
cy = K[1,2]

print("Camera matrix K:\n", K)
print("Principal point (cx, cy):", (cx, cy))
print("Focal lengths (fx, fy) in pixels:", (fx, fy))

# 1) Draw principal point on an example image
img = cv2.imread("frames/screenshot_3_seconds.png")
h, w = img.shape[:2]
# Undistort for nicer visualization (optional)
newK, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w,h), 1, (w,h))
undist = cv2.undistort(img, K, dist, None, newK)
cv2.imwrite("frames/undistorted_screenshot_3_seconds.png", undist)
# draw principal point (cx,cy) — use original K location (distortion small near center)
cv2.drawMarker(undist, (int(round(cx)), int(round(cy))), (0,0,255), markerType=cv2.MARKER_CROSS, 
               markerSize=20, thickness=2)
cv2.putText(undist, f"Principal point ({cx:.1f},{cy:.1f})", (int(cx)+10, int(cy)-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
cv2.imshow("Principal point", undist)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 2) Camera center (in object coordinates) and optical axis direction for each calibration image
# rvec maps object->camera: X_cam = R * X_obj + t
# Camera center in object coords is C = -R.T @ t
for i, (rvec, tvec) in enumerate(zip(rvecs, tvecs)):
    R, _ = cv2.Rodrigues(rvec)
    cam_center_obj = -R.T.dot(tvec.reshape(3,))   # world (object) coords of camera center
    # optical axis (camera z-axis) in object coords:
    z_cam_in_obj = R.T.dot(np.array([0.,0.,1.]))  # unit vector
    print(f"View {i}: camera center (object coords) = {cam_center_obj}")
    print(f"View {i}: optical axis direction (object coords) = {z_cam_in_obj}\n")

# 3) Map pixel motion → mm on object plane at depth Z (meters)
# At depth Z (distance from camera along camera z axis), a pixel offset dx pixels maps to:
#   ΔX (meters) ≈ (dx * Z) / fx
# So mm-per-pixel at depth Z is: (Z / fx) * 1000

def mm_per_pixel_at_depth(Z_meters, fx_pixels=fx):
    return (Z_meters / fx_pixels) * 1000.0

# Example: if object is approx 1.2 meters from camera
Z = 1.2
print(f"At Z={Z} m, mm per pixel (X direction) = {mm_per_pixel_at_depth(Z):.3f} mm/pixel")

# Also compute how many pixels correspond to desired mm displacement:
def pixels_for_mm(mm, Z_meters, fx_pixels=fx):
    meters = mm / 1000.0
    return (meters * fx_pixels) / Z_meters

print("Pixels required for 5 mm motion at Z=1.2m:", pixels_for_mm(5.0, Z))