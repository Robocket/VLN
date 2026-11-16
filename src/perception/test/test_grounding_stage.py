import base64
from io import BytesIO
import sys
from types import ModuleType, SimpleNamespace

from PIL import Image

from vln_perception.gpu_worker import grounded_result


def test_silence_never_runs_grounding_or_changes_response():
    result = {'ok': True, 'response': None, 'raw': '</Silence>'}
    processor = SimpleNamespace()
    assert grounded_result(processor, {}, result, 256) == {
        'ok': True, 'response': None, 'raw': '</Silence>', 'trigger_response': None}


def test_triggered_grounding_uses_last_image_and_a_separate_instruction_context(monkeypatch):
    utils = ModuleType('vlmeval.vlm.qwen3_ovotiming.utils')
    utils.smart_video_resize = lambda **kwargs: (kwargs['height'], kwargs['width'])
    for name in ('vlmeval', 'vlmeval.vlm', 'vlmeval.vlm.qwen3_ovotiming'):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    monkeypatch.setitem(sys.modules, utils.__name__, utils)
    frames = []
    for color in ('red', 'green'):
        output = BytesIO()
        Image.new('RGB', (32, 32), color=color).save(output, 'PNG')
        frames.append({'jpeg': base64.b64encode(output.getvalue()).decode()})
    history = {'messages': ['stream history must stay untouched']}

    def infer(data, max_tokens, temperature):
        assert max_tokens == 256 and temperature == 0.0
        assert data is not history
        assert data['messages'][-1]['content'] == '<image>\nlocate objects'
        assert data['images'][0].getpixel((0, 0)) == (0, 128, 0)
        return '{"objects":[{"label":"chair","bbox":[100,100,900,900]}]}'

    processor = SimpleNamespace(factor=32, max_image_pixels=50176,
                                engine=SimpleNamespace(infer=infer),
                                session=SimpleNamespace(_data=history), generated_token_ids=[12, 34])
    result = grounded_result(processor, {'frames': frames, 'grounding_prompt': 'locate objects'},
                             {'response': 'a chair', 'raw': '</Response>a chair',
                              'source_end_ns': 123}, 256)
    assert result['trigger_response'] == 'a chair'
    assert result['raw'] == '</Response>a chair'
    assert result['source_end_ns'] == 123
    assert result['response'].startswith('{"objects":')
    assert history == {'messages': ['stream history must stay untouched']}
