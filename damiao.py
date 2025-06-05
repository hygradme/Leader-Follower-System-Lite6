import math
from DM_CAN import *
import serial
import time
import copy

def precise_delay(duration_in_ms):
    """
    duration_in_ms: 待機時間をミリ秒単位で指定します。
    """
    start_time = time.perf_counter()
    while (time.perf_counter() - start_time) < (duration_in_ms / 1000.0):
        pass  # 何もしないで待機する


class MultiMotorController:
    def __init__(self, motor_ids, channel) -> None:
        motor_data_list = [
            [DM_Motor_Type.DM4340, motor_ids[0], 0x00],
            [DM_Motor_Type.DM4340, motor_ids[1], 0x00],
            [DM_Motor_Type.DM4340, motor_ids[2], 0x00],
            [DM_Motor_Type.DM4340, motor_ids[3], 0x00],
            [DM_Motor_Type.DM4340, motor_ids[4], 0x00],
            [DM_Motor_Type.DM4310, motor_ids[5], 0x00],
            [DM_Motor_Type.DM4310, motor_ids[6], 0x00]
            ]

        self.serial_device = serial.Serial(channel, 921600, timeout=1)
        self.MotorControl1=MotorControl(self.serial_device)

        self.motor_inst_list = []
        for motor_data in motor_data_list:
            motor = Motor(motor_data[0], motor_data[1], motor_data[2])
            self.MotorControl1.addMotor(motor)
            self.MotorControl1.enable(motor)
            self.MotorControl1.switchControlMode(motor,Control_Type.Torque_Pos)
            self.MotorControl1.save_motor_param(motor)
            self.motor_inst_list.append(motor)

        # motor_inst_list.reverse() # to get tcp first
        self.torque = 6000
        self.velocity = 500#5000
        time.sleep(1)
    def __del__(self):
        self.serial_device.close()

    def get_current_single_angles(self):
        self.serial_device.flushInput()
        success_motor_list = []
        for ind, motor_inst in enumerate(self.motor_inst_list):
            motor_data = self.MotorControl1.get_motor_data(motor_inst)
            if motor_data:
                success_motor_list.append(motor_data)
        if len(success_motor_list) == len(self.motor_inst_list):
            position_list = []
            t_mos_list = []
            t_rotor_list = []
            # success_motor_list.reverse() # reverse
            for motor_data in success_motor_list:
                position_list.append(motor_data["pos"]*180/math.pi)
                t_mos_list.append(motor_data["T_MOS"])
                t_rotor_list.append(motor_data["T_Rotor"])
                # print("ID:", motor_data["ID"], ",Err:", motor_data["ERR"], ", pos:",motor_data["pos"], ", speed:", motor_data["speed"], ", torque:", motor_data["torque"], ", T_MOS", motor_data["T_MOS"], ", T_Rotor", motor_data["T_Rotor"])
            print(position_list)
            print("t_mos", t_mos_list)
            print("t_rotor", t_rotor_list)
            return position_list
        return []

    def set_servo_angle_j(self, angles, is_radian=True):
        if is_radian:
            angles_deg = [angle * 180/math.pi for angle in angles]
        else:
            angles_deg = angles
        print("command will be send", angles_deg)
        # return
        motor_data_list = []
        for ind, motor_inst in enumerate(self.motor_inst_list):
            motor_data = self.MotorControl1.control_pos_force(
                motor_inst,
                angles_deg[ind]*math.pi/180,
                self.velocity,
                self.torque
                )
            if len(motor_data) != 0:
                motor_data_list.append(motor_data)
        print("len(motor_data_list)",motor_data_list)
        if len(motor_data_list) == len(angles_deg):
            position_list = []
            torque_list = []
            t_mos_list = []
            t_rotor_list = []
            # success_motor_list.reverse() # reverse
            for motor_data in motor_data_list:
                position_list.append(motor_data["pos"]*180/math.pi)
                torque_list.append(motor_data["torque"])
                t_mos_list.append(motor_data["T_MOS"])
                t_rotor_list.append(motor_data["T_Rotor"])
            print("pos", position_list)
            print("torque", torque_list)
            print("t_mos", t_mos_list)
            print("t_rotor", t_rotor_list)


