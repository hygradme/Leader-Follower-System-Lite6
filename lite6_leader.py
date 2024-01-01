import time
from dynamixel_sdk import *                    # Uses Dynamixel SDK library
import math


def convert_dxl_to_int32(dxl_value):
    # 32ビット符号付き整数の最大値
    INT32_MAX = 2147483647

    # 値が32ビット符号付き整数の最大値より大きい場合、負の値として解釈
    if dxl_value > INT32_MAX:
        return dxl_value - 4294967296  # 2^32から引く
    else:
        return dxl_value  # そのままの値を使用

class Lite6Leader:
    def __init__(self, DEVICENAME, DXL_IDs):
        # Control table address
        self.ADDR_PRO_PRESENT_POSITION = 132               # DXLの現在位置アドレス

        # Protocol version
        PROTOCOL_VERSION = 2.0                       # Dynamixelのプロトコルバージョン

        # Default setting
        self.DXL_IDs = DXL_IDs#[1, 2, 3, 4, 5, 6, 7]                 # DXLのIDリスト
        BAUDRATE = 1000000#115200#57600                             # Dynamixelのボーレート
        # DEVICENAME = 'COM3'                          # ポート名
        TORQUE_ENABLE = 1                            # トルクをON
        TORQUE_DISABLE = 0                           # トルクをOFF
        DXL_MOVING_STATUS_THRESHOLD = 20             # DXLの移動ステータスのしきい値

        self.angle_offsets = [180] * len(self.DXL_IDs)

        # Initialize PortHandler instance
        # Set the port path
        self.portHandler = PortHandler(DEVICENAME)

        # Initialize PacketHandler instance
        # Set the protocol version
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)

        # Open port
        if self.portHandler.openPort():
            print("Port opened successfully")
        else:
            print("Failed to open the port")
            quit()

        # Set port baudrate
        if self.portHandler.setBaudRate(BAUDRATE):
            print("Baudrate set successfully")
        else:
            print("Failed to set baudrate")
            quit()

    def old_get_angles_from_leader(self, is_radian=True):
        angles = []

        for i, dxl_id in enumerate(self.DXL_IDs):
            # Read present position
            start_time = time.time()
            dxl_present_position, dxl_comm_result, dxl_error = self.packetHandler.read4ByteTxRx(self.portHandler, dxl_id, self.ADDR_PRO_PRESENT_POSITION)
            end_time = time.time()
            print(f"dxl{dxl_id} took {end_time- start_time} [s]")
            if dxl_comm_result != COMM_SUCCESS:
                print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                print("%s" % self.packetHandler.getRxPacketError(dxl_error))

            # Convert to degree (assuming the motor is using default settings)
            angle = (convert_dxl_to_int32(dxl_present_position) / 4096) * 360 - self.angle_offsets[i]
            if is_radian:
                angle = angle * math.pi / 180
            angles.append(angle)
        return angles
    
    def old_2byte_get_angles_from_leader(self, is_radian=True):
        angles = []

        for i, dxl_id in enumerate(self.DXL_IDs):
            # Read present position (2 bytes instead of 4)
            start_time = time.time()
            dxl_present_position, dxl_comm_result, dxl_error = self.packetHandler.read2ByteTxRx(self.portHandler, dxl_id, self.ADDR_PRO_PRESENT_POSITION)
            end_time = time.time()
            # print(f"dxl{dxl_id} took {end_time- start_time} [s]")

            if dxl_comm_result != COMM_SUCCESS:
                print("%s" % self.packetHandler.getTxRxResult(dxl_comm_result))
            elif dxl_error != 0:
                print("%s" % self.packetHandler.getRxPacketError(dxl_error))

            # Convert to degree and adjust
            # Note: The conversion factor might need to be adjusted based on the encoder resolution
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
                # Note: The conversion factor might need to be adjusted based on the encoder resolution
                angle = (convert_dxl_to_int32(dxl_present_position) / 4096) * 360 - self.angle_offsets[i]
                if is_radian:
                    angle = angle * math.pi / 180
                angles.append(angle)
            else:
                print(f"Failed to get data for DXL ID: {dxl_id}")

        # Clear the bulk read parameters
        groupBulkRead.clearParam()

        return angles

if __name__ == "__main__":
    leader = Lite6Leader()

    while True:
        angles = leader.get_angles_from_leader()
        print(angles)
        time.sleep(0.02)  # 0.02秒待機
