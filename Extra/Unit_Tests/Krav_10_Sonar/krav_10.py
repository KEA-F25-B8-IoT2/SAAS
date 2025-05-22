from gpiozero import DistanceSensor, PWMLED
from time import sleep

# Set up the DistanceSensor
sensor = DistanceSensor(echo=7, trigger=5)
MOTOR_BELT=PWMLED(10)
MOTOR_BELT.off()

try:
    while True:
        MOTOR_BELT.value=0.6
        distance = sensor.distance * 100  # sensor.distance gives meters; we convert to cm
        print(f"Distance: {distance:.1f} cm")
        if distance<20:
            MOTOR_BELT.off()
        sleep(2)

except KeyboardInterrupt:
    print("Program stopped")

finally:
    sensor.close()
