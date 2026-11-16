"""YOLOv5 adapter; heavyweight dependencies are loaded only when enabled."""

from pathlib import Path
import sys

import numpy as np


class YoloV5Backend:
    def __init__(self, repo_path, weights_path, device, confidence, iou):
        repo = Path(repo_path).expanduser()
        weights = Path(weights_path).expanduser()
        if not (repo / 'models/common.py').is_file():
            raise ValueError('Set yolov5_repo to a local YOLOv5 checkout')
        if not weights.is_file():
            raise ValueError('Set weights_path to a local YOLOv5 .pt file')
        sys.path.insert(0, str(repo.resolve()))
        import torch
        from models.common import DetectMultiBackend
        from utils.augmentations import letterbox
        from utils.general import check_img_size, non_max_suppression, scale_boxes
        from utils.torch_utils import select_device

        self.torch = torch
        self.letterbox = letterbox
        self.nms = non_max_suppression
        self.scale_boxes = scale_boxes
        self.device = select_device(device)
        self.model = DetectMultiBackend(str(weights), device=self.device, fp16=False)
        self.imgsz = check_img_size((480, 640), s=self.model.stride)
        self.confidence = confidence
        self.iou = iou
        self.model.warmup(imgsz=(1, 3, *self.imgsz))

    def detect(self, frame):
        img = self.letterbox(frame, self.imgsz, stride=self.model.stride, auto=False)[0]
        img = np.ascontiguousarray(img[:, :, ::-1].transpose(2, 0, 1))
        tensor = self.torch.from_numpy(img).to(self.device).float() / 255.0
        with self.torch.inference_mode():
            prediction = self.model(tensor.unsqueeze(0), augment=False, visualize=False)
        detections = self.nms(prediction, self.confidence, self.iou, max_det=10)
        results = []
        for det in detections:
            if len(det):
                det[:, :4] = self.scale_boxes(tensor.shape[2:], det[:, :4], frame.shape[:2]).round()
                for x1, y1, x2, y2, confidence, cls in det.cpu().tolist():
                    results.append((self.model.names[int(cls)], float(confidence),
                                    (x1, y1, x2, y2)))
        return results
