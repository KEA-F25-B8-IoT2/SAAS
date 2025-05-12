"""
This is a template for .py files,
to ensure a similar and streamlined construction.
"""

##### IMPORTS
import smbus3 # https://pypi.org/project/smbus3/
import gpiozero # https://gpiozero.readthedocs.io/en/stable/index.html 
import threading
import ultralytics # https://docs.ultralytics.com/guides/streamlit-live-inference/ 

from matplotlib.figure import Figure
from picamera2 import Picamera2
from sqlite3 import connection
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

##### PINS



##### CONFIGURATIONS



##### OBJECTS




##### VARIABLES




##### FUNCTIONS



##### PROGRAM
while True:
	try:
		app=Flask(__name__)
		socketio=SocketIO(app)
		
        @app.route("/home")
        def home():

		if __name__==('__main__'):
			socketio.run(app,host="0.0.0.0",debug=True)
	except Exception as e:
		print(e)