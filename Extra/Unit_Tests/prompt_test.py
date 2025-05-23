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

# PIN_SON1_ECHO = 7
# PIN_SON1_TRIG = 5

# PIN_SON2_ECHO = 4
# PIN_SON2_TRIG = 17

# PIN_SON3_ECHO = 14
# PIN_SON3_TRIG = 15

# PIN_SON4_ECHO = 12
# PIN_SON4_TRIG = 18

# PIN_NEOPIXEL = 26 # Exp. changed to RGB LED so we can utilise the RGBLED class from the gpiozero module.

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

# arm_activated=False # Is a sorting arm activated? Defaults to False
# arm_default_position=True # "unobstructing" default position

class step_motor(object):
	def __init__(self, pin_1, pin_2, pin_3, pin_4):
		"""Initialize stepper motor. Input the 4 pins."""
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
		for control_pin in self.CONTROL_PINS:
			control_pin.off()

	def arm_degrees(self,desired_degrees):
		""" How many degrees to rotate the arm. """
		output_degrees=int(desired_degrees*(512/360))
		return output_degrees

	def forward(self):
		self.arm_move(self.arm_degrees(70), direction=CCW)

	def backward(self):
		self.arm_move(self.arm_degrees(70), direction=CW)

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
ARM_PLASTIC=step_motor(PIN_STEP1_IN1,PIN_STEP1_IN2,PIN_STEP1_IN3,PIN_STEP1_IN4)
ARM_PAPER=step_motor(PIN_STEP2_IN1,PIN_STEP2_IN2,PIN_STEP2_IN3,PIN_STEP2_IN4)
ARM_CARDBOARD=step_motor(PIN_STEP3_IN1,PIN_STEP3_IN2,PIN_STEP3_IN3,PIN_STEP3_IN4)
# SONAR_LEFTOVER=Sonar(PIN_SON1_ECHO,PIN_SON1_TRIG)
# SONAR_PLASTIC=Sonar(PIN_SON2_ECHO,PIN_SON2_TRIG)
# SONAR_PAPER=Sonar(PIN_SON3_ECHO,PIN_SON3_TRIG)
# SONAR_CARDBOARD=Sonar(PIN_SON4_ECHO,PIN_SON4_TRIG)
ARM_PLASTIC.backward()
ARM_PAPER.backward()
ARM_CARDBOARD.backward()

def main(): # Main program
    while True:
        waste_type=input('Please input the waste type: cardboard, paper plastic or leftover?').lower()
        if waste_type not in ['cardboard', 'paper','plastic', 'leftover']:
            print("NACK. Try again.")
        elif waste_type=='leftover':
            # SONAR_LEFTOVER_START=SONAR_LEFTOVER.distance_cm() # Check current waste height in bin
            conv_start() # Enable conveyer belt
            sleep(5)
            conv_stop()
            # if SONAR_LEFTOVER_START-SONAR_LEFTOVER.distance_cm()>=5: # If height of waste is increased by 5cm or more
            # 	conv_stop() # Disable conveyer belt
        else:
            if waste_type=='cardboard':
                # SONAR_CARDBOARD_START=SONAR_CARDBOARD.distance_cm()
                ARM_CARDBOARD.forward()
                conv_start()
                sleep(5)
                conv_stop()
                ARM_CARDBOARD.backward()
                # if SONAR_CARDBOARD_START-SONAR_CARDBOARD.distance_cm()>=5:
                #     conv_stop()
                #     ARM_CARDBOARD.backward()
            if waste_type=='paper':
                # SONAR_PAPER_START=SONAR_PAPER.distance_cm()
                ARM_PAPER.forward()
                conv_start()
                sleep(5)
                conv_stop()
                ARM_PAPER.backward()
                # if SONAR_PAPER_START-SONAR_PAPER.distance_cm()>=5:
                #     conv_stop
                #     ARM_PAPER.backward()
            if waste_type=='plastic':
                # SONAR_PLASTIC_START=SONAR_PLASTIC.distance_cm()
                ARM_PLASTIC.forward()
                conv_start()
                sleep(5)
                conv_stop()
                ARM_PLASTIC.backward()
                # if SONAR_PLASTIC_START-SONAR_PLASTIC.distance_cm()>=5:
                #     conv_stop()
                #     ARM_PLASTIC.backward()
                        # sleep(3) # Sleep 3 seconds before analysing live-view again


if __name__=='__main__':
	try: # For error handling
		main()
	except Exception:
		print(f"Traceback: \n{traceback.format_exc()}") # Make sure breaking error is printed for debugging.
		conv_stop() # Disable transport belt in case it's running.