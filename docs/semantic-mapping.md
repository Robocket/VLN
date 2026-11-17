# 离线语义点云建图

脚本读取本地 ROS 2 bag，复用当前 OneStreamer 主动流式理解和投影标注方法，
将实际产生语义点的事件点云合并到一张世界坐标总图。不会读取录包内旧的物体坐标作为新标注。

## 运行

在仓库根目录构建完成后执行：

```bash
bash tools/build_semantic_map.sh \
  --bag data/vln_0420_ros2 \
  --output data/maps/vln_0420_semantic
```

脚本自动加载 Jazzy 和本仓库环境，使用现有 OneStreamer Python、权重及配置。
输出目录必须不存在，避免覆盖已有结果；再次运行时使用新的 `--output` 路径。
本机默认输入是转换后的 ROS 2 MCAP 目录；原始 ROS 1 `.bag` 需要先转换。

```bash
# 自定义分辨率、参数和持续监视任务
bash tools/build_semantic_map.sh \
  --bag data/vln_0420_ros2 --output data/maps/custom_run \
  --voxel-size 0.03 --params-file /absolute/path/vln.local.yaml \
  --task 'Describe new objects when they become clearly visible as the camera moves.'
```

已有本仓库的专用语义 worker 时可增加 `--reuse-worker --socket-path /path/to/worker.sock`。
默认启动并管理本次 worker，完成或报错后释放；不关闭其他服务。
`--no-event-files` 可跳过逐事件的 NPZ、JSON 和图片，`--grounding-tokens` 覆盖定位 token 上限。

## 离线处理与融合规则

先索引点云、里程计、CameraInfo 及所需 TF，再按原始图像源时间戳读取彩色帧。
每个图像使用最近时间的点云和位姿，允许在 `sync_tolerance` 内选择文件中稍后到达的消息。
缺少 CameraInfo 时沿用当前 YAML 中的内参；标注精度仍取决于真实标定。
TF 模式按图像时间查询变换，不使用当前时间的最新变换。

采样率和窗口配置沿用 OneStreamer。与实时节点的忙时丢帧策略不同，离线脚本等待每次
推理完成，再读取下一个图像窗口，因此不会因为 GPU 推理耗时而漏掉后续采样帧。
文件末尾不足 4 帧的窗口也会提交。整个 bag 共用同一流式会话；不会周期性重置问题制造触发。
Silence / Standby 不加入总图；Response 的定位框无效或没有有效语义点时也不加入。
每次有效标注将其完整可见点云加入总图，包含该视角下 label_id=0 的未标注背景。

输入 `/cloud_registered` 已由定位系统对齐到 `world`，这里只做融合，不重新执行 SLAM 或 ICP。
默认体素边长为 0.05 米，使用 floor 计算栅格，因此负坐标也正确分格。
每个事件在每个体素中最多投一票：优先有标签点，选点数最多的类别，平票取较小 label_id。
跨事件再按有效类别票数选择标签；未知标签不会覆盖已有语义。坐标取胜出类别的各事件
体素中心均值，不将前景语义坐标与未知背景平均。

instance_id 只在单次标注内有效，不作为跨视角实例 ID 合并。
`observations` 为体素被多少个事件观察到，`label_votes` 为胜出标签获得的事件票数。
两者是融合统计，不是模型置信度。

## 输出文件

| 文件 | 内容 |
| --- | --- |
| `semantic_map.ply` / `.pcd` | 总图，含未标注背景，RGB 按语义着色 |
| `semantic_labeled.ply` / `.pcd` | 总图中 label_id>0 的点 |
| `semantic_map.npz` | 保留点结构、frame_id 和体素分辨率的 NumPy 数据 |
| `labels.json` | 数字 label_id 到类别名的字典，0 表示未标注 |
| `semantic_map_xy.png` | XY 俯视预览及图例 |
| `configuration.json` | 本次参数、模型路径和输入数据路径 |
| `report.json` | 完成状态、窗口/触发/点数统计、跳过原因和耗时 |
| `states.jsonl` | 每个窗口的真实主动输出和定位输出 |
| `events/` | 每个有效事件的点云 NPZ、区域/时间戳 JSON、投影视角 PNG |

PLY 保存 RGB 和 label_id / observations / label_votes 属性；
[PCD 0.7](https://pointclouds.org/documentation/tutorials/pcd_file_format.html) 使用 PCL 的 packed-float RGB 表示。
不支持自定义属性的查看器通常仍可显示 XYZ 和颜色；完整语义可从 NPZ 读取：

```python
import json
import numpy as np

data = np.load('data/maps/vln_0420_semantic/semantic_map.npz', allow_pickle=False)
points = data['points']
labels = json.load(open('data/maps/vln_0420_semantic/labels.json'))
labeled = points[points['label_id'] > 0]
```

所有生成物均在 Git 忽略的 `data/` 中。若中途中断或出错，保存已完成事件的部分总图并在
报告中标明未完成；不将部分结果冒充整包结果。整包完成但没有语义点时写出空图与报告，
并以非零退出码提示检查状态和触发任务。

## 本地录包实跑

`data/vln_0420_ros2` 的一次实跑读取 473 帧图像，采样 237 帧，处理 60 个窗口，
产生 5 次 Response，其中 3 次包含有效语义点。5 cm 融合后保存 1,888 点，
其中 234 点标为 chair，其余为触发视角中的未标注背景，总耗时约 60 秒。
完整统计和逐窗口原始输出保存在该运行目录中。

这是视觉语言框与深度带关联形成的弱语义图，不是完整房间的稠密语义重建；
本次录包没有 CameraInfo，使用现有标定配置，标签边界与空间位置仍需实物核验。
