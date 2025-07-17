import cv2
import numpy as np

# Load and preprocess image


img = cv2.imread("test_img2.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)



# Optional: Enhance contrast using CLAHE
clahe = cv2.createCLAHE(clipLimit= 1, tileGridSize=(10, 10))
enhanced = clahe.apply(gray)

# Optional: Blur to suppress texture noise
blurred = enhanced
blurred = cv2.GaussianBlur(enhanced, (7, 7), 5)

# bg = cv2.medianBlur(blurred, 5)
# foreground = cv2.subtract(blurred, bg)
# cv2.imshow("Foreground", foreground)

mask = cv2.inRange(blurred, 70, 150)
# Optional: clean the mask up
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
cv2.imshow("Mask", mask)

# Set up the SimpleBlobDetector parameters
params = cv2.SimpleBlobDetector_Params()

# Filter by circularity (set min to 0.7+ for round shapes)
params.filterByCircularity = False
# params.minCircularity = 0.2

# Filter by area (helps remove small blobs or huge junk)
params.filterByArea = True
params.minArea = np.pi*14**2
params.maxArea = np.pi*20**2  # adjust based on pad size

# # Filter by convexity (optional, controls how “bulging” the shape is)
params.filterByConvexity = False
params.minConvexity = 0.1

# Filter by inertia (optional, helps detect roundish shapes)
params.filterByInertia = True
params.minInertiaRatio = 0.1

# You can also filter by color (black blobs on white background)
params.filterByColor = True
params.blobColor = 0

# Create a detector with the parameters
detector = cv2.SimpleBlobDetector_create(params)

# Detect blobs
keypoints = detector.detect(blurred)

# Draw detected blobs as red circles
output = img.copy()
for kp in keypoints:
    x, y = int(kp.pt[0]), int(kp.pt[1])
    r = int(kp.size / 2)

    # Draw red circle (optional)
    cv2.circle(output, (x, y), r, (0, 0, 255), 2)

    # Draw big blue box around the blob
    cv2.rectangle(output, (x - r, y - r), (x + r, y + r), (255, 0, 0), 3)

print(f"Detected {len(keypoints)} blobs.")

# Show results
cv2.imshow("Blob Detection", output)
cv2.imshow("Blurred", blurred)
cv2.waitKey(0)
cv2.destroyAllWindows()