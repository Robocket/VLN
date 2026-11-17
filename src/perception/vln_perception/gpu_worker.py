"""Run the reference OneStreamer worker without changing its descriptions or token output."""

import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--integration-dir', required=True)
    args, rest = parser.parse_known_args()
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
                return super().process(request)
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
