"""
The main python script for waste detection, analyzation and sorting.
"""

##### IMPORTS
import threading
import base64
import traceback

from time import sleep
from datetime import datetime
from ultralytics import YOLO
from sqlite3 import Connection
from io import BytesIO
from matplotlib.figure import Figure

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
		self.arm_move(self.arm_degrees(45), direction=CW)

	def backward(self):
		self.arm_move(self.arm_degrees(45), direction=CCW)

class Sonar(DistanceSensor):
	def __init__(self,pin_echo,pin_trigger):
		""" Initialize the sonar. Input echo and trigger pins."""
		super().__init__(echo=pin_echo,trigger=pin_trigger)

	@property # @Property decorator to access the attribute instead of calling the function, like in the original distancesensor
	def distance_cm(self):
		""" Sonar defaults to return distance in m. Convert this to cm."""
		return self.distance*100 # .distance is a constantly updating attribute, and not a function that should be called.


##### OBJECTS
MOTOR_BELT=PWMLED(PIN_MOTOR_BELT) # Create instance, and make sure it's off.
ARM_PLASTIC=step_motor(PIN_STEP1_IN1,PIN_STEP1_IN2,PIN_STEP1_IN3,PIN_STEP1_IN4)
ARM_PAPER=step_motor(PIN_STEP2_IN1,PIN_STEP2_IN2,PIN_STEP2_IN3,PIN_STEP2_IN4)
ARM_CARDBOARD=step_motor(PIN_STEP3_IN1,PIN_STEP3_IN2,PIN_STEP3_IN3,PIN_STEP3_IN4)
SONAR_LEFTOVER=Sonar(PIN_SON1_ECHO,PIN_SON1_TRIG)
SONAR_PLASTIC=Sonar(PIN_SON2_ECHO,PIN_SON2_TRIG)
SONAR_PAPER=Sonar(PIN_SON3_ECHO,PIN_SON3_TRIG)
SONAR_CARDBOARD=Sonar(PIN_SON4_ECHO,PIN_SON4_TRIG)


# https://docs.ultralytics.com/guides/raspberry-pi/#test-the-camera
## Inference with Camera
picam2 = Picamera2() # Instantiate
picam2.preview_configuration.main.format = "RGB888" # Set format
picam2.start() # Start camera
model= YOLO("waste.pt")
app=Flask(__name__)
socketio=SocketIO(app)

##### FUNCTIONS
def conv_start():
	MOTOR_BELT.value=0.6

def conv_stop():
	MOTOR_BELT.off()

def threaded_webserver():
	socketio.run(app,host='0.0.0.0',port=44380)

def chart_bar():
    amounts=[
        db_select_last_rowid('leftover'),db_select_last_rowid('cardboard'),
        db_select_last_rowid('paper'),db_select_last_rowid('plastic')
        ] # Get last rowid from each table.
    fig=Figure()
    ax=fig.subplots()
    x=['leftover','cardboard','paper','plastic'] # Create x-axis for graph
    y=[amounts[0],amounts[1],amounts[2],amounts[3]] # Create y-axis for graph
    bars=ax.bar(x,y,color=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c']) # Create and colorise bars in graph
    ax.tick_params(axis='x',which='both',rotation=30) # Is this necessary?
    ax.set_xlabel("Waste type")
    ax.set_ylabel("Pieces of waste")
    ax.set_title("Waste sorting")
    for bar in bars: # Insert number of waste items per bar
        height=bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center',va='bottom')
    ax.plot(x,y)
    for line in ax.get_lines():
        line.remove() # Remove ugly blue line from the "usual" graph.
    buf=BytesIO()
    fig.savefig(buf,format="png")
    chart_bar=base64.b64encode(buf.getbuffer()).decode("ascii")
    return chart_bar # Return chart for later use

def db_updated_socketio():
    render_chart_bar=chart_bar()
    socketio.emit('database_updated', render_chart_bar) # Emit socketio/flask to update chart bar

def db_select_last_rowid(specified_table):
    con=Connection('waste_sorting.db') # Connect to DB
    cur=con.cursor()
    sql=f"""SELECT rowid from {specified_table} ORDER BY rowid DESC LIMIT 1""" # Get "total amount of trash for this category" by fetching last rowid from desired table
    cur.execute(sql) # Run sql-command
    list_id=cur.fetchall() # Fetch from SQL-query
    tuple_id=list_id[0] # Convert from single-item list-nested tuple, to single-item tuple
    total_id, *useless = tuple_id # Convert tuple to single item, and pack rest into useless-variable
    con.close()
    return int(total_id) # Make sure total_id is int for future use

@app.route('/') # One page website.
def index():
    return render_template('index.html',render_chart_bar=chart_bar()) # Start website with bar chart.

def db_insert(specified_table):
    con=Connection('waste_sorting.db')
    cur=con.cursor()
    timestamp=f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}" # Get formatted timestamp
    sql=f"""INSERT INTO {specified_table}(timestamp)VALUES(?)"""
    cur.execute(sql,(timestamp,)) # Single item tuple needed or execute() will throw an error
    con.commit()
    con.close()
    db_updated_socketio() # Emit to socketio that the db has been updated

def total_amount_socketio():
    total=db_select_last_rowid('leftover')+db_select_last_rowid('cardboard')+db_select_last_rowid('paper')+db_select_last_rowid('plastic')
    socketio.emit('amount_updated',total)

##### PROGRAM
def main(): # Main program
	# global arm_activated, arm_default_position # Make sure variables are usable ## Is this useful or just clutter?
	web_server = threading.Thread(target=threaded_webserver, daemon=True).start() # Start webserver as a background thread. 'daemon' makes sure the thread shuts down when main script shuts down.
	while True:
		frame=picam2.capture_array() # Capture pic
		results=model.predict(frame, conf=0.2, iou=0.3) # analyze
		r=results[0] # save results
		s=r.summary() # Summarise results
		if s: # Only engage if something is detected. Avoids list index error.
			for res in s: # Engage for every detected object
				print(res['name'])
				socketio.emit('detected_object', res['name'])
				total_amount_socketio()
				if res['name'] not in ['cardboard', 'paper', 'plastic']:
					print(res['name']," inserted into db")
					# SONAR_LEFTOVER_START=SONAR_LEFTOVER.distance_cm() # Check current waste height in bin
					db_insert('leftover') # Send timestamp to database for new deposit
					# conv_start() # Enable conveyer belt
					# if SONAR_LEFTOVER_START-SONAR_LEFTOVER.distance_cm()>=5: # If height of waste is increased by 5cm or more
					# 	conv_stop() # Disable conveyer belt
				else:
					db_insert(res['name'])
					# print(f"{res['name']} amount: {db_select_last_rowid(res['name'])}")
					if res['name']=='cardboard':
						print(res['name']," inserted into db")
						# SONAR_CARDBOARD_START=SONAR_CARDBOARD.distance_cm()
						# ARM_CARDBOARD.forward()
						# conv_start()
						# if SONAR_CARDBOARD_START-SONAR_CARDBOARD.distance_cm()>=5:
						# 	conv_stop()
						# 	ARM_CARDBOARD.backward()
					if res['name']=='paper':
						print(res['name']," inserted into db")
						# SONAR_PAPER_START=SONAR_PAPER.distance_cm()
						# ARM_PAPER.forward()
						# conv_start()
						# if SONAR_PAPER_START-SONAR_PAPER.distance_cm()>=5:
						# 	conv_stop
						# 	ARM_PAPER.backward()
					if res['name']=='plastic':
						print(res['name']," inserted into db")
						# SONAR_PLASTIC_START=SONAR_PLASTIC.distance_cm()
						# ARM_PLASTIC.forward()
						# conv_start()
						# if SONAR_PLASTIC_START-SONAR_PLASTIC.distance_cm()>=5:
						# 	conv_stop()
						# 	ARM_PLASTIC.backward()
		sleep(3) # Sleep 3 seconds before analysing live-view again


if __name__=='__main__':
	try: # For error handling
		main()
	except Exception:
		print(f"Traceback: \n{traceback.format_exc()}") # Make sure breaking error is printed for debugging.
		conv_stop() # Disable transport belt in case it's running.