from types import SimpleNamespace

import numpy as np
import pytest

from vln_perception.detector import rotation_matrix


def test_quaternion_normalization_and_rotation():
    matrix = rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=2.0, w=2.0))
    np.testing.assert_allclose(matrix @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], atol=1e-12)


@pytest.mark.parametrize('w', [0.0, float('nan')])
def test_invalid_orientation(w):
    with pytest.raises(ValueError):
        rotation_matrix(SimpleNamespace(x=0.0, y=0.0, z=0.0, w=w))
