import json

import numpy as np
import pytest

from vln_perception.mapping import MAP_DTYPE, VoxelSemanticMap, export_map
from vln_perception.projection import SEMANTIC_POINT_DTYPE


def event(points, labels):
    records = np.zeros(len(points), dtype=SEMANTIC_POINT_DTYPE)
    records['x'], records['y'], records['z'] = np.array(points).T
    records['label_id'] = labels
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
    for _ in range(3):
        mapper.add(event([[0.9, 0.9, 0.9]], [0]), 'world')
    records = mapper.records({1: 'chair'})
    assert records['label_id'].tolist() == [1]
    assert records['observations'].tolist() == [4]
    assert records['label_votes'].tolist() == [1]
    assert records['x'][0] == pytest.approx(0.1)


def test_a_dense_view_gets_one_vote_and_multiple_views_choose_the_winner():
    mapper = VoxelSemanticMap(1.0)
    mapper.add(event([[0.1, 0, 0]]*100, [1]*100), 'world')
    mapper.add(event([[0.2, 0, 0]], [2]), 'world')
    mapper.add(event([[0.4, 0, 0]], [2]), 'world')
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
    summary = export_map(tmp_path, mapper, {1: 'chair'})
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
    ply = (tmp_path/'semantic_map.ply').read_bytes()
    header, data = ply.split(b'end_header\n', 1)
    assert b'format binary_little_endian 1.0\n' in header
    assert b'element vertex 2\n' in header
    assert len(data) == 2*(3*4+3+3*4)
    assert json.loads((tmp_path/'labels.json').read_text()) == {'0': 'unlabeled', '1': 'chair'}
    assert (tmp_path/'semantic_map_xy.png').is_file()


def test_empty_map_is_an_explicit_empty_artifact(tmp_path):
    summary = export_map(tmp_path, VoxelSemanticMap(), {})
    assert summary['map_points'] == summary['labeled_map_points'] == 0
    assert b'element vertex 0\n' in (tmp_path/'semantic_map.ply').read_bytes()
