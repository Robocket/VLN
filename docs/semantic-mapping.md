# 离线场景语义点云建图

脚本读取 ROS 2 bag，复用主动流式场景描述，将每次触发画面中的全部可见点云合并为世界坐标总图。
每个事件的完整描述和原始模型 token 都保留；录包内旧物体坐标不参与标注。

## 运行

```bash
bash tools/build_semantic_map.sh \
  --bag data/bags/vln_0420_ros2 \
  --output data/maps/my_scene_run
```

脚本自动加载 ROS 2 Jazzy、本仓库环境和现有 OneStreamer 权重。
输出目录必须不存在；原始 ROS 1 `.bag` 需先转换为 ROS 2 MCAP/DB3。
`--voxel-size 0.03` 改变分辨率，`--params-file /absolute/path/local.yaml` 指定配置，
`--task '...'` 更改持续问题，`--description-tokens 128` 设置回答长度上限。
已有专用 worker 时可使用 `--reuse-worker --socket-path /path/to/worker.sock`。

## 处理与融合

先索引点云、位姿、CameraInfo 和所需 TF，再按图像源时间采样。
点云和位姿按 150ms 容差匹配，可选择 bag 中稍后到达的消息。
内外参与实时节点一致，默认保留原 VLN 标定，详见[坐标关系](streaming-semantics.md#保留原-vln-标定)。

离线处理等待当前推理完成后继续读取，不会因 GPU 耗时丢弃后续采样帧；文件末尾不足四帧也提交。
整个 bag 共用一个流式会话，不周期性重置以制造触发。Silence / Standby 不加入总图。
每次有效 Response 的完整描述及 token 关联到对应快照的全部可见点。

输入 `/cloud_registered` 已在 `world` 对齐，这里不执行 SLAM 或 ICP。
默认以 5cm 体素融合，负坐标按 floor 分格。重叠体素保留每个相关事件的关联，
可通过事件 ID 找到各次完整描述和 token。重复提交同一事件不会重复计票。

为兼容 PCD 查看器，每个体素另选一个主 `label_id` 用于颜色显示：
每个事件每个体素一票，票数最多的描述胜出，平票取较小 ID。
坐标采用主标签对应的各事件体素中心均值。
`observations` 是观察事件数，`label_votes` 是主标签票数，均不是模型置信度。
主标签仅用于显示，其他场景描述保存在 JSON 的事件关联表中。

## 输出与读取标签

每次建图仅保存两个文件：

| 文件 | 内容 |
| --- | --- |
| `semantic_map.pcd` | 用于查看的总图，含主 label_id、RGB、observations、label_votes |
| `semantic_map.json` | 标签、完整描述、原始 token、相机位姿、每个点的事件关联和运行元数据 |

不生成逐帧日志、单事件文件、预览图、PLY 或重复的标注子集。
JSON 可在 VS Code 中直接打开、折叠和搜索。`labels`、`scene_events`、`metadata` 都是普通 JSON 对象。
`metadata` 中包含是否完成、窗口/事件数量和参数，部分运行不会标成完整结果。
每段描述的 `viewpoint` 保存贴标签时的相机位置、朝向四元数、观察方向、画面向上方向及内参；
`window_viewpoints` 保存本次输入窗口各帧的视角。位置为世界坐标，单位米，四元数顺序为 xyzw。
多视角信息保存在这些事件中，PCD 的单一 VIEWPOINT 字段不代表某一次观察。
坐标约定见[观察视角说明](streaming-semantics.md#每段描述的观察视角)。

```python
import json
from pathlib import Path

data = json.loads(Path('data/maps/vln_0420/semantic_map.json').read_text())
print(data['labels'])  # label_id → 完整描述
print(data['metadata']['status'])
i = 0  # PCD 中点的索引，从 0 开始
for event_id in data['point_event_ids'][i]:
    event = data['scene_events'][str(event_id)]
    print(event['label_id'], event['description'], event['token_ids'])
    print(event['viewpoint']['position'], event['viewpoint']['orientation_xyzw'])
```

`point_event_ids[i]` 对应同目录 PCD 中第 i 个点的全部事件 ID，顺序严格与 PCD 一致。
`scene_events` 通过事件 ID 查询完整描述和原始 token；`labels` 通过标签 ID 查询描述。
坐标、颜色和主 `label_id` 保存在 PCD，JSON 不重复保存几何数据。

`data/bags/` 放录包，`data/maps/` 放地图；全部由 Git 忽略。
终端显示运行进度，中断时保存已有事件及未完成状态到同一 JSON。
没有有效描述时保存空图及状态，以非零退出码提示检查任务。

## 本地验证

本地 bag 含 473 张彩色图像，按 8fps 采样得到 237 帧、60 个窗口。
当前方法实跑产生 5 次主动描述，3,869 个输入可见点全部获得标签。
5cm 融合后有 2,631 点、3,137 条场景事件关联，其中 466 个体素保留多个事件，耗时约一分钟。
实际描述包括笔记本电脑、水瓶、冰箱等场景内容，原文、token 及统计集中在
`data/maps/vln_0420/semantic_map.json`。旧实验地图和调试文件已清理。
