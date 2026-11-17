from types import SimpleNamespace

import numpy as np
import pytest

from vln_perception.projection import (
    SceneDescription, parse_scene_response, project_visible, rotation_matrix,
    scene_records, world_to_camera,
)


def result(text='A room with a blue bottle and desks.'):
    raw = '</Response>' + text
    return {'response': text, 'raw': raw,
            'tokens': {'ids': [151670, 421, 13, 151645], 'text': raw,
                       'source': 'model.generate', 'triggered': True}}


def test_rotation_normalizes_quaternion():
    matrix = rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=2.0, w=2.0))
    np.testing.assert_allclose(matrix @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], atol=1e-12)
    with pytest.raises(ValueError):
        rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=0.0, w=0.0))


def test_world_to_camera_matches_the_original_vln_extrinsic_with_a_rotated_translated_pose():
    # Original VLN: camera(.3,.2,3) -> body(3,.3,.2), then 90deg world yaw + (10,20,30).
    world = np.array([[9.7, 23.0, 30.2], [10.0, 22.0, 30.0]])
    legacy_rotation = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    q = SimpleNamespace(x=0, y=0, z=np.sqrt(0.5), w=np.sqrt(0.5))
    camera = world_to_camera(world, [10, 20, 30], q, legacy_rotation, [0, 0, 0])
    np.testing.assert_allclose(camera, [[0.3, 0.2, 3.0], [0, 0, 2.0]], atol=1e-12)


def test_projection_rejects_behind_camera_outside_and_occluded_surfaces():
    points = np.array([[0, 0, 2], [0, 0, 4], [0, 0, -1], [20, 0, 1],
                       [float('nan'), 0, 1], [0.4, 0, 2]], dtype=float)
    image = np.zeros((8, 8, 3), np.uint8)
    k = np.array([[4.0, 0, 4], [0, 4.0, 4], [0, 0, 1.0]])
    visible, uv, depth = project_visible(points, points, image, k, np.zeros(5), '', cell_size=1)
    np.testing.assert_allclose(visible, [[0, 0, 2], [0.4, 0, 2]])
    assert len(uv) == len(depth) == 2


def test_original_description_and_model_tokens_are_preserved_verbatim():
    output = result()
    description = parse_scene_response(output)
    assert description.text == output['response']
    assert list(description.token_ids) == output['tokens']['ids']
    assert description.token_text == output['raw']


@pytest.mark.parametrize('change', [
    {'response': ''}, {'response': '{"objects":[]}'}, {'tokens': {}},
    {'tokens': {'ids': [True], 'text': '</Response>abc', 'triggered': True}},
])
def test_missing_or_mismatched_scene_payloads_are_rejected(change):
    output = result()
    output.update(change)
    with pytest.raises(ValueError):
        parse_scene_response(output)


def test_all_visible_points_share_the_whole_description_not_object_specific_labels():
    snapshot = SimpleNamespace(points=np.array([[1, 2, 3], [8, 9, 10], [-1, -2, 4.0]]))
    text = 'A room containing a desk, chair and refrigerator.'
    description = SceneDescription(text, (12, 34), '</Response>'+text, 'model.generate')
    ids = {}
    records, event = scene_records(snapshot, description, ids, event_id=7)
    assert ids == {text: 1}
    assert records['label_id'].tolist() == [1, 1, 1]
    assert records['event_id'].tolist() == [7, 7, 7]
    np.testing.assert_allclose(records['z'], [3, 10, 4])
    assert event['token_ids'] == [12, 34]
    assert event['scope'] == 'all_camera_visible_points'
    assert event['point_count'] == 3
