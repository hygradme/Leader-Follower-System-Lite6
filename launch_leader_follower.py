import math
import time
from robot_controller import RobotContorller
from xarm.wrapper import XArmAPI
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

    ip_robot = "192.168.1.160"
    arm = XArmAPI(ip_robot, is_radian=True)
    DXL_IDs = [1, 2, 3, 4, 5, 6]
    if use_gripper:
        pga = ParalleGripperOpenRB150(arm)
        gripper_id = 8
        DXL_IDs.append(gripper_id)
        gripper_scale = 4
    leader = Lite6Leader(DEVICENAME, DXL_IDs=DXL_IDs)

    DH_params = None
    rc = RobotContorller(arm, DH_params, filter_size=5, filter_type=None)

    # initialize
    angles = leader.get_angles_from_leader(is_radian=True)
    time.sleep(2)

    if use_follower:
        move_to_start_position(arm, angles[:6])
    time.sleep(1)
    print("start following")
    if use_gripper:
        # pga.change_goal_current_val(50)
        time.sleep(0.5)

    while True:
        angles = leader.get_angles_from_leader(is_radian=True)
        print([round(angle * 180 / math.pi, 1) for angle in angles])
        if use_follower:
            rc.move_robot_joint(angles[:6], is_radian=True)
            if use_gripper:
                gripper_pos = int(angles[6] * gripper_scale * 180 / math.pi)
                gripper_pos = max(min(gripper_pos, 250), 0)
                pga.move(gripper_pos)
        else:
            time.sleep(0.02)
        # pos = pga.get_pos()
        # print("position", pos)

