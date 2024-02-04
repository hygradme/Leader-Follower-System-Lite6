import time
from dynamixel_sdk import *
import math


def convert_dxl_to_int32(dxl_value):
    INT32_MAX = 2147483647

    if dxl_value > INT32_MAX:
        return dxl_value - 4294967296
    else:
        return dxl_value

class Lite6Leader:
    def __init__(self, DEVICENAME, DXL_IDs, BAUDRATE=57600):
        self.ADDR_PRO_PRESENT_POSITION = 132

        PROTOCOL_VERSION = 2.0

        # Default setting
        self.DXL_IDs = DXL_IDs
        # BAUDRATE = 1000000  #115200#57600
        TORQUE_ENABLE = 1
        TORQUE_DISABLE = 0
        DXL_MOVING_STATUS_THRESHOLD = 20

        self.angle_offsets = [180] * len(self.DXL_IDs)
        self.portHandler = PortHandler(DEVICENAME)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)

        if self.portHandler.openPort():
            print("Port opened successfully")
        else:
            print("Failed to open the port")
            quit()

        if self.portHandler.setBaudRate(BAUDRATE):
            print("Baudrate set successfully")
        else:
            print("Failed to set baudrate")
            quit()

    def old_2byte_get_angles_from_leader(self, is_radian=True):
        angles = []

        for i, dxl_id in enumerate(self.DXL_IDs):
            # Read present position (2 bytes instead of 4)
            start_time = time.time()
            dxl_present_position, dxl_comm_result, dxl_error = self.packetHandler.read2ByteTxRx(self.portHandler, dxl_id, self.ADDR_PRO_PRESENT_POSITION)
            end_time = time.time()

            if dxl_comm_result != COMM_SUCCESS:
                print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                print("%s" % self.packetHandler.getRxPacketError(dxl_error))

            # Convert to degree and adjust
            angle = (dxl_present_position / 4096) * 360 - self.angle_offsets[i]
            if is_radian:
                angle = angle * math.pi / 180
            angles.append(angle)

        return angles

    def get_angles_from_leader(self, is_radian=True):
        angles = []
        byte_size = 4

        # Initialize GroupBulkRead instance
        groupBulkRead = GroupBulkRead(self.portHandler, self.packetHandler)

        # Add parameters to the group bulk read
        for dxl_id in self.DXL_IDs:
            groupBulkRead.addParam(dxl_id, self.ADDR_PRO_PRESENT_POSITION, byte_size)

        # Perform bulk read
        dxl_comm_result = groupBulkRead.txRxPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))

        # Check if data is available and then get the data
        for i, dxl_id in enumerate(self.DXL_IDs):
            if groupBulkRead.isAvailable(dxl_id, self.ADDR_PRO_PRESENT_POSITION, byte_size):
                dxl_present_position = groupBulkRead.getData(dxl_id, self.ADDR_PRO_PRESENT_POSITION, byte_size)

                # Convert to degree and adjust
                angle = (convert_dxl_to_int32(dxl_present_position) / 4096) * 360 - self.angle_offsets[i]
                if is_radian:
                    angle = angle * math.pi / 180
                angles.append(angle)
            else:
                print(f"Failed to get data for DXL ID: {dxl_id}")

        groupBulkRead.clearParam()

        return angles

if __name__ == "__main__":
    leader = Lite6Leader()

    while True:
        angles = leader.get_angles_from_leader()
        print(angles)
        time.sleep(0.02)
