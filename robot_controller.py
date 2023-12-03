import sys
import os
import time
from datetime import datetime
import json
import shutil
from collections import deque

import numpy as np
from xarm.wrapper import XArmAPI


class RobotContorller:
    def __init__(self, arm, DH_params, filter_size=5, filter_type=None):
        self.arm = arm
        self.DH_params = DH_params
        self.q_max = [6.283185307179586, 2.61799, 5.235988, 6.283185307179586, 2.1642, 6.283185307179586]
        self.q_min = [-6.283185307179586, -2.61799, -0.061087, -6.283185307179586, -2.1642, -6.283185307179586]
        # self.arm.close_lite6_gripper()

        self.arm.set_mode(mode=1)
        self.arm.set_state(0)

        # Filter related
        self.filter_type = filter_type
        self.filter_size = filter_size
        self.angle_history = deque(maxlen=self.filter_size)

    def check_safety(self, angles, is_radian=True):
        for angle, q_min, q_max in zip(angles, self.q_min, self.q_max):
            assert q_min <= angle and angle <= q_max


    def _apply_median_filter(self, angles):
        self.angle_history.append(angles)
        if len(self.angle_history) < self.filter_size:
            return angles
        medians = np.median(np.array(self.angle_history), axis=0)
        return medians.tolist()

    def _apply_average_filter(self, angles):
        self.angle_history.append(angles)
        if len(self.angle_history) < self.filter_size:
            return angles
        averages = np.mean(np.array(self.angle_history), axis=0)
        return averages.tolist()

    def _apply_weighted_average_filter(self, angles):
        self.angle_history.append(angles)
        if len(self.angle_history) < self.filter_size:
            return angles
        weights = np.linspace(0.5, 1.5, len(self.angle_history))
        weighted_average = np.average(np.array(self.angle_history), axis=0, weights=weights)
        return weighted_average.tolist()

    def reset_filter_history(self):
        """Reset the angle history for the filter."""
        self.angle_history.clear()

    def _apply_filter(self, angles):
        if self.filter_type == "median":
            return self._apply_median_filter(angles)
        elif self.filter_type == "average":
            return self._apply_average_filter(angles)
        elif self.filter_type == "weighted":
            return self._apply_weighted_average_filter(angles)

        return angles

    def move_robot_joint(self, joints, is_radian=True):
        target_angles = joints

        act_target_angles = [ang for ang in target_angles]

        act_target_angles = self._apply_filter(act_target_angles[:6])
        self.check_safety(act_target_angles)
        self.arm.set_servo_angle_j(angles=act_target_angles[:6], is_radian=True)  #, speed=100)#, wait=False)
