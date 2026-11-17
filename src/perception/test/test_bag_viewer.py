import numpy as np
import pytest

from vln_perception.bag_viewer import depth_preview


def test_millimeters_and_meters_show_the_same_depth_colors():
    millimeters = np.array([[0, 1000], [2500, 6000]], dtype=np.uint16)
    original = millimeters.copy()
    meters = millimeters.astype(np.float32)/1000
    np.testing.assert_array_equal(depth_preview(millimeters, '16UC1'), depth_preview(meters, '32FC1'))
    np.testing.assert_array_equal(millimeters, original)


def test_invalid_depth_pixels_are_black_without_modifying_source():
    source = np.array([[float('nan'), float('inf')], [-1.0, 2.0]], dtype=np.float32)
    image = depth_preview(source, '32FC1')
    assert not image[0, 0].any() and not image[0, 1].any() and not image[1, 0].any()
    assert image[1, 1].any()
    assert np.isnan(source[0, 0]) and np.isinf(source[0, 1]) and source[1, 0] == -1


@pytest.mark.parametrize('maximum', [0, -1, float('nan'), float('inf')])
def test_invalid_display_range_is_rejected(maximum):
    with pytest.raises(ValueError):
        depth_preview(np.ones((1, 1), dtype=np.uint16), '16UC1', maximum)


def test_non_depth_encodings_are_rejected():
    with pytest.raises(ValueError, match='Unsupported depth encoding'):
        depth_preview(np.ones((1, 1), dtype=np.uint8), 'rgb8')
