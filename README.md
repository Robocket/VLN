# VLN

基于 RGB-D 目标检测、自然语言目标选择和点云 A* 规划的视觉语言导航原型。
`main` 分支保留 ROS 1 实现；ROS 2 Jazzy 迁移在 `migration/ros2-jazzy` 分支维护。

```text
ros1/src/VLN_planner/   ROS 1 消息、检测、目标选择和 A* 规划
examples/              摄像头预览、YOLO + ORB 实验
tools/                 PyTorch / Transformers 环境检查
docs/                  ROS 1 使用说明和录包命令
```

构建产物、模型、录包、编辑器配置和本地 `publish/` 论文资料由 `.gitignore` 排除。
源码移动后需要在 ROS Noetic 环境重新构建，不复用原位置的构建缓存。

## 构建与运行

从仓库根目录执行：

```bash
source /opt/ros/noetic/setup.bash
cd ros1
catkin build
source devel/setup.bash
roslaunch VLN_planner yolo_detection.launch
```

运行前需要相机、深度和里程计话题；规划器还需要注册后的点云。
模型路径、Python 推理依赖和相机参数需按实际设备配置。
详细操作见 [ROS 1 使用说明](docs/ros1.md)。

环境检查与摄像头实验脚本放在 `tools/` 和 `examples/` 中，分别按需运行。
