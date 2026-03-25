# 注意修改！

quat = [q.x, q.y, q.z, q.w]# scipy要求(x,y,z,w)顺序



## 环境

PyTorch版本： 2.8.0+cu126
适配的CUDA版本： 12.6
Python 3.9.23

目前版本仅使用cpu运行，对torch版本和python版本理论上无特定要求



## 运行

cd ~/vln/ros/workspace


catkin build --cmake-args -DPYTHON_EXECUTABLE=/home/k325/miniconda3/envs/vln/bin/python3 #由于使用了虚拟环境所以编译时必须指定python解释器，用caktin_make会默认使用ros的python解释器

source devel/setup.bash

roslaunch yolo_detection_package yolo_detection.launch

运行前需确保激光雷达正确发布Odometry话题，realsense能正常显示rgb图像

