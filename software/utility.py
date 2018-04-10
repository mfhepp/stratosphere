# utility.py
# Utility functions

# run in child process
def blink(led_pin, frequency):
    period = 1./frequency
    while True:
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(led, GPIO.LOW)
        time.sleep(period)
    return
