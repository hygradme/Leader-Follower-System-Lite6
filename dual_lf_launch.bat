@echo off
set PROJECT_PATH=D:\robot

cd %PROJECT_PATH%\lead_follow_system\LeadFollowSystem
call %PROJECT_PATH%\xarm\t265\t265_lite6_env\Scripts\activate
cd %PROJECT_PATH%\lead_follow_system\LeadFollowSystem
python launch_dual_leader_follower_gp500_damiao_keyboard.py
pause