"""Resolve production preferences into an immutable output-profile payload."""
from copy import deepcopy
import math
from pathlib import Path

from .common import CastError, read_json, root_path

DEFAULT = dict(orientation='portrait', resolution=dict(width=1080, height=1920), fps=30,
               subtitle_style=dict(font_family='Microsoft YaHei', font_size=48, color='#FFFFFF', bottom_margin_ratio=.12),
               avatar=dict(enabled=True, mode='placeholder', x=.78, y=.68, width=.14, height=.105))


def require(condition, message):
    if not condition:
        raise CastError('invalid_video_config', message)


def orientation(width, height):
    return 'square' if width == height else 'landscape' if width > height else 'portrait'


def merge(base, patch):
    result = deepcopy(base)
    for key, value in patch.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else deepcopy(value)
    return result


def fit(resolution, direction):
    short, long = sorted((resolution['width'], resolution['height']))
    if direction == 'square':
        return dict(width=short, height=short)
    require(short != long, 'Provide a nonsquare resolution when changing a square canvas to portrait or landscape.')
    return dict(width=short if direction == 'portrait' else long, height=long if direction == 'portrait' else short)


def apply(base, patch):
    require(isinstance(patch, dict) and set(patch) <= set(DEFAULT), 'Unknown or invalid video preference fields.')
    for key in ('resolution', 'subtitle_style', 'avatar'):
        if key in patch:
            require(isinstance(patch[key], dict) and set(patch[key]) <= set(DEFAULT[key]), 'Unknown or invalid video.' + key + ' fields.')
    if 'resolution' in patch:
        require(set(patch['resolution']) == {'width', 'height'}, 'Resolution requires both width and height.')
        require(all(type(patch['resolution'][k]) is int and patch['resolution'][k] > 0 and patch['resolution'][k] % 2 == 0 for k in ('width', 'height')), 'Resolution must use positive even pixel dimensions for yuv420p export.')
    if 'orientation' in patch:
        require(patch['orientation'] in ('portrait', 'landscape', 'square'), 'Orientation must be portrait, landscape or square.')
    result = merge(base, patch)
    if 'resolution' in patch and 'orientation' not in patch:
        result['orientation'] = orientation(**result['resolution'])
    elif 'orientation' in patch and 'resolution' not in patch:
        result['resolution'] = fit(result['resolution'], result['orientation'])
    require(orientation(**result['resolution']) == result['orientation'], 'Orientation conflicts with resolution; width and height are actual output dimensions.')
    require(type(result['fps']) is int and result['fps'] > 0, 'FPS must be a positive integer.')
    style, avatar = result['subtitle_style'], result['avatar']
    require(all(isinstance(style[k], str) and style[k].strip() for k in ('font_family', 'color')), 'Subtitle font/color must be nonempty strings.')
    require(type(style['font_size']) is int and style['font_size'] > 0, 'Subtitle font size must be a positive integer.')
    number = lambda v: type(v) in (int, float) and math.isfinite(v)
    require(number(style['bottom_margin_ratio']) and 0 <= style['bottom_margin_ratio'] <= 1, 'Subtitle bottom margin must be between 0 and 1.')
    require(type(avatar['enabled']) is bool and avatar['mode'] in ('placeholder', 'media'), 'Invalid avatar enabled/mode settings.')
    for key in ('x', 'y', 'width', 'height'):
        require(number(avatar[key]) and 0 <= avatar[key] <= 1 and (key in ('x', 'y') or avatar[key] > 0), 'Avatar coordinates/sizes must be valid normalized values.')
    require(avatar['x'] + avatar['width'] <= 1 and avatar['y'] + avatar['height'] <= 1, 'Avatar exceeds the output canvas.')
    return result


def profile_data(video):
    return dict(**deepcopy(video['resolution']), fps=video['fps'], subtitle_style=deepcopy(video['subtitle_style']), avatar=deepcopy(video['avatar']))


def resolve_video(directory=None, override=None, data_root=None):
    start = Path(directory or Path.cwd()).expanduser().resolve()
    if start.is_file():
        start = start.parent
    folders = (start, *start.parents)
    result, sources = deepcopy(DEFAULT), []
    for folder in folders:
        marker = folder/'cast-project.json'
        if marker.is_file():
            legacy = read_json(marker).get('defaults', {}).get('output', {})
            patch = {}
            if 'width' in legacy and 'height' in legacy:
                patch['resolution'] = dict(width=legacy['width'], height=legacy['height'])
            if 'fps' in legacy:
                patch['fps'] = legacy['fps']
            if patch:
                result = apply(result, patch)
            break
    shared = Path(data_root or root_path())/'config.json'
    paths = [shared, *[folder/'.codoop-cast/config.json' for folder in reversed(folders)]]
    for path in paths:
        if not path.is_file():
            continue
        data = read_json(path)
        if 'video' in data:
            require(data.get('schema_version') == 1, 'Unsupported video configuration version: ' + str(path))
            result = apply(result, data['video'])
            if data['video']:
                sources.append(str(path))
    if override is not None:
        result = apply(result, override)
        if override:
            sources.append('task')
    return dict(video=result, video_sources=sources, video_explicit=bool(sources))


def saved_patch(existing, patch, base=None):
    """Keep partial inheritance while normalizing a changed orientation/resolution."""
    base = base or DEFAULT
    apply(base, patch)
    require(isinstance(existing, dict), 'Saved video preferences must be an object.')
    result = merge(existing, patch)
    if 'orientation' in patch and 'resolution' not in patch and 'resolution' in result:
        result['resolution'] = fit(result['resolution'], result['orientation'])
    elif 'resolution' in patch and 'orientation' not in patch:
        result['orientation'] = orientation(**result['resolution'])
    apply(base, result)
    return result
