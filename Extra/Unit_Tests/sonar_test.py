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

##########################################################################################
"""
THE FOLLOWING SECTION IS FOR HARDWARE RELATED FUNCTIONS AND VAR/CONSTS
"""
##########################################################################################

# PINS
PIN_MOTOR_BELT = 10 

PIN_STEP1_IN1 = 7
PIN_STEP1_IN2 = 5
PIN_STEP1_IN3 = 17
PIN_STEP1_IN4 = 4

PIN_STEP2_IN1 = 15
PIN_STEP2_IN2 = 14
PIN_STEP2_IN3 = 16
PIN_STEP2_IN4 = 3

PIN_STEP3_IN1 = 2
PIN_STEP3_IN2 = 23
PIN_STEP3_IN3 = 18
PIN_STEP3_IN4 = 12

PIN_SON1_ECHO = 6
PIN_SON1_TRIG = 13

PIN_SON2_ECHO = 24
PIN_SON2_TRIG = 27

PIN_SON3_ECHO = 25
PIN_SON3_TRIG = 11

PIN_SON4_ECHO = 22
PIN_SON4_TRIG = 9

PIN_NEOPIXEL = 26 # Exp. changed to RGB LED so we can utilise the RGBLED class from the gpiozero module.
# VARS

class Sonar(DistanceSensor):
	def __init__(self,pin_echo,pin_trigger):
		""" Initialize the sonar. Input echo and trigger pins."""
		super().__init__(echo=pin_echo,trigger=pin_trigger)

	@property # @Property decorator to access the attribute instead of calling the function, like in the original distancesensor
	def distance_cm(self):
		""" Sonar defaults to return distance in m. Convert this to cm."""
		return self.distance*100 # .distance is a constantly updating attribute, and not a function that should be called.

def conv_start():
	MOTOR_BELT.value=0.7

def conv_stop():
	MOTOR_BELT.off()

##### OBJECTS
MOTOR_BELT=PWMLED(PIN_MOTOR_BELT) # Create instance, and make sure it's off.
SONAR_PLASTIC=Sonar(PIN_SON1_ECHO,PIN_SON1_TRIG)
SONAR_PAPER=Sonar(PIN_SON2_ECHO,PIN_SON2_TRIG)
SONAR_CARDBOARD=Sonar(PIN_SON3_ECHO,PIN_SON3_TRIG)
SONAR_LEFTOVER=Sonar(PIN_SON4_ECHO,PIN_SON4_TRIG)

def main(): # Main program
	while True:
		print("plastic:", SONAR_PLASTIC.distance_cm)
		print("paper:", SONAR_PAPER.distance_cm)
		print("cardboard:", SONAR_CARDBOARD.distance_cm)
		print("leftover:", SONAR_LEFTOVER.distance_cm)
		sleep(0.5)

if __name__=='__main__':
	try: # For error handling
		main()
	except Exception:
		print(f"Traceback: \n{traceback.format_exc()}") # Make sure breaking error is printed for debugging.
		conv_stop() # Disable transport belt in case it's running.