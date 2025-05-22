from gpiozero import OutputDevice
import time

# De 4 forbindelser på motoren
IN1 = OutputDevice(9)
IN2 = OutputDevice(11)
IN3 = OutputDevice(27)
IN4 = OutputDevice(13)

# Sæt dem i en liste til senere
CONTROL_PINS = [IN1, IN2, IN3, IN4]

# Full-step-sekvens til motoren
# Vi kører full-step med 2-coil aktivering pga. øget torque
fullstep_seq = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]
CW = 1 # Med uret
CCW = -1 # Mod uret

def move_step(steps, direction=CW, delay=0.001):
    sequence=fullstep_seq if direction == CW else fullstep_seq[-1::-1]
    # 
    for i in range (steps):
        for step in sequence:
            for pin,val in zip(CONTROL_PINS, step):
                pin.value=val
            time.sleep(delay)

def off():
    for i in CONTROL_PINS:
        i.off()

def step_test():
    try:
        input_prompt=int(input("Enter rotation in degrees: ")) # Bed om hvor mange grader den skal drejes.
        # Kun til test.
        input_degrees=int(input_prompt*(512/360)) # Sørg for at input er i grader, som konverteres til steps
        for i in range(5):
            move_step(input_degrees, direction=CW) # Med uret først
            time.sleep(1)
            move_step(input_degrees, direction=CCW) # Mod uret dernæst
            time.sleep(1)
        print("Første del done.")
        off() # Sluk for motorerne, så hver enkelte ikke trækker 0.200A hver.
        print("Slukket 5 sek")
        time.sleep(5)
        for i in range(5):
            move_step(input_degrees, direction=CW) # Med uret først
            time.sleep(1)
            move_step(input_degrees, direction=CCW) # Mod uret dernæst
            time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        print("Slukket for good")
        off()