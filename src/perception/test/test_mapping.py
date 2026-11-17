import json

import numpy as np
import pytest

from vln_perception.mapping import MAP_DTYPE, VoxelSemanticMap, export_map
from vln_perception.projection import SEMANTIC_POINT_DTYPE


def event(points, labels, event_id=1):
    records = np.zeros(len(points), dtype=SEMANTIC_POINT_DTYPE)
    records['x'], records['y'], records['z'] = np.array(points).T
    records['label_id'] = labels
    records['event_id'] = event_id
    return records


def test_negative_coordinates_use_floor_and_frames_cannot_be_mixed():
    mapper = VoxelSemanticMap(1.0, 'world')
    mapper.add(event([[-0.1, 0, 0], [0.1, 0, 0]], [1, 1]), 'world')
    assert len(mapper.voxels) == 2
    with pytest.raises(ValueError, match='Cannot combine'):
        mapper.add(event([[0, 0, 0]], [1]), 'body')


def test_unknown_never_erases_known_label_and_does_not_shift_its_center():
    mapper = VoxelSemanticMap(1.0)
    mapper.add(event([[0.1, 0.1, 0.1]], [1]), 'world')
    for i in range(3):
        mapper.add(event([[0.9, 0.9, 0.9]], [0], i+2), 'world')
    records = mapper.records({1: 'chair'})
    assert records['label_id'].tolist() == [1]
    assert records['observations'].tolist() == [4]
    assert records['label_votes'].tolist() == [1]
    assert records['x'][0] == pytest.approx(0.1)


def test_a_dense_view_gets_one_vote_and_multiple_views_choose_the_winner():
    mapper = VoxelSemanticMap(1.0)
    mapper.add(event([[0.1, 0, 0]]*100, [1]*100), 'world')
    mapper.add(event([[0.2, 0, 0]], [2], 2), 'world')
    mapper.add(event([[0.4, 0, 0]], [2], 3), 'world')
    records = mapper.records({1: 'chair', 2: 'desk'})
    assert records['label_id'].tolist() == [2]
    assert records['label_votes'].tolist() == [2]
    assert records['x'][0] == pytest.approx(0.3)


def test_one_event_prefers_a_known_class_over_unknown_and_breaks_ties_stably():
    mapper = VoxelSemanticMap(1.0)
    mapper.add(event([[0.1, 0, 0]]*9, [0]*7+[2, 1]), 'world')
    assert mapper.records({1: 'chair', 2: 'desk'})['label_id'].tolist() == [1]


@pytest.mark.parametrize('size', [0, -0.1, float('nan'), float('inf')])
def test_bad_voxel_sizes_are_rejected(size):
    with pytest.raises(ValueError):
        VoxelSemanticMap(size)


def test_exports_preserve_semantics_and_binary_color_bits(tmp_path):
    mapper = VoxelSemanticMap(0.05)
    mapper.add(event([[1, 2, 3], [4, 5, 6]], [1, 0]), 'world')
    summary = export_map(tmp_path, mapper, {1: 'chair'}, {1: {'token_ids': [7, 8]}},
                         {'completed': True, 'status': 'complete'})
    assert summary['map_points'] == 2 and summary['labeled_map_points'] == 1
    saved = np.load(tmp_path/'semantic_map.npz', allow_pickle=False)
    records = saved['points']
    assert str(saved['frame_id']) == 'world'
    assert records.dtype == MAP_DTYPE
    assert records['label_id'].tolist() == [1, 0]
    pcd = (tmp_path/'semantic_map.pcd').read_bytes()
    header, data = pcd.split(b'DATA binary\n', 1)
    assert b'TYPE F F F F U U U\n' in header and b'POINTS 2\n' in header
    np.testing.assert_array_equal(np.frombuffer(data, dtype=MAP_DTYPE), records)
    assert json.loads(str(saved['labels'])) == {'0': 'unlabeled', '1': 'chair'}
    assert json.loads(str(saved['scene_events']))['1']['token_ids'] == [7, 8]
    metadata = json.loads(str(saved['metadata']))
    assert metadata['completed'] is True and metadata['map_points'] == 2
    assert {p.name for p in tmp_path.iterdir()} == {'semantic_map.pcd', 'semantic_map.npz'}


def test_empty_map_is_an_explicit_empty_artifact(tmp_path):
    summary = export_map(tmp_path, VoxelSemanticMap(), {}, {}, {'completed': False, 'status': 'failed'})
    assert summary['map_points'] == summary['labeled_map_points'] == 0
    assert b'POINTS 0\n' in (tmp_path/'semantic_map.pcd').read_bytes()
    saved = np.load(tmp_path/'semantic_map.npz', allow_pickle=False)
    assert json.loads(str(saved['metadata']))['completed'] is False


def test_every_scene_event_link_survives_fusion_and_duplicate_events_are_idempotent(tmp_path):
    mapper = VoxelSemanticMap(1.0)
    first = event([[0.1, 0, 0]], [1], 41)
    mapper.add(first, 'world')
    mapper.add(event([[0.2, 0, 0]], [2], 42), 'world')
    mapper.add(first, 'world')
    assert mapper.events == 2
    offsets, ids = mapper.event_links()
    assert offsets.tolist() == [0, 2]
    assert ids.tolist() == [41, 42]
    events = {41: {'description': 'A desk is visible.', 'token_ids': [7, 8]},
              42: {'description': 'A room with chairs.', 'token_ids': [9, 10]}}
    export_map(tmp_path, mapper, {1: 'A desk is visible.', 2: 'A room with chairs.'}, events)
    saved = np.load(tmp_path/'semantic_map.npz', allow_pickle=False)
    assert saved['scene_event_ids'].tolist() == [41, 42]
    stored = json.loads(str(saved['scene_events']))
    assert stored['41']['token_ids'] == [7, 8]
    assert stored['42']['token_ids'] == [9, 10]
