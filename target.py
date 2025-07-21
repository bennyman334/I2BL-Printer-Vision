from inference_sdk import InferenceHTTPClient
import base64
from PIL import Image
from io import BytesIO
import json
import cv2



client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="Nr0e8P5NwyJ8r4YDQwha"
)

result = client.run_workflow(
    workspace_name="circledetection-gtnkk",
    workflow_id="custom-workflow-3",
    images={
        "image": "pic.png"
    },
    use_cache=True # cache workflow definition for 15 minutes
)

first_result = result[0]
visualization_b64 = first_result['polygon_visualization']
img_bytes = base64.b64decode(visualization_b64)

with open('output.png', 'wb') as f: 
    f.write(img_bytes)

detections = result[0]['predictions']

img = Image.open(BytesIO(img_bytes))
img.show()

detections_list = detections['predictions']   # Grab the list of detections


centers = []
for det in detections_list: 
    center=(det['x'],det['y'])
    centers.append(center)

print(centers)


img = cv2.imread('pic.png')  # Use your actual image filename
for center in centers:
    x, y = int(center[0]), int(center[1])  # Convert to int for pixel indices
    cv2.circle(img, (x, y), radius=5, color=(0, 0, 255), thickness=-1)  # (B, G, R), so (0, 0, 255) is red
cv2.imshow('Centers Overlay', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite('overlay_centers.png', img)


