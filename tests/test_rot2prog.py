"""Unit tests for the Rot2Prog encoding shared by the manager and the simulator.

Both classes open ZMQ sockets in __init__, so the tests build them without
running it. Only the packet arithmetic is exercised: no port is opened and no
rotor is needed.
"""

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import rotor_manager as rm
import rotor_simulator as rs


@pytest.fixture
def manager():
    return rm.RotorManager.__new__(rm.RotorManager)


@pytest.fixture
def simulator():
    return rs.RotorSimulator.__new__(rs.RotorSimulator)


class TestEncodeAngle:
    def test_zero_degrees_carries_the_360_offset(self, manager):
        assert manager._encode_angle(0) == (3, 60)

    def test_splits_into_hundreds_and_remainder(self, manager):
        assert manager._encode_angle(180) == (5, 40)

    def test_both_bytes_always_fit_in_one_byte(self, manager):
        for angle in range(0, 361):
            high, low = manager._encode_angle(angle)

            assert 0 <= high <= 255
            assert 0 <= low <= 255


class TestRoundTrip:
    @pytest.mark.parametrize("angle", [0, 1, 45, 90, 180, 270, 359, 360])
    def test_whole_degrees_survive_encode_then_decode(self, manager, simulator, angle):
        high, low = manager._encode_angle(angle)

        assert simulator._decode_angle(high, low) == pytest.approx(float(angle))

    def test_fractional_degrees_are_truncated_to_whole_degrees(self, manager, simulator):
        """The format carries whole degrees, so 180.7 comes back as 180."""
        high, low = manager._encode_angle(180.7)

        assert simulator._decode_angle(high, low) == pytest.approx(180.0)


class TestBuildPacket:
    def test_packet_is_eleven_bytes(self, manager):
        packet = manager._build_packet(0, 0, rm.CMD_STATUS)

        assert len(packet) == rm.PACKET_SIZE

    def test_packet_is_framed_by_the_start_and_end_bytes(self, manager):
        packet = manager._build_packet(120, 30, rm.CMD_SET)

        assert packet[0] == rm.PACKET_START
        assert packet[-1] == rm.PACKET_END

    def test_the_command_byte_is_the_one_asked_for(self, manager):
        for command in (rm.CMD_SET, rm.CMD_STOP, rm.CMD_STATUS):
            packet = manager._build_packet(0, 0, command)

            assert packet[9] == command

    def test_azimuth_and_elevation_land_in_their_own_fields(self, manager):
        packet = manager._build_packet(azimuth=180, elevation=45, command=rm.CMD_SET)

        assert (packet[1], packet[2]) == manager._encode_angle(180)
        assert (packet[5], packet[6]) == manager._encode_angle(45)

    def test_the_manager_and_the_simulator_agree_on_the_constants(self):
        assert (rm.CMD_SET, rm.CMD_STOP, rm.CMD_STATUS) == (rs.CMD_SET, rs.CMD_STOP, rs.CMD_STATUS)
        assert (rm.PACKET_START, rm.PACKET_END, rm.PACKET_SIZE) == (rs.PACKET_START, rs.PACKET_END, rs.PACKET_SIZE)
