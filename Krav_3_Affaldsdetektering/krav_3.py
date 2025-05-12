import cv2
from picamera2 import Picamera2, Preview
from ultralytics import YOLO
from datetime import datetime

# Funktionalitet til at tage billede.
# Blot til at sikre at kamera dur.
def take_picture():
    date_time = datetime.now()
    datetime_img = f"{date_time.strftime('%d-%m-%Y-%H:%M:%S')}.jpg"
    picam = Picamera2()
    config = picam.create_preview_configuration(main={"size": (1080, 1080)}) #Max resolution = 4608x2592
    picam.configure(config)
    picam.start()
    picam.capture_file(f"img/{datetime_img}")
    picam.close()

take_picture()