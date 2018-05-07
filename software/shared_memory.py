# shared_memory.py
# All variables in shared memory that need to be accessible to all
# modules of the application

import multiprocessing as mp

# Global variables in shared memory
timestamp = mp.Array("c", "01-01-1970T00:00:00Z")
last_sstv_image = mp.Array("c", "files/sstv-testbild-small.png")
altitude = mp.Value("d", 0.0)
altitude_outdated = mp.Value("i", 1)
altitude_max = mp.Value("d", 25000.0)
latitude = mp.Value("d", 0.0)
latitude_direction = mp.Value("c", "N")
latitude_outdated = mp.Value("i", 1)
longitude = mp.Value("d", 0.0)
longitude_direction = mp.Value("c", "E")
longitude_outdated = mp.Value("i", 1)
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
cam_top_recording = mp.Value("i", 0)
cam_bottom_recording = mp.Value("i", 0)
# Variables for controling graceful shutdown of threads
continue_gps = mp.Value("i", 1)
main_camera_active = mp.Value("i", 1)
sensors_active = mp.Value("i", 1)
imu_logging_active = mp.Value("i", 1)
