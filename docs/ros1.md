# ROS 1 源码

原 `ros/workspace/src/VLN_planner` 移至 `ros1/src/VLN_planner`，保留迁移前的源码和本地修改。
旧构建目录中的路径缓存不能用于新位置，需要在 ROS Noetic 环境中重新构建。
不要在同一个终端混用 Noetic 和 Jazzy。

```bash
source /opt/ros/noetic/setup.bash
cd ros1
catkin build
source devel/setup.bash
roslaunch VLN_planner yolo_detection.launch
```

如需指定 Python，使用 `catkin build --cmake-args -DPYTHON_EXECUTABLE=/path/to/python3`，
并确保该解释器安装了 ROS 1 所需 Python 依赖。旧源码仍保留原本的模型绝对路径，
运行前需按本机环境调整。本次调整只涉及目录结构，没有验证 ROS 1 构建和运行。

原 `cmd.txt` 已移到 `docs/ros1-commands.txt`，录包命令可用于 ROS 1：

```bash
rosbag record -O vln.bag \
  /Odometry /camera/color/image_raw /camera/depth/image_rect_raw \
  /cloud_registered /object/absolute_coords_list /cloud_registered_body \
  /livox/imu /livox/lidar /rosout /tf /tf_static
```
