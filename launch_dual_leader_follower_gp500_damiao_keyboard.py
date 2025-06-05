# ======================================================================
# ファイル名：main.py
#   ※keyboard_control.pyと同じフォルダに置いてください
# ======================================================================

import math
import json
import time
from unittest.mock import create_autospec

# ここで先ほどの keyboard_control モジュールをインポート
from keyboard_control import getch_nonblocking, cleanup_console

# from xarm.wrapper import XArmAPI
# from lkmtech import MotorController, MultiMotorController
from damiao import MultiMotorController
from robot_controller_gp500 import RobotContorllerGP500
from lite6_leader import Lite6Leader
# from control_openRB150_with_modbus_rtu import ParalleGripperOpenRB150


def move_to_start_position(arm, servo_initial):
    arm.set_servo_angle(angle=servo_initial[:6], is_radian=True, speed=0.3, wait=True)
    time.sleep(0.2)
    arm.set_mode(mode=1)
    arm.set_state(0)
    time.sleep(1)


if __name__ == "__main__":
    # ─── 初期設定 ─────────────────────────────────────────────────────────
    with open('config_gp500.json', 'r') as config_file:
        config = json.load(config_file)

    LEADERDEVICENAME   = config["LEADERDEVICENAME"]
    use_follower       = config["use_follower"]
    use_left           = config["use_left"]
    use_right          = config["use_right"]
    devicename_robot_left  = config["devicename_robot_left"]
    devicename_robot_right = config["devicename_robot_right"]
    DXL_IDs_left       = config["DXL_IDs_left"]
    DXL_IDs_right      = config["DXL_IDs_right"]
    leader_baudrate    = config["leader_baudrate"]

    use_gripper        = config["use_gripper"]
    DXL_IDs = []
    sign_list_left = [1, 1, 1, 1, 1, 1, 1]

    # ─── フォロワー (／モック) 初期化 ────────────────────────────────────────
    arm_left = create_autospec(MultiMotorController)
    if use_left:
        DXL_IDs += DXL_IDs_left
        if use_follower:
            motor_ids = [1,2,3,4,5,6,7]
            arm_left = MultiMotorController(motor_ids, devicename_robot_left)
            print("arm_left is not mock")

    arm_right = create_autospec(MultiMotorController)
    if use_right:
        DXL_IDs += DXL_IDs_right
        if use_follower:
            motor_ids = [0x11,0x12,0x13,0x14,0x15,0x16,0x17]
            arm_right = MultiMotorController(motor_ids, devicename_robot_right)
            print("arm_right is not mock")

    # ─── グリッパー設定 ─────────────────────────────────────────────────────
    if use_gripper:
        gripper_follower_baudrate = config["gripper_follower_baudrate"]
        gripper_id_left  = config["gripper_id_left"]
        gripper_id_right = config["gripper_id_right"]
        gripper_scale    = config["gripper_scale"]
        gripper_offset_left  = config["gripper_offset_left"]
        gripper_offset_right = config["gripper_offset_right"]
        gripper_pos_max_deg  = config["gripper_pos_max_deg"]
        gripper_pos_min_deg  = config["gripper_pos_min_deg"]

        pga_left  = None  # ParalleGripperOpenRB150(arm_left, baudrate=gripper_follower_baudrate)
        pga_right = None  # ParalleGripperOpenRB150(arm_right, baudrate=gripper_follower_baudrate)
        DXL_IDs_left.extend(gripper_id_left)
        DXL_IDs_right.extend(gripper_id_right)

    # ─── リーダーとコントローラの生成 ─────────────────────────────────────────
    leader = Lite6Leader(LEADERDEVICENAME, DXL_IDs=DXL_IDs, BAUDRATE=leader_baudrate)
    DH_params = None
    rc_left  = RobotContorllerGP500(arm_left, DH_params, filter_size=5, filter_type=None)
    rc_right = RobotContorllerGP500(arm_right, DH_params, filter_size=5, filter_type=None)

    # ─── 初期角度取得・キャリブレーション ─────────────────────────────────────
    inital_leader_angles = leader.get_angles_from_leader(is_radian=False)
    time.sleep(2)

    if use_left:
        initial_single_angles_left = arm_left.get_current_single_angles()
        time.sleep(1)
        print("initial_single_angles_left", initial_single_angles_left)
    if use_right:
        initial_single_angles_right = arm_right.get_current_single_angles()
        time.sleep(1)
        print("initial_single_angles_right", initial_single_angles_right)

    if use_left and not use_right:
        inital_leader_angles_left  = inital_leader_angles[0:7]
        inital_leader_angles_right = [None] * 7
    elif use_right and not use_left:
        inital_leader_angles_right = inital_leader_angles[0:7]
        inital_leader_angles_left  = [None] * 7
    else:  # use_left and use_right
        inital_leader_angles_left  = inital_leader_angles[0:7]
        inital_leader_angles_right = inital_leader_angles[7:14]

    # 必要ならここで move_to_start_position(arm_left, …) を呼ぶ
    time.sleep(1)
    print("Ready. Press 'a' to toggle run/stop.")

    # ─── キーボード・フラグ ────────────────────────────────────────────────────
    use_keyboard_control = True
    control_key = "a"
    running = False

    try:
        while True:
            # 1) キー入力チェック（ノンブロッキング）
            if use_keyboard_control:
                key = getch_nonblocking()  # bytes または str, あるいは None
                if key is not None:
                    # Windows 側は bytes なので文字列にし、Linux/macOS はすでに str の想定
                    if isinstance(key, bytes):
                        k = key.decode("utf-8", errors="ignore").lower()
                    else:
                        k = key.lower()

                    if k == control_key:
                        running = not running
                        if running:
                            print(f"--> '{control_key}' pressed: STARTING main loop.")
                        else:
                            print(f"--> '{control_key}' pressed: PAUSING main loop.")

            # 2) running==False の間は元の処理をスキップしてスリープだけ行う
            if not running:
                time.sleep(0.1)
                continue

            # ───── running==True のときだけ、従来のメイン処理を実行 ───────────────
            start_time = time.time()
            angles = leader.get_angles_from_leader(is_radian=False)

            if use_left and not use_right:
                angles_left  = angles[0:7]
                angles_right = [None] * 7
                print("left:", [round(a, 1) for a in angles_left])
            elif use_right and not use_left:
                angles_right = angles[0:7]
                angles_left  = [None] * 7
                print("right:", [round(a, 1) for a in angles_right])
            else:  # both True
                angles_left  = angles[0:7]
                angles_right = angles[7:14]
                print("left:",  [round(a,1) for a in angles_left],
                      "right:", [round(a,1) for a in angles_right])

            if use_follower:
                if use_left:
                    rc_left.move_robot_joint(angles_left, is_radian=False)
                if use_right:
                    rc_right.move_robot_joint(angles_right, is_radian=False)
                if use_gripper:
                    gripper_pos_right = -int(angles[13] * gripper_scale) - gripper_offset_right
                    gripper_pos_right = max(min(gripper_pos_right, gripper_pos_max_deg), gripper_pos_min_deg)
                    pga_right.move(gripper_pos_right)

                    gripper_pos_left = int(angles[6] * gripper_scale) - gripper_offset_left
                    gripper_pos_left = max(min(gripper_pos_left, gripper_pos_max_deg), gripper_pos_min_deg)
                    pga_left.move(gripper_pos_left)
                    print("act gripper val", gripper_pos_left, gripper_pos_right)

            end_time = time.time()
            print(f"{(end_time - start_time)*1000:.1f} [ms]")

    except KeyboardInterrupt:
        print("\nExit requested. Cleaning up…")
    finally:
        # 終了時にターミナル設定を復元（Linux/macOS 側のみ効果あり）
        cleanup_console()
