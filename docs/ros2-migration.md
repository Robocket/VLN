# ROS 2 运行约定

当前感知实现为 [OneStreamer 主动流式理解与投影点云标注](streaming-semantics.md)。
模型 worker 与 ROS 进程使用独立 Python 环境；源码位于 `src/perception`。

| ROS 2 包 | 运行入口 |
| --- | --- |
| `vln_perception` | `ros2 run vln_perception streaming_semantics` |
| `vln_navigation` | `ros2 run vln_navigation vln_goal` |
| `vln_navigation` | `ros2 run vln_navigation instruction_cli` |
| `vln_planner` | `ros2 run vln_planner a_star_planner_node` |
| `vln_bringup` | `ros2 launch vln_bringup vln.launch.py` |

接口包保留 `ObjectCoordinate` 和 `ObjectCoordinates`，用于世界坐标中的物体类别与点。
传感器输入使用 SensorData QoS，输出和指令使用 reliable / volatile QoS。
物体坐标使用触发图像的时间戳；录包回放时所有 VLN 节点需设置 `use_sim_time:=true`。

## 目标选择

直接输入已标注类别名无需 LLM。自然语言选择可单独安装 `llama-cpp-python` 并配置
`llm_model_path`，按需加载 GGUF；此部分与 OneStreamer 的视频模型环境独立。
保留 Qwen 对话模板，输出必须是合法物体索引，否则不发布目标。
`llm_gpu_layers: 0` 使用 CPU，默认 `-1` 请求使用可用 GPU backend；与视觉模型共用 GPU 时需考虑显存。

LLM 选择使用固定坐标快照，推理期间 ROS 回调继续执行。列表消息时间超过
`max_object_age` 后拒绝选择或发布。默认目标高度 `goal_height` 为 0 米。

## 规划

`/Odometry`、`/cloud_registered` 和 `/vln_goal` 必须位于配置的 `frame_id`。
规划器默认以原点为中心建立 500×500 栅格，分辨率 0.05m；不提供 TF 自动转换。
点云要求 FLOAT32 XYZ、紧凑行布局和本机字节序。
按 `z_min` / `z_max` 截取高度，`inflation_radius` 单位为格。
默认 1.4–1.6m 高度切片和一格膨胀需按实际机器人调整。

收到有效点云、里程计和目标后规划一次；起点或目标被占据时在配置半径内寻找空闲格。
越界目标不会夹到地图边缘；规划失败发布空路径。A* 阻止对角穿过障碍角点。
当前不包含滚动地图、动态重规划、轨迹执行或 Nav2 action 接口。

## 启动参数

`enable_perception`、`enable_goal_selector`、`enable_planner`、`use_rviz`、
`use_sim_time`、`params_file`、`start_onestreamer_worker`。
仅连接已运行的专用 worker 时使用 `start_onestreamer_worker:=false`，并配置其 socket 路径。
