from gpiozero import PWMLED
from time import sleep

# MOTOR_BELT_LED=LED(10) # Brug predefineret klasse til at styre motor
# .ON() resulterer i ca. 1.7W og 0.3A, uden andet.

MOTOR_BELT=PWMLED(10)
MOTOR_BELT.off() # Sørg for at den starter slukket
def led_test():
    try:
        MOTOR_BELT.on()
        sleep(2)
        MOTOR_BELT.off()
    except Exception as e:
        print(e)

def pwm_test():
    try:
        for i in range(0,11): 
            MOTOR_BELT.value=i/10 # /10 er nemmeste måde, da range ikke understøtter floats, og det ellers kræver import af andre libs/moduler
            sleep(2)
        MOTOR_BELT.off() # Sluk for motor
    except Exception as e:
        print(e)