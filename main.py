#!/usr/bin/env python3
import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path
import subprocess


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
        extract_project(template, td)
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
        keep = image_clips[:len(images)]

        for c in image_clips[len(images):]:
            c['clip']['enabled'] = False
            c['timing']['duration'] = 1

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

        base = audio_ms // len(images)
        rem = audio_ms - base * len(images)
        current = 0

        for idx, c in enumerate(keep):
            dur = base + (rem if idx == len(images) - 1 else 0)
            c['clip']['enabled'] = True
            c['clip']['file']['path'] = str(images[idx])
            c['clip']['file']['size'] = os.path.getsize(images[idx])
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
    parser.add_argument('--template', required=True)
    parser.add_argument('--audio', required=True)
    parser.add_argument('--images', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    build_project(
        Path(args.template),
        Path(args.audio),
        [Path(p) for p in args.images],
        Path(args.output),
    )
    print(args.output)


if __name__ == '__main__':
    main()
