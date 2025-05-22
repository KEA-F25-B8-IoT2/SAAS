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

def chart_bar():
    amounts=[
        db_select_last_rowid('person'),db_select_last_rowid('toilet'),
        db_select_last_rowid('laptop'),db_select_last_rowid('restaffald')
        ]
    fig=Figure()
    ax=fig.subplots()
    x=['person','toilet','laptop','restaffald']
    y=[amounts[0],amounts[1],amounts[2],amounts[3]]
    bars=ax.bar(x,y,color=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c'])
    ax.tick_params(axis='x',which='both',rotation=30)
    ax.set_xlabel("Waste type")
    ax.set_ylabel("Pieces of waste")
    ax.set_title("Waste sorting")
    for bar in bars:
        height=bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center',va='bottom')
    ax.plot(x,y)
    for line in ax.get_lines():
        line.remove()
    buf=BytesIO()
    fig.savefig(buf,format="png")
    chart_bar=base64.b64encode(buf.getbuffer()).decode("ascii")
    return chart_bar

@app.route('/')
def index():
    return render_template('index.html',render_chart_bar=chart_bar())

def total_amount_socketio():
    total=db_select_last_rowid('person')+db_select_last_rowid('toilet')+db_select_last_rowid('laptop')+db_select_last_rowid('restaffald')
    socketio.emit('amount_updated',total)

def db_insert(specified_table):
    con=Connection('affaldssortering.db')
    cur=con.cursor()
    timestamp=f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    sql=f"""INSERT INTO {specified_table}(timestamp)VALUES(?)"""
    cur.execute(sql,(timestamp,)) # Single item tuple needed or execute() will throw an error
    con.commit()
    con.close()
    db_updated_socketio()

def db_updated_socketio():
    render_chart_bar=chart_bar()
    socketio.emit('database_updated', render_chart_bar)

def db_select_last_rowid(specified_table):
    con=Connection('affaldssortering.db')
    cur=con.cursor()
    sql=f"""SELECT rowid from {specified_table} ORDER BY rowid DESC LIMIT 1"""
    cur.execute(sql)
    list_id=cur.fetchall() # Fetch from SQL-query
    tuple_id=list_id[0] # Convert from single-item list-nested tuple, to single-item tuple
    total_id, *useless = tuple_id # Convert tuple to single item, and pack rest into useless-variable
    con.close()
    return int(total_id)


##### PROGRAM
def main():
    web_server = threading.Thread(target=threaded_webserver, daemon=True).start()
    while True:
        frame=picam2.capture_array() # Capture pic
        results=model.predict(frame, conf=0.2, iou=0.3) # analyze
        r=results[0] # save results
        s=r.summary() # Summarise results
        if s: # Make sure something is detected.
            # `if s` avoids list index error.
            for res in s:
                print(res['name'])
                socketio.emit('detected_object', res['name'])
                total_amount_socketio()
                if res['name'] not in ['person', 'laptop', 'toilet']:
                    db_insert('restaffald')
                else:
                    db_insert(res['name'])
                    print(f"{res['name']} amount: {db_select_last_rowid(res['name'])}")
        sleep(5)

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print(e)
        print(f"Traceback: \n{traceback.format_exc()}") #Traceback Test