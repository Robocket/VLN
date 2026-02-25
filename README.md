# 注意修改！

node文件在~/vln/ros/workspace/src/yolo_detection_package

将其中部分参数修改

**\# 添加YOLOv5本地仓库路径，方便调用本地的yolo模型**

line 23
YOLOV5_REPO_PATH = "～/yolov5" **#改为你的yolo仓库**

line 126
self.weights_path = '/home/crl/yolov5/weights_download/yolov5s.pt' **#改为你的权重路径**



## 环境

PyTorch版本： 2.8.0+cu126
适配的CUDA版本： 12.6
Python 3.9.23

目前版本仅使用cpu运行，对torch版本和python版本理论上无特定要求



## 运行

cd ~/vln/ros/workspace

catkin_make 

source devel/setup.bash

roslaunch yolo_detection_package yolo_detection.launch

运行前需确保激光雷达正确发布Odometry话题，realsense能正常显示rgb图像

