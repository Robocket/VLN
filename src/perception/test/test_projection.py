from types import SimpleNamespace

import numpy as np
import pytest

from vln_perception.projection import (
    Region, associate_regions, parse_regions, project_visible, rotation_matrix,
)


def test_rotation_normalizes_quaternion():
    matrix = rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=2.0, w=2.0))
    np.testing.assert_allclose(matrix @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], atol=1e-12)
    with pytest.raises(ValueError):
        rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=0.0, w=0.0))


def test_projection_rejects_behind_camera_outside_and_occluded_surfaces():
    points = np.array([[0, 0, 2], [0, 0, 4], [0, 0, -1], [20, 0, 1],
                       [float('nan'), 0, 1], [0.4, 0, 2]], dtype=float)
    image = np.zeros((8, 8, 3), np.uint8)
    k = np.array([[4.0, 0, 4], [0, 4.0, 4], [0, 0, 1.0]])
    visible, uv, depth = project_visible(points, points, image, k, np.zeros(5), '', cell_size=1)
    np.testing.assert_allclose(visible, [[0, 0, 2], [0.4, 0, 2]])
    assert len(uv) == len(depth) == 2


def test_depth_band_does_not_label_background_or_other_regions():
    points = np.array([[0, 0, 2], [0.1, 0, 2], [0.2, 0, 2], [0, 0.1, 8], [9, 9, 2]])
    uv = np.array([[4, 4], [5, 4], [4, 5], [2, 2], [9, 9]])
    labels, instances, objects = associate_regions(
        points, uv, points[:, 2], 10, 10, [Region('chair', (100, 100, 800, 800))], {})
    assert list(labels) == [1, 1, 1, 0, 0]
    assert list(instances) == [1, 1, 1, 0, 0]
    assert objects[0]['point_count'] == 3
    np.testing.assert_allclose(objects[0]['centroid'], [0.1, 0, 2])


def test_small_overlapping_box_keeps_ownership_and_label_ids_are_stable():
    points = np.array([[0, 0, 2], [1, 1, 2], [2, 2, 2]], dtype=float)
    uv = np.array([[4, 4], [5, 4], [4, 5]])
    ids = {'existing': 1}
    labels, _, objects = associate_regions(
        points, uv, points[:, 2], 10, 10,
        [Region('room', (0, 0, 1000, 1000)), Region('chair', (300, 300, 600, 600))], ids)
    assert labels.tolist() == [2, 2, 2]
    assert [x['label'] for x in objects] == ['chair']
    assert ids == {'existing': 1, 'chair': 2}


@pytest.mark.parametrize('text', [
    'the chair is over there', '{"objects":[{"label":"chair","bbox":[0,0,1]}]}',
    '{"objects":[{"label":"chair","bbox":[0,0,NaN,1000]}]}',
    '{"objects":[{"label":"chair","bbox":[0,0,1001,1000]}]}',
    '{"objects":[{"label":"chair","bbox":[5,0,1,1000]}]}',
    '{"objects":[{"label":"","bbox":[0,0,1000,1000]}]}',
])
def test_ungrounded_response_is_rejected(text):
    with pytest.raises((ValueError, TypeError)):
        parse_regions(text)


def test_normalized_json_boxes():
    assert parse_regions('```json\n{"objects":[{"label":" Chair ","bbox":[1,2,3,4]}]}\n```') == [
        Region('chair', (1.0, 2.0, 3.0, 4.0))]
