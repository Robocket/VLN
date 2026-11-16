from types import SimpleNamespace

import pytest

from vln_navigation.goal_selector import select_index


def objects():
    return [SimpleNamespace(class_name=name, point=SimpleNamespace(x=x, y=0.0, z=0.0))
            for name, x in [('bottle', 2.0), ('chair', 3.0)]]


class Completion:
    def __init__(self, text):
        self.text = text

    def create_completion(self, **kwargs):
        assert 'distance=1.00m' in kwargs['prompt']
        return {'choices': [{'text': self.text}]}


def test_exact_class_without_model():
    assert select_index(' BOTTLE ', objects(), None) == 0


def test_natural_language_requires_model():
    with pytest.raises(ValueError, match='llm_model_path'):
        select_index('去最近的椅子', objects(), None)


@pytest.mark.parametrize('output', ['1', '<think>\n</think>\n1'])
def test_llm_selects_from_snapshot(output):
    assert select_index('选椅子', objects(), (1.0, 0.0, 0.0), Completion(output)) == 1


@pytest.mark.parametrize('output', ['物体 1 距离 3.0 米', '-1', '2', '', '0 or 1'])
def test_invalid_model_output_is_rejected(output):
    with pytest.raises(ValueError):
        select_index('选椅子', objects(), (1.0, 0.0, 0.0), Completion(output))
