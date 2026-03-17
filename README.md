# GRS Rotor Manager

## Overview

The Rotor Manager is an internal component of the Ground Station software pipeline. It is responsible for sending positioning commands to an AlfaSpid RAS1 azimuth/elevation rotator via the Rot2Prog binary serial protocol, allowing the ground station antenna to physically track a satellite pass.

```
Station Manager
      |
      |-- set_position(az, el) -->  Rotor Manager  --  Rot2Prog packet  -->  AlfaSpid Rotator
      |-- stop()               -->  Rotor Manager
      |-- request_status()     -->  Rotor Manager  <--  status response  --  AlfaSpid Rotator
```

## Dependencies

- Python 3
- `pyzmq`

## Files

- `rotor_manager.py` — the `RotorManager` class, intended to be used by the Station Manager.
- `rotor_simulator.py` — a standalone simulator that mimics the AlfaSpid rotator, for testing without hardware.

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

## ZMQ Interface

### Commands sent (to rotator / simulator)

| Method | Description |
|---|---|
| `set_position(az, el)` | Commands the rotator to move to the given azimuth and elevation in degrees |
| `stop()` | Commands the rotator to stop immediately and hold its current position |
| `request_status()` | Requests the current azimuth and elevation from the rotator |

Commands are sent over a ZMQ **PUSH** socket. The address of the rotator (or simulator) is passed to the constructor.

### Status responses received (from rotator / simulator)

Status responses are received over a ZMQ **SUB** socket on port `5560`, subscribed to the `status` topic. The payload is two packed 32-bit floats: `(azimuth, elevation)`.

## Rot2Prog Protocol

Commands are encoded as 11-byte binary packets following the Rot2Prog protocol used by the AlfaSpid Rot2Prog controller:

| Byte | Content |
|------|---------|
| 1 | `0x57` — START byte ('W') |
| 2 | Azimuth high byte |
| 3 | Azimuth low byte |
| 4 | Azimuth pulse high byte |
| 5 | Azimuth pulse low byte |
| 6 | Elevation high byte |
| 7 | Elevation low byte |
| 8 | Elevation pulse high byte |
| 9 | Elevation pulse low byte |
| 10 | Command byte (`0x0F` stop / `0x1F` status / `0x2F` set) |
| 11 | `0x20` — END byte (space) |

Angles are encoded with a +360° offset to avoid negative values, so 0° azimuth is transmitted as 360 in the packet. The pulse bytes are fixed at `0x01, 0x00` corresponding to 1 degree resolution as per the Rot2Prog transmission setting.

The rotator must be set to **CPU (Auto) mode** on the front panel for it to respond to software commands. Refer to the AlfaSpid Rot2Prog hardware manual for instructions on switching modes.

## Running the Simulator

The simulator mimics the AlfaSpid rotator and is useful for testing the full pipeline without hardware. Run it standalone:

```bash
python rotor_simulator.py
```

It will bind on port `5559` for incoming commands and publish status responses on port `5560`.

## Testing

With the simulator running in one terminal, run the provided test script in another:

```bash
python test_rotor.py
```

Expected simulator output:
```
[Simulator] Running, waiting for commands...
[Simulator] SET POSITION -> Azimuth: 180.0°  Elevation: 45.0°
[Simulator] STATUS request -> Responding with AZ: 180.0°  Elevation: 45.0°
[Simulator] SET POSITION -> Azimuth: 200.0°  Elevation: 60.0°
[Simulator] STOP received. Holding at AZ: 200.0°  Elevation: 60.0°
[Simulator] STATUS request -> Responding with AZ: 200.0°  Elevation: 60.0°
```

Expected manager output:
```
[Manager] Set position -> AZ: 180.0°  EL: 45.0°
[Manager] Status response -> AZ: 180.0°  EL: 45.0°
[Manager] Set position -> AZ: 200.0°  EL: 60.0°
[Manager] Stop command sent
[Manager] Status response -> AZ: 200.0°  EL: 60.0°
```

## Notes

- The `RotorManager` constructor takes the rotator address as a parameter, keeping it decoupled from any hardcoded addresses. Pass `"tcp://localhost:5559"` when using the simulator, or the actual serial-to-IP bridge address when using real hardware.
- ZMQ PUB/SUB has a slow joiner issue at startup where the first messages may be dropped before subscriptions are established. The test script uses `time.sleep()` between commands to avoid this. In production, the Station Manager should account for this with a brief startup delay.
- The simulator does not model real rotator movement speed or inertia — it updates its internal position instantly upon receiving a SET command. A more realistic simulation would interpolate the position over time based on the rotation speeds in the hardware manual (120 sec/360° at 12V, 60 sec/360° at 24V).
