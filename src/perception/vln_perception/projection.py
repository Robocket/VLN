"""Camera projection and conservative box-to-point semantic association."""

from dataclasses import dataclass
import hashlib
import json
import math
import re

import cv2
import numpy as np


DEFAULT_TASK = ('What objects are visible in the current image? Report the first clear view, '
                'then respond only for newly visible objects or a clear semantic scene change.')
GROUNDING_FORMAT = (
    'Locate clearly visible physical objects in this image. Output exactly one JSON object in this schema: '
    '{"objects":[{"label":"chair","bbox":[100,200,500,900]}]}. '
    'Use only evidence in this image. '
    'bbox coordinates are [left,top,right,bottom], normalized to integers from 0 to 1000 '
    'relative to that entire image. Use short object class names. '
    'Never invent objects, coordinates, or objects outside the image. '
    'If no object can be grounded, output {"objects":[]}. Do not use streaming control markers.')


def rotation_matrix(q):
    v = np.array([q.x, q.y, q.z, q.w], dtype=float)
    norm = np.linalg.norm(v)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError('Invalid rotation quaternion')
    x, y, z, w = v / norm
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ])


@dataclass(frozen=True)
class Region:
    label: str
    bbox: tuple


def parse_regions(text):
    if not isinstance(text, str) or len(text) > 65536:
        raise ValueError('Grounding response must be a bounded JSON string')
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get('objects'), list) or len(data['objects']) > 32:
        raise ValueError('Expected objects array with at most 32 grounded regions')
    result = []
    for item in data['objects']:
        if not isinstance(item, dict):
            raise ValueError('Each region must be an object')
        label, box = item.get('label'), item.get('bbox')
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            raise ValueError('Invalid semantic label')
        if not isinstance(box, list) or len(box) != 4 or any(
                isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x)
                or x < 0 or x > 1000 for x in box):
            raise ValueError('bbox must contain four finite coordinates in [0,1000]')
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError('bbox must have positive width and height')
        result.append(Region(label.strip().casefold(), tuple(float(x) for x in box)))
    return result


def project_visible(points, camera_points, image, k, distortion, model,
                    near=0.05, far=30.0, cell_size=2, occlusion_tolerance=0.1):
    """Keep finite, in-frustum points and the nearest surface per image cell."""
    height, width = image.shape[:2]
    valid = (np.isfinite(points).all(axis=1) & np.isfinite(camera_points).all(axis=1)
             & (camera_points[:, 2] >= near) & (camera_points[:, 2] <= far))
    points, camera_points = points[valid], camera_points[valid]
    if len(points) == 0:
        return points, np.empty((0, 2), dtype=int), np.empty(0)
    if model == 'equidistant':
        pixels, _ = cv2.fisheye.projectPoints(camera_points.reshape(-1, 1, 3).astype(float),
                                             np.zeros(3), np.zeros(3), k, distortion)
    elif model in ('', 'plumb_bob', 'rational_polynomial'):
        pixels, _ = cv2.projectPoints(camera_points.astype(float), np.zeros(3), np.zeros(3), k, distortion)
    else:
        raise ValueError(f'Unsupported camera distortion model: {model}')
    pixels = pixels.reshape(-1, 2)
    valid = (np.isfinite(pixels).all(axis=1) & (pixels[:, 0] >= 0) & (pixels[:, 0] < width)
             & (pixels[:, 1] >= 0) & (pixels[:, 1] < height))
    points, camera_points, uv = points[valid], camera_points[valid], pixels[valid].astype(int)
    cells_w = (width + cell_size - 1) // cell_size
    cells_h = (height + cell_size - 1) // cell_size
    cells = (uv[:, 1] // cell_size) * cells_w + uv[:, 0] // cell_size
    depth = camera_points[:, 2]
    closest = np.full(cells_w * cells_h, np.inf)
    np.minimum.at(closest, cells, depth)
    visible = depth <= closest[cells] + occlusion_tolerance
    return points[visible], uv[visible], depth[visible]


def associate_regions(points, uv, depth, width, height, regions, label_ids,
                      depth_band=0.3, min_points=3):
    """Weak labels: boxes plus a depth band, not instance segmentation masks."""
    labels = np.zeros(len(points), dtype=np.uint32)
    instances = np.zeros(len(points), dtype=np.uint32)
    annotations = []
    ordered = sorted(enumerate(regions, 1), key=lambda pair:
                     (pair[1].bbox[2]-pair[1].bbox[0]) * (pair[1].bbox[3]-pair[1].bbox[1]))
    for instance, region in ordered:
        box = np.array(region.bbox) * [width/1000, height/1000, width/1000, height/1000]
        x1, y1, x2, y2 = box
        inside = ((uv[:, 0] >= x1) & (uv[:, 0] < x2) & (uv[:, 1] >= y1)
                  & (uv[:, 1] < y2) & (instances == 0))
        cx, cy = (x1+x2)/2, (y1+y2)/2
        center = (inside & (np.abs(uv[:, 0]-cx) <= (x2-x1)*0.2)
                  & (np.abs(uv[:, 1]-cy) <= (y2-y1)*0.2))
        selected_depths = depth[center if np.any(center) else inside]
        if len(selected_depths) == 0:
            continue
        selected = inside & (np.abs(depth - np.median(selected_depths)) <= depth_band)
        if np.count_nonzero(selected) < min_points:
            continue
        if region.label not in label_ids:
            label_ids[region.label] = len(label_ids) + 1
        labels[selected] = label_ids[region.label]
        instances[selected] = instance
        annotations.append({'label': region.label, 'label_id': label_ids[region.label],
                            'instance_id': instance, 'bbox': list(region.bbox),
                            'point_count': int(np.count_nonzero(selected)),
                            'centroid': np.median(points[selected], axis=0).tolist()})
    return labels, instances, annotations


def label_color(label):
    if not label:
        return 0x808080
    digest = hashlib.sha256(label.encode()).digest()
    r, g, b = (64 + value % 192 for value in digest[:3])
    return (r << 16) | (g << 8) | b
