"""
The main python script for waste detection, analyzation and sorting.
"""

##### IMPORTS
import threading

from time import sleep
from datetime import datetime
from ultralytics import YOLO

from picamera2 import Picamera2, Preview
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from gpiozero import PWMLED, OutputDevice, DistanceSensor

##### VARS AND CONTS
# PINS
PIN_MOTOR_BELT = 10 

PIN_STEP1_IN1 = 19
PIN_STEP1_IN2 = 20
PIN_STEP1_IN3 = 21
PIN_STEP1_IN4 = 23

PIN_STEP2_IN1 = 9
PIN_STEP2_IN2 = 11
PIN_STEP2_IN3 = 27
PIN_STEP2_IN4 = 13

PIN_STEP3_IN1 = 22
PIN_STEP3_IN2 = 25
PIN_STEP3_IN3 = 24
PIN_STEP3_IN4 = 6

PIN_SON1_ECHO = 7
PIN_SON1_TRIG = 5

PIN_SON2_ECHO = 4
PIN_SON2_TRIG = 17

PIN_SON3_ECHO = 14
PIN_SON3_TRIG = 15

PIN_SON4_ECHO = 12
PIN_SON4_TRIG = 18

PIN_NEOPIXEL = 26 # Exp. changed to RGB LED so we can utilise the RGBLED class from the gpiozero module.

# CONSTS
# Fullstep-sequence, dual-coil activation for increased torque
FULLSTEP_SEQUENCE = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

CW = 1 # Clockwise rotation
CCW = -1 # Counter clockwise rotation

# VARS

arm_activated=False # Is a sorting arm activated? Defaults to False
arm_default_position=True # "unobstructing" default position


##### CONFIGURATIONS
class step_motor(object):
	def __init__(self, pin_1, pin_2, pin_3, pin_4):
		"""Initialize stepper motor. Just input the 4 pins."""
		self.IN1 = OutputDevice(pin_1)
		self.IN2 = OutputDevice(pin_2)
		self.IN3 = OutputDevice(pin_3)
		self.IN4 = OutputDevice(pin_4)
		self.CONTROL_PINS=[self.IN1,self.IN2,self.IN3,self.IN4]
		
	def arm_move(self,steps, direction=CW, delay=0.001):
		sequence=FULLSTEP_SEQUENCE if direction == CW else FULLSTEP_SEQUENCE[-1::-1]
		for i in range (steps):
			for step in sequence:
				for pin,val in zip(self.CONTROL_PINS, step):
					pin.value=val
				sleep(delay)

	def arm_off(self):
		for control_pin in CONTROL_PINS:
			control_pin.off()

	def arm_degrees(self,desired_degrees):
		output_degrees=int(desired_degrees*(512/360))
		return output_degrees

	def arm_forward(self,deg):
		self.arm_move(self.arm_degrees(deg), direction=CW)

	def arm_backward(self,deg):
		self.arm_move(self.arm_degrees(deg), direction=CCW)


##### OBJECTS
MOTOR_BELT=PWMLED(PIN_MOTOR_BELT)
MOTOR_BELT.off()
arm_plastic=step_motor(PIN_STEP1_IN1,PIN_STEP1_IN2,PIN_STEP1_IN3,PIN_STEP1_IN4)
arm_paper=step_motor(PIN_STEP2_IN1,PIN_STEP2_IN2,PIN_STEP2_IN3,PIN_STEP2_IN4)
arm_cardboard=step_motor(PIN_STEP3_IN1,PIN_STEP3_IN2,PIN_STEP3_IN3,PIN_STEP3_IN4)


# https://docs.ultralytics.com/guides/raspberry-pi/#test-the-camera
## Inference with Camera
### Method 1
####Initialize the Picamera2
picam2 = Picamera2() # Instantiate
picam2.preview_configuration.main.format = "RGB888" # Set format
picam2.start() # Start camera
model= YOLO("yolo11n.pt")
app=Flask(__name__)
socketio=SocketIO(app)

##### FUNCTIONS
def threaded_webserver():
	socketio.run(app,host='0.0.0.0',port=44380)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>SAAS</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js" integrity="sha512- q/dWJ3kcmjBLU4Qc47E4A9kTB4m3wuTY7vkFJDTZKjTs8jhyGQnaUrxa0Ytd0ssMZhbNua9hE+E7Qv1j+DyZwA==" crossorigin="anonymous">></script>
    </head>
    <body>
        <h1>Smart Automatiseret AffaldsSortering</h1>
        <h2>Software As A Service</h2>
        <h3>Waste detection</h3>
        <p>Object: <span id="obj_det">Waiting for object</span></p>
        <script type="text/javascript">
            var socket = io();
            socket.on('detected_object', function(received_data) {
                document.getElementById('obj_det').innerText = received_data;
            });
        </script>
    </body>
    </html>
    """


##### PROGRAM
def main():
	global arm_activated, arm_default_position
	web_server = threading.Thread(target=threaded_webserver, daemon=True)
	web_server.start()
	while True:
		try:
			frame=picam2.capture_array() # Capture pic
			results=model.predict(frame, conf=0.2, iou=0.3) # analyze
			r=results[0] # save results
			s=r.summary() # Summarise results
			for res in s:
				print(res['name'])
				socketio.emit('detected_object', res['name'])
				if arm_activated==True and arm_default_position==False:
					sleep(5)
					arm_paper.arm_backward(45)
					arm_plastic.arm_backward(45)
					arm_cardboard.arm_backward(45)
					MOTOR_BELT.off()
					arm_activated=False
					arm_default_position=True
				if res['name']=='person' and res['confidence'] >= 0.3 and arm_default_position==True:
					MOTOR_BELT.value = 0.6
					print(res['name'].upper())
				if res['name']=='laptop' and res['confidence'] >= 0.3:
					arm_activated=True
					arm_default_position=False
					print(res['name'].upper())
					arm_paper.arm_forward(45) # 45 Can be changed to desired degree reotation
					arm_plastic.arm_forward(45)
					arm_cardboard.arm_forward()
			sleep(3)
		except Exception as e:
			print(e)
			break
		except KeyboardInterrupt:
			MOTOR_BELT.off()
			break

if __name__=='__main__':
	try:
		main()
	except Exception as e:
		print(e)