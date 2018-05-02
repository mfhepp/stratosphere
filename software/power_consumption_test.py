  # camtest.py
  # Simple test for external camera unit(s)

import logging
import time
import config
import camera
import sensors
import dra818


def main():
    data = []
    logging.info('Power consumption test started.')
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start top camera recording.')
    cam_top = camera.ExternalCamera(
        config.CAM1_PWR,
        config.CAM1_REC,
        config.CAM1_STATUS)
    status_ok = cam_top.start_recording()
    if status_ok:
        logging.info('Top camera recording started.')
    else:
        logging.error('Problem: Top camera recording already running.')
    for i in range(60):
        if cam_top.get_recording_status():
            logging.info('Top camera recording acknowledgment received.')
            break
        logging.info('Waiting for top camera recording acknowledgment' +
                     ' (%i).' % i)
        time.sleep(1)
    else:
        logging.error('Problem: Top camera recording did not start.')
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start bottom camera recording.')
    cam_bottom = camera.ExternalCamera(
        config.CAM2_PWR,
        config.CAM2_REC,
        config.CAM2_STATUS)
    status_ok = cam_bottom.start_recording()
    if status_ok:
        logging.info('Bottom camera recording started.')
    else:
        logging.error('Problem: Bottom camera recording already running.')
    for i in range(60):
        if cam_bottom.get_recording_status():
            logging.info('Bottom camera recording acknowledgment received.')
            break
        logging.info('Waiting for bottom camera recording acknowledgment' +
                     ' (%i).' % i)
        time.sleep(1)
    else:
        logging.error('Problem: Top camera recording did not start.')
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start LOW power Tx.')
    transceiver = dra818.DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=145.525,
        squelch_level=8)
    transceiver.start_transmitter(full_power=False)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    time.sleep(1)
    transceiver.stop_transmitter()
    logging.info('Transmitter turned off.')
    raw_input('Press ENTER to start HIGH power Tx.')
    transceiver.start_transmitter(full_power=True)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    time.sleep(1)
    transceiver.stop_transmitter()
    logging.info('Transmitter turned off.')
    # Shut down 1 camera and test Tx
    raw_input('Press ENTER to shut down top camera.')
    cam_top.power_on_off()
    raw_input('Press ENTER to when camera shut down.')
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start LOW power Tx.')
    transceiver.start_transmitter(full_power=False)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    time.sleep(1)
    transceiver.stop_transmitter()
    logging.info('Transmitter turned off.')
    raw_input('Press ENTER to start HIGH power Tx.')
    transceiver.start_transmitter(full_power=True)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    # Shut down 2nd camera and test Tx
    raw_input('Press ENTER to shut down bottom camera.')
    cam_top.power_on_off()
    raw_input('Press ENTER to when camera shut down.')
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start LOW power Tx.')
    transceiver.start_transmitter(full_power=False)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    time.sleep(1)
    transceiver.stop_transmitter()
    logging.info('Transmitter turned off.')
    raw_input('Press ENTER to start HIGH power Tx.')
    transceiver.start_transmitter(full_power=True)
    time.sleep(3)
    u, i, t = sensors.get_battery_status()
    data.append((u, i))
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    logging.info('\nSummary:')
    for measurement in data:
        logging.info('\tU=%fV, I=%fA' % measurement)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
