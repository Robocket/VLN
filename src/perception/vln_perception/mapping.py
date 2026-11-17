"""World-frame voxel fusion preserving every associated scene description event."""

import json
from pathlib import Path

import numpy as np

from .projection import label_color


MAP_DTYPE = np.dtype([
    ('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('rgb', '<u4'),
    ('label_id', '<u4'), ('observations', '<u4'), ('label_votes', '<u4'),
])


class VoxelSemanticMap:
    """Retain all scene events; select a primary label for display by event votes."""

    def __init__(self, voxel_size=0.05, frame_id='world'):
        if not np.isfinite(voxel_size) or voxel_size <= 0:
            raise ValueError('voxel_size must be finite and positive')
        if not frame_id:
            raise ValueError('A nonempty world frame is required')
        self.voxel_size, self.frame_id = voxel_size, frame_id
        self.voxels = {}
        self.voxel_events = {}
        self.seen_events = set()
        self.events = self.input_points = self.input_labeled_points = 0

    def add(self, records, frame_id):
        if frame_id != self.frame_id:
            raise ValueError(f'Cannot combine frames {frame_id!r} and {self.frame_id!r}')
        event_ids = np.unique(records['event_id'])
        if not len(records):
            return
        if len(event_ids) != 1 or int(event_ids[0]) <= 0:
            raise ValueError('Each cloud must have one positive scene event_id')
        event_id = int(event_ids[0])
        if event_id in self.seen_events:
            return
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
            self.voxel_events.setdefault(key, set()).add(event_id)
            votes = self.voxels.setdefault(key, {})
            if label not in votes:
                votes[label] = [0, np.zeros(3)]
            votes[label][0] += 1
            votes[label][1] += center
        self.seen_events.add(event_id)
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
                raise ValueError(f'Missing scene description for label {winner}')
            result[index] = (*list(total / count), label_color(labels[winner]) if winner else 0x808080,
                             winner, sum(value[0] for value in votes.values()), count)
        return result

    def event_links(self):
        """CSR arrays align with records(); event metadata retains the exact token IDs."""
        offsets, event_ids = [0], []
        for key in sorted(self.voxels):
            event_ids.extend(sorted(self.voxel_events[key]))
            offsets.append(len(event_ids))
        return np.array(offsets, dtype=np.uint64), np.array(event_ids, dtype=np.uint32)


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


def export_map(directory, semantic_map, labels, scene_events, metadata=None):
    """Save a viewable PCD and readable JSON with exact scene token links."""
    records = semantic_map.records(labels)
    offsets, event_ids = semantic_map.event_links()
    if set(int(x) for x in event_ids) - set(scene_events):
        raise ValueError('Map contains scene event IDs without token metadata')
    summary = {'map_points': len(records),
               'labeled_map_points': int(np.count_nonzero(records['label_id'])),
               'scene_event_links': len(event_ids)}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    write_pcd(directory / 'semantic_map.pcd', records)
    payload = {
        'point_cloud_file': 'semantic_map.pcd',
        'frame_id': semantic_map.frame_id,
        'voxel_size': semantic_map.voxel_size,
        'labels': {'0': 'unlabeled', **{str(key): value for key, value in sorted(labels.items()) if key}},
        'scene_events': {str(key): value for key, value in sorted(scene_events.items())},
        # Entry i refers to point i in the PCD, including all overlapping scene events.
        'point_event_ids': [event_ids[int(start):int(end)].tolist()
                            for start, end in zip(offsets[:-1], offsets[1:])],
        'metadata': {**(metadata or {}), **summary},
    }
    (directory / 'semantic_map.json').write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    return summary
