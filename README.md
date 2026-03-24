<h1 align="center">
    GRS Rotor Manager
    <br>
</h1>

<h4 align="center">Antenna Rotor Manager of the SpaceLab's Ground Station.</h4>

<p align="center">
    <a href="https://github.com/spacelab-ufsc/grs-rotor-manager">
        <img src="https://img.shields.io/badge/status-development-green?style=for-the-badge">
    </a>
    <a href="https://github.com/spacelab-ufsc/grs-rotor-manager/releases">
        <img alt="GitHub commits since latest release (by date)" src="https://img.shields.io/github/commits-since/spacelab-ufsc/grs-rotor-manager/latest?style=for-the-badge">
    </a>
    <a href="https://github.com/spacelab-ufsc/grs-rotor-manager/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/license-GPL3-yellow?style=for-the-badge">
    </a>
</p>

<p align="center">
    <a href="#overview">Overview</a> •
    <a href="#dependencies">Dependencies</a> •
    <a href="#usage">Usage</a> •
    <a href="#testing">Testing</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#license">License</a>
</p>

## Overview

The GRS Rotor Manager is an internal component of SpaceLab's Ground Station software pipeline. It is responsible for sending positioning commands to an AlfaSpid RAS-2 azimuth/elevation rotator via the Rot2Prog binary serial protocol, allowing the ground station antenna to physically track a satellite pass.

## Dependencies

* [pyzmq](https://pypi.org/project/pyzmq/)

### Installation

```
pip install pyzmq
```

## Usage

The `RotorManager` class is not meant to be run standalone. It is instantiated and driven by the Station Manager:

```python
from rotor_manager import RotorManager

manager = RotorManager("tcp://localhost:5559")

manager.set_position(azimuth=180.0, elevation=45.0)
manager.request_status()
manager.stop()

manager.close()
```

### ZMQ Interface

Commands sent (to rotator):

| Method | Description |
|---|---|
| `set_position(az, el)` | Commands the rotator to move to the given azimuth and elevation in degrees |
| `stop()` | Commands the rotator to stop immediately and hold its current position |
| `request_status()` | Requests the current azimuth and elevation from the rotator |

Commands are sent over a ZMQ **PUSH** socket. The rotator address is passed to the constructor, keeping the component decoupled from any hardcoded addresses.

Status responses are received over a ZMQ **SUB** socket subscribed to the `status` topic. The payload is two packed 32-bit floats: `(azimuth, elevation)`.

### Rot2Prog Protocol

Commands are encoded as 11-byte binary packets following the Rot2Prog protocol used by the AlfaSpid controller:

| Byte | Content |
|------|---------|
| 1 | `0x57` — START byte |
| 2 | Azimuth high byte |
| 3 | Azimuth low byte |
| 4 | Azimuth pulse high byte |
| 5 | Azimuth pulse low byte |
| 6 | Elevation high byte |
| 7 | Elevation low byte |
| 8 | Elevation pulse high byte |
| 9 | Elevation pulse low byte |
| 10 | Command byte |
| 11 | `0x20` — END byte |

Angles are encoded with a +360° offset to avoid negative values. The pulse bytes are fixed at `0x01, 0x00`, corresponding to 1° resolution as per the Rot2Prog transmission setting.

> **Note:** The rotator must be set to **CPU (Auto) mode** on the front panel for it to respond to software commands. Refer to the AlfaSpid Rot2Prog hardware manual for instructions on switching modes.

## Testing

A standalone simulator is included that mimics the AlfaSpid rotator, useful for testing the full pipeline without hardware. Run it in one terminal:

```
python rotor_simulator.py
```

Then run the provided test script in another terminal:

```
python test_rotor.py
```

## Documentation

The documentation of this project is generated using the Sphinx tool, and it is available [here](https://spacelab-ufsc.github.io/grs-rotor-manager/).

### Dependencies

* Sphinx
* sphinx-rtd-theme

### Building the Documentation

```
make html
```

## License

This project is licensed under GPLv3 license.
