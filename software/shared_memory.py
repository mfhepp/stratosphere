# shared_memory.py
# All variables in shared memory that need to be accessible to all
# modules of the application

import multiprocessing as mp

# Global variables in shared memory
timestamp = mp.Array("c", "01-01-1970T00:00:00Z")
last_sstv_image = mp.Array("c", "files/sstv-testbild-small.png")
altitude = mp.Value("d", 0.0)
altitude_outdated = mp.Value("i", 1)
altitude_max = mp.Value("d", 0.0)
latitude = mp.Value("d", 0.0)
latitude_direction = mp.Value("c", "N")
latitude_outdated = mp.Value("i", 1)
longitude = mp.Value("d", 0.0)
longitude_direction = mp.Value("c", "E")
longitude_outdated = mp.Value("i", 1)
course = mp.Value("d", 0.0)
speed = mp.Value("d", 0.0)
continue_gps = mp.Value("i", 1)
next_threshold = -1
internal_temp = mp.Value("d", 0.0)
external_temp = mp.Value("d", 0.0)
external_temp_ADC = mp.Value("d", 0.0)
cpu_temp = mp.Value("d", 0.0)
battery_voltage = mp.Value("d", 0.0)
discharge_current = mp.Value("d", 0.0)
battery_temp = mp.Value("d", 0.0)
battery_discharge_capacity = mp.Value("d", 0.0)
atmospheric_pressure = mp.Value("d", 0.0)
humidity_internal = mp.Value("d", 0.0)
humidity_external = mp.Value("d", 0.0)
motion_sensor_status = mp.Value("i", 0)  # I did not find a ctypes typecode for Boolean :-()
motion_sensor_message = mp.Array("c", "no message from motion sensor")
motion_sensor_G_X = mp.Value("d", 0.0)
motion_sensor_A_X = mp.Value("d", 0.0)
motion_sensor_M_X = mp.Value("d", 0.0)
motion_sensor_pitch = mp.Value("d", 0.0)
motion_sensor_roll = mp.Value("d", 0.0)
motion_sensor_heading = mp.Value("d", 0.0)
