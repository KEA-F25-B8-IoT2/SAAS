##########################################################################################
"""
THE FOLLOWING SECTION IS FOR IMPORTS
"""
##########################################################################################

##### IMPORTS
import threading
import base64
import traceback

from time import sleep
from ultralytics import YOLO
from sqlite3 import Connection
from io import BytesIO
from matplotlib.figure import Figure

from datetime import datetime, timedelta
from picamera2 import Picamera2, Preview
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from gpiozero import PWMLED, OutputDevice, DistanceSensor

# https://docs.ultralytics.com/guides/raspberry-pi/#test-the-camera
## Inference with Camera
picam2 = Picamera2() # Instantiate
picam2.preview_configuration.main.format = "RGB888" # Set format
picam2.start() # Start camera
model= YOLO("waste.pt")
def main(): # Main program
# global arm_activated, arm_default_position # Make sure variables are usable ## Is this useful or just clutter?
    while True:
        frame=picam2.capture_array() # Capture pic
        results=model.predict(frame, conf=0.5, iou=0.3, save=True) # analyze
        # Conf 0.5-0.7 is usually good enough for initial phases and testing. Hence we don't want anything if the model is not at least 0.5 confident.
        r=results[0] # save results
        s=r.summary() # Summarise results
        print(s)
        if s:
            break
        sleep(1)

if __name__=='__main__':
	try: # For error handling
		main()
	except Exception:
		print(f"Traceback: \n{traceback.format_exc()}") # Make sure breaking error is printed for debugging.