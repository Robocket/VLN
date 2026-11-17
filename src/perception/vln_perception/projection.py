"""Camera projection and scene-description labels for complete visible point clouds."""

from copy import deepcopy
from dataclasses import dataclass
import hashlib

import cv2
import numpy as np


SEMANTIC_POINT_DTYPE = np.dtype([
    ('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('rgb', '<u4'),
    ('label_id', '<u4'), ('event_id', '<u4'),
])


DEFAULT_TASK = ('What objects are visible in the current image? Report the first clear view, '
                'then respond only for newly visible objects or a clear semantic scene change.')


@dataclass(frozen=True)
class SceneDescription:
    text: str
    token_ids: tuple
    token_text: str
    token_source: str


def parse_scene_response(result):
    text, raw, tokens = result.get('response'), result.get('raw'), result.get('tokens')
    if not isinstance(text, str) or not text.strip() or len(text) > 65536:
        raise ValueError('A nonempty bounded scene description is required')
    if not isinstance(raw, str) or '</Response>' not in raw or raw.split('</Response>', 1)[1].strip() != text:
        raise ValueError('Scene text does not match the original proactive Response')
    if not isinstance(tokens, dict) or tokens.get('text') != raw or tokens.get('triggered') is not True:
        raise ValueError('Scene label requires the original triggered model token payload')
    ids = tokens.get('ids')
    if not isinstance(ids, list) or not ids or len(ids) > 4096 or any(type(x) is not int or x < 0 for x in ids):
        raise ValueError('Scene token IDs must be a nonempty list of nonnegative integers')
    return SceneDescription(text, tuple(ids), raw, str(tokens.get('source', 'model.generate')))


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


def world_to_camera(points, position, orientation, camera_to_body_rotation, camera_to_body_translation):
    """Inverse of VLN's original p_world = R_odom @ (R_cb @ p_camera + t_cb) + t_odom."""
    body = (points - np.asarray(position)) @ rotation_matrix(orientation)
    return (body - np.asarray(camera_to_body_translation)) @ np.asarray(camera_to_body_rotation).reshape(3, 3)


def camera_viewpoint(position, camera_to_world_rotation):
    """World pose of the projection camera: optical X right, Y down, Z forward."""
    rotation = np.asarray(camera_to_world_rotation, dtype=float).reshape(3, 3)
    quaternion = np.empty(4)
    trace = np.trace(rotation)
    if trace > 0:
        scale = 2 * np.sqrt(1 + trace)
        quaternion[:3] = [rotation[2, 1]-rotation[1, 2], rotation[0, 2]-rotation[2, 0],
                          rotation[1, 0]-rotation[0, 1]]
        quaternion[:3] /= scale
        quaternion[3] = scale / 4
    else:
        i = int(np.argmax(np.diag(rotation)))
        j, k = (i+1) % 3, (i+2) % 3
        scale = 2 * np.sqrt(1 + rotation[i, i] - rotation[j, j] - rotation[k, k])
        quaternion[i] = scale / 4
        quaternion[j] = (rotation[j, i]+rotation[i, j]) / scale
        quaternion[k] = (rotation[k, i]+rotation[i, k]) / scale
        quaternion[3] = (rotation[k, j]-rotation[j, k]) / scale
    quaternion /= np.linalg.norm(quaternion)
    if quaternion[3] < 0:
        quaternion *= -1
    return {'position': np.asarray(position, dtype=float).tolist(),
            'orientation_xyzw': quaternion.tolist(),
            'forward': rotation[:, 2].tolist(), 'up': (-rotation[:, 1]).tolist()}


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


def label_color(label):
    if not label:
        return 0x808080
    digest = hashlib.sha256(label.encode()).digest()
    r, g, b = (64 + value % 192 for value in digest[:3])
    return (r << 16) | (g << 8) | b


def scene_records(snapshot, description, label_ids, event_id):
    """Every camera-visible point receives the same complete scene description."""
    if description.text not in label_ids:
        label_ids[description.text] = len(label_ids) + 1
    label_id = label_ids[description.text]
    records = np.empty(len(snapshot.points), dtype=SEMANTIC_POINT_DTYPE)
    records['x'], records['y'], records['z'] = snapshot.points.T
    records['label_id'] = label_id
    records['event_id'] = event_id
    records['rgb'] = label_color(description.text)
    event = {'event_id': event_id, 'label_id': label_id, 'description': description.text,
             'token_ids': list(description.token_ids), 'token_text': description.token_text,
             'token_source': description.token_source, 'point_count': len(records),
             'centroid': np.median(snapshot.points, axis=0).tolist() if len(records) else None,
             'scope': 'all_camera_visible_points', 'viewpoint': deepcopy(snapshot.viewpoint)}
    return records, event
