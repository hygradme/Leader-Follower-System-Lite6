# Leader Follower System for UFACTORY Lite 6

## Summary
This is leader follower system for UFACTORY Lite 6.

## Gripepr
I use OpenParallelGripper for this project:

https://github.com/hygradme/OpenParallelGripper

If you don't have this gripper, please change the config
"use_gripper": false

## Requirement
- xArm-Python-SDK (https://github.com/xArm-Developer/xArm-Python-SDK)
- dynamixel_sdk (https://github.com/ROBOTIS-GIT/DynamixelSDK)
- numpy

## Usage
Check config.json and fix it to fit your environment.

Launch leader follower system
```
python lauch_dual_leader_follower.py

```

About config.json

    "DEVICENAME": "COM7"
    "use_gripper": true

    "use_follower": true
    If true, the follower robot move. Please be careful. If false, just show the value from leader.

    "use_left": true
    Make either use_left or use_right to true to use this system with single arm configuration.

    "use_right": true

    "ip_robot_left": "192.168.1.188"

    "ip_robot_right": "192.168.1.160"

    "leader_baudrate": 57600
    Default baudrate of Dynamixel is 57600 and you need to use Dynamixel Wizard software to change the baudrate if you need higher frequency control. I recommend 1000000 to avoid unnecessary vibration of follower robots.

    "DXL_IDs_left": [1, 2, 3, 4, 5, 6]
    Dynamixel IDs corresponding to axis 1~6 of left Lite 6

    "DXL_IDs_right": [11, 12, 13, 14, 15, 16],
    Dynamixel IDs corresponding to axis 1~6 of right Lite 6

Gripper config:

    "gripper_follower_baudrate": 115200

    "gripper_id_left": [8]

    "gripper_id_right": [18]

    "gripper_scale": 8

    "gripper_offset_left": 40

    "gripper_offset_right": 40

    "gripper_pos_max_deg": 250

    "gripper_pos_min_deg": 30



