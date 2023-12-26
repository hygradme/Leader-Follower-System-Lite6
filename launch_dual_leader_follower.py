import math
import time
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
    DEVICENAME = "COM3"
    use_gripper = True
    use_follower = True
    use_left = True
    use_right = True

    ip_robot_left = "192.168.1.188"
    ip_robot_right = "192.168.1.160"

    if use_left:
        arm_left = XArmAPI(ip_robot_left, is_radian=True)
    else:
        arm_left = create_autospec(XArmAPI)

    if use_right:
        arm_right = XArmAPI(ip_robot_right, is_radian=True)
    else:
        arm_right = create_autospec(XArmAPI)

    DXL_IDs_left = [1, 2, 3, 4, 5, 6]
    DXL_IDs_right = [11, 12, 13, 14, 15, 16]
    if use_gripper:
        pga_left = ParalleGripperOpenRB150(arm_left)
        pga_right = ParalleGripperOpenRB150(arm_right)
        gripper_id_left = [8]
        gripper_id_right =  [18]
        DXL_IDs_left.extend(gripper_id_left)
        DXL_IDs_right.extend(gripper_id_right)
        gripper_scale = 8
        gripper_offset_left = 40
        gripper_offset_right = 40
    DXL_IDs = DXL_IDs_left + DXL_IDs_right
    leader = Lite6Leader(DEVICENAME, DXL_IDs=DXL_IDs)

    DH_params = None
    rc_left = RobotContorller(arm_left, DH_params, filter_size=5, filter_type=None)
    rc_right = RobotContorller(arm_right, DH_params, filter_size=5, filter_type=None)

    # initialize
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
        angles_left = angles[0:6]
        angles_right = angles[7:13]
        print("left:", [round(angle * 180 / math.pi, 1) for angle in angles_left], "right:", [round(angle * 180 / math.pi, 1) for angle in angles_right], "gripper:",round(angles[6] * 180 / math.pi, 1), round(angles[13] * 180 / math.pi, 1))
        leader_time = time.time()
        print("leader took", leader_time - start_time, "[s]")
        if use_follower:
            rc_left.move_robot_joint(angles_left, is_radian=True)
            print("left took", time.time() - leader_time, "[s]")
            rc_right.move_robot_joint(angles_right, is_radian=True)
            print("right took", time.time() - leader_time, "[s]")
            if use_gripper:
                gripper_pos_left = int(angles[6] * gripper_scale * 180 / math.pi) - gripper_offset_left
                gripper_pos_left = max(min(gripper_pos_left, 250), 0)
                pga_left.move(gripper_pos_left)
                gripper_pos_right = -int(angles[13] * gripper_scale * 180 / math.pi) - gripper_offset_right
                gripper_pos_right = max(min(gripper_pos_right, 250), 0)
                pga_right.move(gripper_pos_right)
        else:
            time.sleep(0.02)
        end_time = time.time()
        print(end_time - start_time, "[s]")

        # pos = pga.get_pos()
        # print("position", pos)

