"""Add triggered grounding to the reference worker without loading a second model.

Executed by robot-agent's model Python, not the ROS Python environment.
The reference server, streaming session, quantization and cache implementation are reused.
"""

import argparse
import base64
from io import BytesIO
from pathlib import Path
import sys
import time


def grounded_result(processor, request, result, max_tokens):
    """A separate instruction pass must not alter the active streaming question/history."""
    result['trigger_response'] = result.get('response')
    if result.get('response') is None:
        return result
    prompt = request.get('grounding_prompt')
    if not isinstance(prompt, str) or not prompt or len(prompt) > 8192:
        raise ValueError('A bounded grounding_prompt is required for semantic responses')
    from PIL import Image
    from vlmeval.vlm.qwen3_ovotiming.utils import smart_video_resize
    started = time.perf_counter()
    with Image.open(BytesIO(base64.b64decode(request['frames'][-1]['jpeg'], validate=True))) as image:
        image = image.convert('RGB')
    h, w = smart_video_resize(num_frames=1, height=image.height, width=image.width,
                              factor=processor.factor, frame_min_pixels=processor.factor ** 2,
                              frame_max_pixels=processor.max_image_pixels, force_resize=True)
    image = image.resize((w, h))
    # This is independent of processor.session._data: grounding does not pollute event memory.
    text = processor.engine.infer({
        'messages': [
            {'role': 'system', 'content': 'You are a visual grounding assistant. Output strict JSON only.'},
            {'role': 'user', 'content': '<image>\n' + prompt}],
        'images': [image],
    }, max_tokens=max_tokens, temperature=0.0)
    result['response'] = text
    result['grounding_ms'] = round((time.perf_counter() - started) * 1000, 2)
    result['grounding_tokens'] = list(processor.generated_token_ids)
    return result


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--integration-dir', required=True)
    parser.add_argument('--grounding-tokens', type=int, default=256)
    args, rest = parser.parse_known_args()
    if not 1 <= args.grounding_tokens <= 4096:
        raise ValueError('grounding-tokens must be between 1 and 4096')
    integration = Path(args.integration_dir).resolve()
    if not (integration / 'live_worker.py').is_file():
        raise ValueError(f'OneStreamer integration not found: {integration}')
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in the OneStreamer environment; restore the GPU before launching')
    sys.path.insert(0, str(integration))
    import live_worker

    class SemanticProcessor(live_worker.Processor):
        def process(self, request):
            try:
                result = super().process(request)
                return grounded_result(self, request, result, args.grounding_tokens)
            except RuntimeError as exc:
                fatal = ('unspecified launch failure', 'device-side assert', 'cuda unknown error')
                if any(marker in str(exc).casefold() for marker in fatal):
                    # The reference server catches Exception and would otherwise reuse
                    # a poisoned CUDA context for every incoming window.
                    raise SystemExit(f'Fatal CUDA context error; restore GPU and restart: {exc}') from exc
                raise

    live_worker.Processor = SemanticProcessor
    sys.argv = [str(integration / 'live_worker.py')] + rest
    live_worker.main()


if __name__ == '__main__':
    main()
