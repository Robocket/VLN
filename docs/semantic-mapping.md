# 离线场景语义点云建图

脚本读取 ROS 2 bag，复用主动流式场景描述，将每次触发画面中的全部可见点云合并为世界坐标总图。
每个事件的完整描述和原始模型 token 都保留；录包内旧物体坐标不参与标注。

## 运行

```bash
bash tools/build_semantic_map.sh \
  --bag data/vln_0420_ros2 \
  --output data/maps/my_scene_run
```

脚本自动加载 ROS 2 Jazzy、本仓库环境和现有 OneStreamer 权重。
输出目录必须不存在；原始 ROS 1 `.bag` 需先转换为 ROS 2 MCAP/DB3。
`--voxel-size 0.03` 改变分辨率，`--params-file /absolute/path/local.yaml` 指定配置，
`--task '...'` 更改持续问题，`--description-tokens 128` 设置回答长度上限。
`--no-event-files` 跳过单事件 NPZ、JSON 和投影图。
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

为兼容 PCD/PLY 查看器，每个体素另选一个主 `label_id` 用于颜色显示：
每个事件每个体素一票，票数最多的描述胜出，平票取较小 ID。
坐标采用主标签对应的各事件体素中心均值。
`observations` 是观察事件数，`label_votes` 是主标签票数，均不是模型置信度。
主标签仅用于显示，其他场景描述保存在 NPZ 的事件关联表中。

## 输出与读取标签

| 文件 | 内容 |
| --- | --- |
| `semantic_map.pcd` / `.ply` | 总图，含主 label_id、RGB、observations、label_votes |
| `semantic_labeled.pcd` / `.ply` | label_id>0 的点；当前每个有效事件的可见点均有标签 |
| `semantic_map.npz` | points、frame_id、体素分辨率、每个点的所有事件关联 |
| `labels.json` | 数字 label_id → 完整场景描述，0 表示未标注 |
| `scene_events.json` | event_id → 描述、原始 token 序列、源时间和视角元数据 |
| `semantic_map_xy.png` | XY 预览，图例显示标签 ID 与描述摘要 |
| `configuration.json` / `report.json` | 配置和完成状态、窗口/触发/点数/耗时统计 |
| `states.jsonl` | 每个窗口的原始模型状态、回答和 token |
| `events/` | 每次触发的点云 NPZ、完整事件 JSON、投影图 PNG |

单事件点云含 `label_id` 和 `event_id`。总图合并后，一个点可能关联多个事件，
使用 `scene_event_offsets` 与 `scene_event_ids` 组成的压缩索引读取：

```python
import json
import numpy as np

folder = 'data/maps/vln_0420_scene_v2'
data = np.load(f'{folder}/semantic_map.npz', allow_pickle=False)
labels = json.load(open(f'{folder}/labels.json'))
events = json.load(open(f'{folder}/scene_events.json'))
i = 0  # 要查询的总图点索引
point = data['points'][i]
print('显示标签:', int(point['label_id']), labels[str(int(point['label_id']))])
start, end = data['scene_event_offsets'][i:i+2]
for event_id in data['scene_event_ids'][int(start):int(end)]:
    event = events[str(int(event_id))]
    print(event['description'], event['token_ids'])
```

PCD/PLY 保存单个主标签；查看所有关联描述时需同时读取 NPZ 与 JSON。
不支持自定义属性的查看器仍可显示 XYZ/RGB。

所有生成物都在 Git 忽略的 `data/`。中断会保存已完成事件的部分地图，并标明未完成。
整包处理后若没有有效描述，保存空图和诊断报告，以非零退出码提示检查触发任务。

## 本地验证

本地 bag 含 473 张彩色图像，按 8fps 采样得到 237 帧、60 个窗口。
当前方法实跑产生 5 次主动描述，3,869 个输入可见点全部获得标签。
5cm 融合后有 2,631 点、3,137 条场景事件关联，其中 466 个体素保留多个事件，耗时约 56 秒。
实际描述包括笔记本电脑、水瓶、冰箱等场景内容，原文及 token 可在 `scene_events.json` 查看。
完整统计位于 `data/maps/vln_0420_scene_v2/report.json`。
旧 `data/maps/vln_0420_semantic` 是已停用的框关联结果，不代表当前方法。
