# VLN

基于 RGB-D 检测、自然语言目标选择和点云 A* 规划的视觉语言导航原型。
运行环境为 **Ubuntu 24.04 / ROS 2 Jazzy / Python 3.12**。

```text
src/
  vln_interfaces/      四种自定义消息
  vln_perception/      YOLOv5 检测、深度投影、物体坐标与 Marker
  vln_navigation/      指令话题、可选 GGUF 目标选择、终端指令入口
  vln_planner/         C++ A* 点云栅格规划
  vln_bringup/         launch、参数和 RViz 2 配置
examples/              摄像头预览、YOLO + ORB 实验
tools/                PyTorch / Transformers 环境检查
tests/                ROS 2 跨节点集成测试
docs/                 ROS 2 配置和运行说明
```

仓库根目录即 colcon 工作空间，源码位于 `src/`，构建输出为根目录的 `build/`、`install/` 和 `log/`。
构建目录、模型、录包和本地 `publish/` 论文资料由 `.gitignore` 排除。

## 构建 ROS 2

先安装 Jazzy、colcon 和 rosdep，然后从仓库根目录执行：

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --symlink-install --cmake-args -DPython3_EXECUTABLE=/usr/bin/python3
source install/setup.bash
```

ROS 依赖由 `package.xml` 管理。YOLOv5 仓库、权重、PyTorch 和可选
`llama-cpp-python` 需单独准备，见[运行与迁移说明](docs/ros2-migration.md)。

## 运行

在仓库根目录复制参数文件，并填入本机模型路径和传感器参数：

```bash
cp src/vln_bringup/config/vln.yaml /tmp/vln.local.yaml
# 编辑 /tmp/vln.local.yaml 的 yolov5_repo、weights_path、坐标系和相机外参
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vln_bringup vln.launch.py params_file:=/tmp/vln.local.yaml
```

另开终端，加载相同环境后输入指令：

```bash
ros2 run vln_navigation instruction_cli
# 不加载 LLM 时输入检测类别名，例如 bottle
# 配置 llm_model_path 后可输入自然语言，例如“去最近的椅子”
```

也可以直接发送指令：

```bash
ros2 topic pub --once /vln/instruction std_msgs/msg/String "{data: 'bottle'}"
```

没有模型时可启动目标选择和规划节点，使用外部物体坐标输入：

```bash
ros2 launch vln_bringup vln.launch.py enable_perception:=false
```

规划器发布 `/planned_path`，目前没有路径跟踪器或速度控制器。
传感器驱动、定位和 TF 由外部系统提供。

## 验证

从仓库根目录执行：

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon test --event-handlers console_direct+ --return-code-on-test-failure
colcon test-result --verbose
ROS_DOMAIN_ID=87 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST /usr/bin/python3 -m pytest -q tests/test_ros2_pipeline.py
```

集成测试使用合成 RGB-D / 点云和固定检测结果，验证真实 ROS 2 消息传输、坐标投影、
指令到目标、避障路径及越界拒绝；真实模型推理和机器人运行需要另行验证。
