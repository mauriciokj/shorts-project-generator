#!/usr/bin/env python3
import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path
import subprocess


def probe_image(path: str) -> dict:
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'stream=codec_name,width,height:format=size',
        '-of', 'json',
        path,
    ]
    out = subprocess.check_output(cmd, text=True)
    obj = json.loads(out)
    stream = obj['streams'][0]
    return {
        'codec': stream['codec_name'],
        'width': int(stream['width']),
        'height': int(stream['height']),
        'size': int(obj['format']['size']),
    }


def get_mp3_duration_ms(path: str) -> int:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        path,
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return int(round(float(out) * 1000))


def extract_project(template_path: Path, temp_dir: Path):
    with zipfile.ZipFile(template_path, 'r') as z:
        z.extractall(temp_dir)
    for name in ["config.json", "meta.json"]:
        p = temp_dir / name
        if p.exists():
            os.chmod(p, 0o644)


def load_json(path: Path):
    with open(path, 'r') as f:
        return json.load(f)


def dump_json(path: Path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, ensure_ascii=False)


def build_project(template, audio_path, images, output_path):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        if template:
            extract_project(template, td)
        else:
            base_dir = Path(__file__).resolve().parent / 'assets' / 'template-base'
            (td / 'config.json').write_text((base_dir / 'config.json').read_text())
            (td / 'meta.json').write_text((base_dir / 'meta.json').read_text())
        config = load_json(td / 'config.json')
        meta = load_json(td / 'meta.json') if (td / 'meta.json').exists() else {}

        clips = config['data']['content']['timeline']['clips']

        # remove subtitle clips
        clips = [c for c in clips if c.get('clip', {}).get('name') != '#Subtitle_template#']
        config['data']['content']['timeline']['clips'] = clips

        audio_ms = get_mp3_duration_ms(str(audio_path))

        image_clips = []
        audio_clip = None
        music_clip = None

        for c in clips:
            clip = c.get('clip', {})
            file = clip.get('file')
            timing = c.get('timing', {})
            track = timing.get('track', {}).get('@meta_reference')
            if isinstance(file, dict) and file.get('format') == 'mp3':
                p = file.get('path', '')
                if 'short.mp3' in p or 'wiba-short.mp3' in p or 'popo-whindersson-short.mp3' in p:
                    audio_clip = c
                elif 'musicas/' in p:
                    music_clip = c
            if isinstance(file, dict) and file.get('format') in ('png', 'jpeg') and track == 5:
                image_clips.append(c)

        image_clips = sorted(image_clips, key=lambda c: c['timing']['timestamp'])

        # Prefer clips that come from the original template image set instead of any stray
        # manually inserted image from prior experiments.
        preferred = []
        for c in image_clips:
            p = c.get('clip', {}).get('file', {}).get('path', '')
            if 'cris-cyborg-wiba-images' in p:
                preferred.append(c)

        keep = (preferred[:len(images)] if len(preferred) >= len(images) else image_clips[:len(images)])
        keep_ids = {id(c) for c in keep}

        # Remove any foreign inherited image clip entirely instead of only disabling it,
        # otherwise Movavi may still try to resolve the old file path on load.
        filtered_clips = []
        for c in clips:
            clip = c.get('clip', {})
            file = clip.get('file')
            track = c.get('timing', {}).get('track', {}).get('@meta_reference')
            if isinstance(file, dict) and file.get('format') in ('png', 'jpeg') and track == 5:
                if id(c) not in keep_ids:
                    continue
            filtered_clips.append(c)
        clips = filtered_clips
        config['data']['content']['timeline']['clips'] = clips

        if audio_clip:
            f = audio_clip['clip']['file']
            f['path'] = str(audio_path)
            f['size'] = os.path.getsize(audio_path)
            f['length'] = audio_ms
            audio_clip['timing']['timestamp'] = 0
            audio_clip['timing']['duration'] = audio_ms
            audio_clip['timing']['sourceDuration'] = audio_ms
            audio_clip['clip']['sourceDuration'] = audio_ms

        if music_clip:
            music_clip['timing']['timestamp'] = 0
            music_clip['timing']['duration'] = audio_ms

        # Clean user collection so Movavi stops indexing inherited media from the template.
        allowed_paths = {str(audio_path), *[str(p) for p in images]}
        music_path = None
        if music_clip and isinstance(music_clip.get('clip', {}).get('file'), dict):
            music_path = music_clip['clip']['file'].get('path')
            if music_path:
                allowed_paths.add(music_path)

        user_collection = config.get('data', {}).get('content', {}).get('userCollection', {})
        items = user_collection.get('items')
        if isinstance(items, list):
            filtered_items = []
            for item in items:
                rp = item.get('resourcePath')
                if not rp or rp in allowed_paths:
                    filtered_items.append(item)
            user_collection['items'] = filtered_items

        base = audio_ms // len(images)
        rem = audio_ms - base * len(images)
        current = 0

        for idx, c in enumerate(keep):
            dur = base + (rem if idx == len(images) - 1 else 0)
            info = probe_image(str(images[idx]))
            c['clip']['enabled'] = True
            c['clip']['file']['path'] = str(images[idx])
            c['clip']['file']['size'] = info['size']
            c['clip']['file']['format'] = 'jpeg' if info['codec'] in ('jpeg', 'mjpeg') else info['codec']
            for vt in c['clip']['file'].get('videoTracks', []):
                if 'Media::Video' in vt:
                    vt['Media::Video']['width'] = info['width']
                    vt['Media::Video']['height'] = info['height']
                if 'Media::FileTrack' in vt:
                    vt['Media::FileTrack']['bitrate'] = info['size']
                    if info['codec'] == 'png':
                        vt['Media::FileTrack']['codecId'] = 'CODEC_ID_PNG'
                    elif info['codec'] in ('jpeg', 'mjpeg'):
                        vt['Media::FileTrack']['codecId'] = 'CODEC_ID_MJPEG'
            c['timing']['timestamp'] = current
            c['timing']['duration'] = dur
            c['timing']['sourceDuration'] = 4000
            c['timing']['sourcePosition'] = 0
            if idx == 0:
                c['timing']['transitionIn'] = 0
                c['timing']['transitionOut'] = 500
            elif idx < len(images) - 1:
                c['timing']['transitionIn'] = 500
                c['timing']['transitionOut'] = 500
            else:
                c['timing']['transitionIn'] = 500
                c['timing']['transitionOut'] = 1000
            current += dur

        dump_json(td / 'config.json', config)
        dump_json(td / 'meta.json', meta)

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.write(td / 'config.json', arcname='config.json')
            if (td / 'meta.json').exists():
                z.write(td / 'meta.json', arcname='meta.json')


def main():
    parser = argparse.ArgumentParser(description='Generate Movavi .mepj shorts project from template + mp3 + images')
    parser.add_argument('--template', required=False, default=None)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--images', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    build_project(
        Path(args.template) if args.template else None,
        Path(args.audio),
        [Path(p) for p in args.images],
        Path(args.output),
    )
    print(args.output)


if __name__ == '__main__':
    main()
