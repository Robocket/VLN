# ROS 2 迁移与运行约定

## 包和接口

| ROS 2 包 | 接口或运行入口 |
| --- | --- |
| `vln_interfaces` | `vln_interfaces/msg` 中的四种消息 |
| `vln_perception` | `ros2 run vln_perception yolo_detection_node` |
| `vln_navigation` | `ros2 run vln_navigation vln_goal` |
| `vln_navigation` | `/vln/instruction` 话题，另开 `instruction_cli` 输入 |
| `vln_planner` | `ros2 run vln_planner a_star_planner_node` |
| `vln_bringup` | `ros2 launch vln_bringup vln.launch.py` |

接口包与 Python 实现分开，避免消息生成与 Python 包安装混用。
ROS 2 的消息类型名是 `vln_interfaces/msg/ObjectCoordinates` 等。
跨版本联调需要另外配置包含自定义消息的 bridge，或使用 ROS 2 驱动重新采集。

## 推理依赖

构建不加载模型，也不自动下载权重。真实感知需要本地 YOLOv5 checkout
（包含 `models/common.py`）、匹配的 `.pt` 权重、PyTorch 和该 YOLOv5 版本的依赖。
YOLOv5 revision 和权重版本应在部署时一起记录。

如使用虚拟环境，基于系统 `/usr/bin/python3` 并保留 ROS Python 包：

```bash
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r /absolute/path/to/yolov5/requirements.txt
# 仅自然语言选择需要；GPU 编译选项取决于部署环境
python -m pip install llama-cpp-python
```

创建虚拟环境后，用其中的 Python 重新构建节点入口，使 `ros2 run` 使用同一解释器：

```bash
source /opt/ros/jazzy/setup.bash
cd ros2
python -m colcon build --symlink-install --packages-select vln_perception vln_navigation
source install/setup.bash
```

在本地参数文件设置 `yolov5_repo`、`weights_path`；可选设置 `llm_model_path` 为 GGUF。
`llm_gpu_layers: 0` 使用 CPU；默认 `-1` 请求全部层使用可用的 GPU backend。
自然语言解析保留 Qwen 对话模板，输出必须是合法物体索引；不合法输出不会发布目标。
其他模型可能需要调整模板。模型按需加载，直接输入类别名无需 LLM。

## 话题、单位与坐标系

| 话题 | 类型 | 约定 |
| --- | --- | --- |
| `/camera/color/image_raw` | `sensor_msgs/msg/Image` | 转成 BGR8 |
| `/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/msg/Image` | 与彩色图对齐，16UC1 毫米或 32FC1 米 |
| `/camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` | 更新内参；未收到时使用参数内参 |
| `/Odometry` | `nav_msgs/msg/Odometry` | pose 位于配置的 `frame_id` |
| `/cloud_registered` | `sensor_msgs/msg/PointCloud2` | FLOAT32 XYZ，位于相同 `frame_id` |
| `/object_detections` | `vln_interfaces/msg/ObjectDetections` | 检测框为像素单位，保留彩色图 header |
| `/object/absolute_coords_list` | `vln_interfaces/msg/ObjectCoordinates` | 世界坐标中的物体列表 |
| `/object/markers` | `visualization_msgs/msg/MarkerArray` | 物体点与标签 |
| `/yolo_detection_result` | `sensor_msgs/msg/Image` | 标注后的彩色图 |
| `/vln/instruction` | `std_msgs/msg/String` | 自然语言或检测类别名 |
| `/vln_goal` | `geometry_msgs/msg/PoseStamped` | 目标位姿，地面高度默认 0 米 |
| `/planned_path` | `nav_msgs/msg/Path` | 规划结果；失败时为空路径 |

传感器输入使用 SensorData QoS，可接收 best effort 发布者。
输出和指令使用 reliable / volatile QoS；目标选择器需先收到新的坐标消息再接收指令。
彩深时间差默认容限 10ms，位姿与图像时间差容限 200ms；不重复处理相同时间戳。
新默认深度话题要求深度已对齐到彩色图，同分辨率本身不代表完成对齐。

绝对坐标计算为：`p_world = R_odom * (R_camera_to_body * p_camera + t_camera_to_body) + t_odom`。
默认相机外参保留迁移前本地版本的轴顺序，实际部署需以标定结果为准。
里程计 body 必须与该外参对应；当前不通过 TF 自动查询外参或转换输入。
坐标系名称不同的输入会被拒绝。若定位使用 `camera_init`，需同时修改所有节点的
`frame_id` 和 RViz Fixed Frame，或在外部统一变换到 `world`。

## 规划行为与边界

规划器在原点周围创建固定大小栅格，默认分辨率 0.05m，500 × 500 格。
点云按 `z_min` / `z_max` 截取，膨胀半径单位为格。
保留原有 1.4–1.6m 高度切片和一格膨胀作为迁移默认值，实际机器人需调整。
用 ROS 2 原生点云迭代器读取 XYZ，不再依赖 PCL。

收到有效点云、里程计和目标后规划一次，起点或目标被障碍占据时在配置半径内寻找空闲格。
越界目标不会被夹到地图边缘。A* 使用不可变队列代价并阻止对角穿过障碍角点。
当前不提供滚动地图、动态重规划、轨迹执行或 Nav2 action 接口。

感知历史延续“每个类别保留最近一个坐标”的行为，不包含多实例跟踪或过期清理。
`max_object_age` 检查的是列表消息时间，不能保证历史列表中每个物体都刚被看到。
LLM 使用固定快照选择，推理期间 ROS 回调继续执行；列表过期后不会发布该次目标。

## 联调与验证

播放 ROS 2 录包时，所有节点使用相同仿真时钟：

```bash
ros2 launch vln_bringup vln.launch.py params_file:=/tmp/vln.local.yaml use_sim_time:=true
ros2 bag play /path/to/ros2_bag --clock
```

启动参数：`enable_perception`、`enable_goal_selector`、`enable_planner`、`use_rviz`、
`use_sim_time`、`params_file`。开启 RViz 使用 `use_rviz:=true`。

本次验证覆盖 Jazzy 编译和无需权重的自动化测试。真实 YOLO/GGUF 推理、传感器驱动、
标定与实车闭环需要在模型及硬件就绪后验证。

实现参考：[ROS 2 Python 迁移指南](https://repo.test.ros2.org/en/jazzy/How-To-Guides/Migrating-from-ROS1/Migrating-Python-Packages.html)、
[ament_cmake_python 说明](https://github.com/ros2/ros2_documentation/blob/jazzy/source/How-To-Guides/Ament-CMake-Python-Documentation.rst)。
