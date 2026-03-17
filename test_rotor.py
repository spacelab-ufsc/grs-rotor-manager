# test_rotor.py
from rotor_manager import RotorManager
import time

manager = RotorManager("tcp://localhost:5559")

# Point to a satellite pass position
manager.set_position(azimuth=180.0, elevation=45.0)
time.sleep(0.5)

# Request current status
manager.request_status()
time.sleep(0.5)

# Simulate a Doppler tracking update mid-pass
manager.set_position(azimuth=200.0, elevation=60.0)
time.sleep(0.5)

# Stop the rotor
manager.stop()
time.sleep(0.5)

manager.request_status()

manager.close()
