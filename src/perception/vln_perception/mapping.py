"""World-frame semantic voxel fusion and portable point cloud export."""

from collections import Counter
import json
from pathlib import Path

import cv2
import numpy as np

from .projection import label_color


MAP_DTYPE = np.dtype([
    ('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('rgb', '<u4'),
    ('label_id', '<u4'), ('observations', '<u4'), ('label_votes', '<u4'),
])


class VoxelSemanticMap:
    """One class vote per voxel per event, so dense scans cannot dominate a label."""

    def __init__(self, voxel_size=0.05, frame_id='world'):
        if not np.isfinite(voxel_size) or voxel_size <= 0:
            raise ValueError('voxel_size must be finite and positive')
        if not frame_id:
            raise ValueError('A nonempty world frame is required')
        self.voxel_size, self.frame_id = voxel_size, frame_id
        self.voxels = {}
        self.events = self.input_points = self.input_labeled_points = 0

    def add(self, records, frame_id):
        if frame_id != self.frame_id:
            raise ValueError(f'Cannot combine frames {frame_id!r} and {self.frame_id!r}')
        xyz = np.column_stack([records[k] for k in ('x', 'y', 'z')]).astype(float)
        finite = np.isfinite(xyz).all(axis=1)
        xyz, labels = xyz[finite], records['label_id'][finite]
        if not len(xyz):
            return
        grid = np.floor(xyz / self.voxel_size)
        if np.any(np.abs(grid) >= np.iinfo(np.int64).max):
            raise ValueError('Coordinates exceed the supported voxel grid')
        groups, inverse, counts = np.unique(
            np.column_stack([grid.astype(np.int64), labels.astype(np.int64)]),
            axis=0, return_inverse=True, return_counts=True)
        sums = np.zeros((len(groups), 3), dtype=float)
        np.add.at(sums, inverse, xyz)
        candidates = {}
        for group, count, total in zip(groups, counts, sums):
            key, label = tuple(int(x) for x in group[:3]), int(group[3])
            candidate = (label, int(count), total / count)
            current = candidates.get(key)
            # Unknown is absence of a class claim, not evidence against a semantic label.
            rank = lambda item: (item[0] != 0, item[1], -item[0])
            if current is None or rank(candidate) > rank(current):
                candidates[key] = candidate
        for key, (label, count, center) in candidates.items():
            votes = self.voxels.setdefault(key, {})
            if label not in votes:
                votes[label] = [0, np.zeros(3)]
            votes[label][0] += 1
            votes[label][1] += center
        self.events += 1
        self.input_points += len(xyz)
        self.input_labeled_points += int(np.count_nonzero(labels))

    def records(self, labels):
        result = np.empty(len(self.voxels), dtype=MAP_DTYPE)
        for index, key in enumerate(sorted(self.voxels)):
            votes = self.voxels[key]
            candidates = [label for label in votes if label != 0] or [0]
            winner = min(candidates, key=lambda label: (-votes[label][0], label))
            count, total = votes[winner]
            if winner and winner not in labels:
                raise ValueError(f'Missing class name for label {winner}')
            result[index] = (*list(total / count), label_color(labels[winner]) if winner else 0x808080,
                             winner, sum(value[0] for value in votes.values()), count)
        return result


def write_ply(path, records):
    """Binary little-endian PLY with standard RGB and explicit semantic properties."""
    dtype = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
                      ('red', 'u1'), ('green', 'u1'), ('blue', 'u1'),
                      ('label_id', '<u4'), ('observations', '<u4'), ('label_votes', '<u4')])
    body = np.empty(len(records), dtype=dtype)
    for name in ('x', 'y', 'z', 'label_id', 'observations', 'label_votes'):
        body[name] = records[name]
    for name, shift in [('red', 16), ('green', 8), ('blue', 0)]:
        body[name] = (records['rgb'] >> shift) & 255
    header = ('ply\nformat binary_little_endian 1.0\n'
              f'element vertex {len(body)}\n'
              'property float x\nproperty float y\nproperty float z\n'
              'property uchar red\nproperty uchar green\nproperty uchar blue\n'
              'property uint label_id\nproperty uint observations\nproperty uint label_votes\nend_header\n')
    with Path(path).open('wb') as output:
        output.write(header.encode('ascii'))
        output.write(body.tobytes())


def write_pcd(path, records):
    """PCD 0.7; RGB uses the packed float convention expected by PCL viewers."""
    header = ('# .PCD v0.7\nVERSION 0.7\n'
              'FIELDS x y z rgb label_id observations label_votes\n'
              'SIZE 4 4 4 4 4 4 4\nTYPE F F F F U U U\nCOUNT 1 1 1 1 1 1 1\n'
              f'WIDTH {len(records)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n'
              f'POINTS {len(records)}\nDATA binary\n')
    with Path(path).open('wb') as output:
        output.write(header.encode('ascii'))
        # The dtype is packed; the fourth field's bits are the PCL float RGB encoding.
        output.write(records.astype(MAP_DTYPE, copy=False).tobytes())


def write_preview(path, records, labels, voxel_size):
    image = np.full((1000, 1360, 3), 250, dtype=np.uint8)
    cv2.putText(image, f'Semantic map: XY / voxel {voxel_size:g}m', (25, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 1)
    if len(records):
        xy = np.column_stack([records['x'], records['y']])
        low, high = xy.min(axis=0), xy.max(axis=0)
        scale = 880 / max(float(np.max(high-low)), voxel_size)
        uv = ((xy-low) * scale).astype(int)
        # Paint known classes after unknown points so semantic surfaces stay visible.
        for index in np.argsort(records['label_id'] != 0, kind='stable'):
            x, y = int(uv[index, 0])+45, 945-int(uv[index, 1])
            color = int(records['rgb'][index])
            cv2.circle(image, (x, y), 2, (color & 255, (color >> 8) & 255, (color >> 16) & 255), -1)
        cv2.putText(image, f'X: {low[0]:.2f} .. {high[0]:.2f} m', (45, 980),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1)
        cv2.putText(image, f'Y: {low[1]:.2f} .. {high[1]:.2f} m', (980, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1)
    else:
        cv2.putText(image, 'No semantic annotations were produced', (70, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 180), 2)
    counts = Counter(int(x) for x in records['label_id'])
    for row, (label, count) in enumerate(sorted(counts.items())):
        if row >= 34:
            break
        color = label_color(labels[label]) if label else 0x808080
        y = 110 + row * 24
        cv2.rectangle(image, (980, y-12), (995, y+3),
                      (color & 255, (color >> 8) & 255, (color >> 16) & 255), -1)
        cv2.putText(image, f'{labels.get(label, "unlabeled")[:32]}: {count}', (1004, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (30, 30, 30), 1)
    if not cv2.imwrite(str(path), image):
        raise OSError(f'Could not write preview: {path}')


def export_map(directory, semantic_map, labels):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    records = semantic_map.records(labels)
    labeled = records[records['label_id'] != 0]
    for name, points in [('semantic_map', records), ('semantic_labeled', labeled)]:
        write_ply(directory / f'{name}.ply', points)
        write_pcd(directory / f'{name}.pcd', points)
    np.savez_compressed(directory / 'semantic_map.npz', points=records,
                        frame_id=semantic_map.frame_id, voxel_size=semantic_map.voxel_size)
    (directory / 'labels.json').write_text(json.dumps(
        {'0': 'unlabeled', **{str(key): value for key, value in sorted(labels.items()) if key}},
        indent=2, ensure_ascii=False) + '\n')
    write_preview(directory / 'semantic_map_xy.png', records, labels, semantic_map.voxel_size)
    return {'map_points': len(records), 'labeled_map_points': len(labeled),
            'class_point_counts': {labels.get(key, 'unlabeled'): count for key, count in
                                   sorted(Counter(int(x) for x in records['label_id']).items())}}
