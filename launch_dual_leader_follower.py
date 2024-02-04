import math
import time
import json
from unittest.mock import MagicMock, create_autospec

from xarm.wrapper import XArmAPI

from robot_controller import RobotContorller
from lite6_leader import Lite6Leader
from control_openRB150_with_modbus_rtu import ParalleGripperOpenRB150


def move_to_start_position(arm, servo_initial):
    arm.set_mode(mode=0)
    arm.set_state(0)
    time.sleep(0.2)

    arm.set_servo_angle(angle=servo_initial[:6], is_radian=True, speed=0.3, wait=True)
    time.sleep(0.2)
    arm.set_mode(mode=1)
    arm.set_state(0)
    time.sleep(1)


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    DEVICENAME = config["DEVICENAME"]
    use_follower = config["use_follower"]
    use_left = config["use_left"]
    use_right = config["use_right"]
    ip_robot_left = config["ip_robot_left"]
    ip_robot_right = config["ip_robot_right"]
    DXL_IDs_left = config["DXL_IDs_left"]
    DXL_IDs_right = config["DXL_IDs_right"]
    leader_baudrate = config["leader_baudrate"]

    use_gripper = config["use_gripper"]

    if use_left:
        arm_left = XArmAPI(ip_robot_left, is_radian=True)
    else:
        arm_left = create_autospec(XArmAPI)

    if use_right:
        arm_right = XArmAPI(ip_robot_right, is_radian=True)
    else:
        arm_right = create_autospec(XArmAPI)

    if use_gripper:
        gripper_follower_baudrate = config["gripper_follower_baudrate"]

        gripper_id_left = config["gripper_id_left"]
        gripper_id_right = config["gripper_id_right"]
        gripper_scale = config["gripper_scale"]
        gripper_offset_left = config["gripper_offset_left"]
        gripper_offset_right = config["gripper_offset_right"]
        gripper_pos_max_deg = config["gripper_pos_max_deg"]
        gripper_pos_min_deg = config["gripper_pos_min_deg"]

        pga_left = ParalleGripperOpenRB150(arm_left, baudrate=gripper_follower_baudrate)
        pga_right = ParalleGripperOpenRB150(arm_right, baudrate=gripper_follower_baudrate)
        DXL_IDs_left.extend(gripper_id_left)
        DXL_IDs_right.extend(gripper_id_right)

    DXL_IDs = DXL_IDs_left + DXL_IDs_right
    leader = Lite6Leader(DEVICENAME, DXL_IDs=DXL_IDs, BAUDRATE=leader_baudrate)

    DH_params = None
    rc_left = RobotContorller(arm_left, DH_params, filter_size=5, filter_type=None)
    rc_right = RobotContorller(arm_right, DH_params, filter_size=5, filter_type=None)

    angles = leader.get_angles_from_leader(is_radian=True)
    time.sleep(2)

    if use_follower:
        move_to_start_position(arm_left, angles[0:6])
        move_to_start_position(arm_right, angles[7:13])
    time.sleep(1)
    print("start following")
    if use_gripper:
        # pga.change_goal_current_val(50)
        time.sleep(0.5)
    while True:
        start_time = time.time()
        angles = leader.get_angles_from_leader(is_radian=True)
        leader_time = time.time()
        angles_left = angles[0:6]
        angles_right = angles[7:13]
        print("left:", [round(angle * 180 / math.pi, 1) for angle in angles_left], "right:", [round(angle * 180 / math.pi, 1) for angle in angles_right], "gripper:",round(angles[6] * 180 / math.pi, 1), round(angles[13] * 180 / math.pi, 1))
        if use_follower:
            rc_left.move_robot_joint(angles_left, is_radian=True)
            rc_right.move_robot_joint(angles_right, is_radian=True)
            if use_gripper:
                gripper_start = time.time()
                gripper_pos_right = -int(angles[13] * gripper_scale * 180 / math.pi) - gripper_offset_right
                gripper_pos_right = max(min(gripper_pos_right, gripper_pos_max_deg), gripper_pos_min_deg)
                pga_right.move(gripper_pos_right)
                # gripper_pos_left = 250 - int(angles[6] * gripper_scale * 180 / math.pi) #- gripper_offset_left  # gello gripper
                gripper_pos_left = int(angles[6] * gripper_scale * 180 / math.pi) - gripper_offset_left  # for my leader gripper
                gripper_pos_left = max(min(gripper_pos_left, gripper_pos_max_deg), gripper_pos_min_deg)
                pga_left.move(gripper_pos_left)
                print("act gripper val",gripper_pos_left, gripper_pos_right)
        else:
            time.sleep(0.01)
        end_time = time.time()
        print(end_time - start_time, "[s]")
