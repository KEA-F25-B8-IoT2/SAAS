from time import sleep
from picamera2 import Picamera2, Preview
from ultralytics import YOLO

# https://docs.ultralytics.com/guides/raspberry-pi/#test-the-camera
## Inference with Camera
### Method 1
####Initialize the Picamera2
picam2 = Picamera2()
picam2.preview_configuration.main.format = "RGB888"
picam2.start()

# Load the default YOLOv11 model
model = YOLO("yolo11n.pt")

while True:
    try:
        frame=picam2.capture_array()
        results=model.predict(frame, conf=0.2, iou=0.3)
        r=results[0]
        s=r.summary()
        sleep(0.5)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        break