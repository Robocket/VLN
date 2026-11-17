# VLN

基于 OneStreamer 主动流式理解、投影视角点云语义标注、自然语言目标选择和 A* 规划的原型。
运行环境为 **Ubuntu 24.04 / ROS 2 Jazzy / Python 3.12**。

```text
src/
  interfaces/      物体世界坐标消息
  perception/      OneStreamer 流式接入、投影与触发式点云标注
  navigation/      指令话题、可选 GGUF 目标选择、终端指令入口
  planner/         C++ A* 点云栅格规划
  bringup/         launch、参数和 RViz 2 配置
examples/          摄像头预览
tools/             播放、建图脚本和推理环境检查
tests/             Unix socket 和 ROS 2 跨节点集成测试
docs/              配置和运行说明
```

源码目录使用简短名称，ROS 包名仍为 `vln_interfaces`、`vln_perception` 等。
仓库根目录即 colcon 工作空间，输出为 `build/`、`install/`、`log/`。
本地 `data/`、模型、录包、论文资料和构建目录均由 `.gitignore` 排除。
录包集中放在 `data/bags/`，地图放在 `data/maps/`；原始包保留在 `data/bags/original/`。
播放所需的本地 Livox 接口环境放在 `.cache/ros2_compat_ws/`。

## 构建

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --symlink-install --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

## 主动感知

默认复用 `/home/crl/DDD/EGI/robot-agent` 的 OneStreamer 配置、独立 Python 环境和已有权重。
不启动其摄像头或 ROS 桥接，直接使用本仓库的图像、点云和位姿话题。
NF4、SDPA、视觉缓存、4 帧窗口和 8fps 采样沿用参考配置。
回答长度上限设为 128 token，以保留完整场景描述；每个窗口只执行一次流式推理。

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vln_bringup vln.launch.py
```

运行前检查 `src/bringup/config/vln.yaml` 的图像内参、相机外参和世界坐标系。
生产标定可使用 `transform_mode: tf`，通过图像时间戳查询世界坐标到 optical frame 的变换。
默认 `odometry` 模式保留原 VLN 的相机到机体外参及内参，使用原变换的逆变换将世界点投到画面。
配置文件可通过 `params_file:=/absolute/path/vln.local.yaml` 覆盖。

OneStreamer 的 Silence / Standby 只发布状态。每次主动 Response 后，完整描述和原始 token
序列都关联到该画面中全部可见点：

- `/semantic/cloud`：相机视锥内、遮挡过滤后的点云，包含 `rgb`、`label_id`、`event_id`。
- `/semantic/labels`：完整场景描述、原始 token ID、标签字典、事件 ID 和源时间戳。
- `/semantic/projection`：标注后的相机视角图。
- `/semantic/markers`：在 RViz 显示本次完整场景描述。
- `/semantic/state`：原始主动状态、拒绝原因及时间信息。

同一画面的点共享整句场景标签，标签表示视角上下文。
输出只对应触发窗口最后一帧的快照，不把延迟响应贴到最新点云上。
详细行为与参数见 [主动点云语义标注](docs/streaming-semantics.md)。

更新持续监视任务：

```bash
ros2 topic pub --once /semantic/task std_msgs/msg/String "{data: 'What objects are visible in the current image? Report newly visible objects or a clear semantic scene change.'}"
```

任务更新会重置流式会话并丢弃旧任务在途结果，是否触发仍由模型决定。

## 录包与导航

播放脚本自动加载本地 Livox 接口、发布时钟，并打开彩色图像窗口：

```bash
bash tools/play_bag.sh

# 彩色、深度双窗口与循环播放
bash tools/play_bag.sh --show-depth --loop

# 与当前感知节点同时运行时排除录包旧坐标
bash tools/play_bag.sh --loop --exclude-topics /object/absolute_coords_list
```

图像窗口中按 **空格** 暂停/继续，按 **Q/Esc** 或关闭窗口退出并停止播放器。
支持 `--bag`、`--rate`、`--start-offset`、`--duration`、`--keep-open`；
`--image-topic` 选择图像话题，深度窗口可用 `--depth-topic` 和 `--depth-max` 设置话题和显示量程。
默认 bag 为 `data/bags/vln_0420_ros2`，默认显示 `/camera/color/image_raw`。

同时运行感知时使用 `use_sim_time:=true`。录包内旧物体坐标可用上述参数排除。
输入不再需要深度图；投影直接读取点云。录包缺少 CameraInfo 时使用配置中的内参。

当前场景标签不表示物体位置，因此默认关闭目标选择，感知节点不发布物体坐标。
若有外部 ObjectCoordinates 输入，可用 `enable_goal_selector:=true` 启用原导航接口，
再另开终端加载相同 ROS 环境：

```bash
ros2 run vln_navigation instruction_cli
# 输入外部坐标提供的类别名，例如 chair
# 配置 llm_model_path 后可输入自然语言
```

无需模型的已有物体坐标回放可使用 `enable_perception:=false enable_goal_selector:=true`。
规划器发布 `/planned_path`，不包含路径执行或速度控制器。

## 离线语义建图

```bash
bash tools/build_semantic_map.sh --bag data/bags/vln_0420_ros2 --output data/maps/my_run
```

整包逐窗口推理后，将有效触发视角的语义点云按世界坐标合并，仅保存
PCD 和 JSON 两个文件。JSON 包含完整描述、原始 token、标签表和所有重叠事件关联，
以及每次触发的相机位置、朝向和输入窗口各帧视角，可在 VS Code 中直接查看。
输出目录不能已存在，默认体素分辨率 5 cm；生成物留在 Git 忽略的 `data/`。
处理规则和本地实跑结果见[离线建图说明](docs/semantic-mapping.md)。

## 验证

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon test --event-handlers console_direct+ --return-code-on-test-failure
colcon test-result --verbose
ROS_DOMAIN_ID=87 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST /usr/bin/python3 -m pytest -q tests
```

自动化测试覆盖真实 DDS、Unix socket 协议、主动触发门控、快照一致性、TF、点云遮挡和规划。
CI 使用可控 worker；真实模型效果、坐标标定和实车闭环需要本机验证。
