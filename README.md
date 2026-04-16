## 运行

cd ~/vln/ros/workspace

catkin build --cmake-args -DPYTHON_EXECUTABLE=/home/k325/miniconda3/envs/vln/bin/python3 

#由于使用了虚拟环境所以编译时必须指定python解释器，用caktin_make会默认使用ros的python解释器

source devel/setup.bash

roslaunch yolo_detection_package yolo_detection.launch

运行前需确保激光雷达和realsense正常发布话题



  git config --global user.email "2444326907@qq.com"
  git config --global user.name "crl"
