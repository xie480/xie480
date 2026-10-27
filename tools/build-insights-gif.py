"""Build palette-matched looping blossom accents for README section headers."""
from math import pi, sin
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
UI = ROOT / 'assets' / 'ui'
HEADER_STEMS = ('section-insights', 'section-activity')
FRAME_COUNT = 36
FRAME_DURATION_MS = 120


def make_petal() -> Image.Image:
    """Draw one small, softly antialiased sakura petal."""
    scale = 4
    petal = Image.new('RGBA', (20 * scale, 14 * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(petal)
    silhouette = [
        (0, 8), (4, 3), (9, 0), (15, 1),
        (19, 5), (17, 9), (11, 13), (5, 14), (1, 11),
    ]
    silhouette = [(x * scale, y * scale) for x, y in silhouette]
    draw.polygon(silhouette, fill=(206, 145, 167, 255))
    return petal.resize((20, 14), Image.Resampling.LANCZOS)


def rounded_rect_mask() -> Image.Image:
    """Return the opaque part of the 900x108 rounded paper card."""
    mask = Image.new('L', (900, 108), 255)
    pixels = mask.load()
    samples = 4
    for y in range(10):
        for x in range(10):
            inside = 0
            for sy in range(samples):
                py = y + (sy + 0.5) / samples
                for sx in range(samples):
                    px = x + (sx + 0.5) / samples
                    inside += (px - 10) ** 2 + (py - 10) ** 2 <= 100
            value = 255 if inside >= samples * samples / 2 else 0
            pixels[x, y] = value
            pixels[899 - x, y] = value
            pixels[x, 107 - y] = value
            pixels[899 - x, 107 - y] = value
    return mask


def build_gif(stem: str, petal: Image.Image, opaque_shape: Image.Image,
              transparent_corners: Image.Image) -> None:
    source = UI / f'{stem}-keyframe.png'
    output = UI / f'{stem}.gif'
    base = Image.open(source).convert('RGBA')
    if base.size != (900, 108):
        raise ValueError(f'Expected a 900x108 keyframe at {source}, got {base.size}')

    # Rebuild edge pixels against the intended paper colour before making the
    # GIF corners transparent, so the card blends with light and dark themes.
    for y in range(10):
        for x in range(10):
            for px, py in ((x, y), (899 - x, y), (x, 107 - y), (899 - x, 107 - y)):
                if opaque_shape.getpixel((px, py)):
                    base.putpixel((px, py), (246, 242, 240, 255))

    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        progress = index / FRAME_COUNT
        # One petal drifts toward the blossom mark and fades away.
        x = 745 + round(48 * progress)
        y = 88 - round(40 * progress) + round(2 * sin(progress * 2 * pi))
        opacity = round(104 * sin(pi * progress) ** 1.35)
        angle = -32 + 20 * progress

        layer = petal.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        alpha = layer.getchannel('A').point(lambda value: value * opacity // 255)
        layer.putalpha(alpha)

        frame = base.copy()
        frame.alpha_composite(layer, (x, y))
        frames.append(frame.convert('RGB'))

    # Use one palette across frames to avoid colour flicker in the paper and
    # outlined text. Index 0 is reserved for the transparent rounded corners.
    palette = frames[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    palette_colors = (palette.getpalette() or [])[:765]
    gif_palette = [255, 0, 255] + palette_colors
    gif_palette.extend([0] * (768 - len(gif_palette)))
    indexed = []
    for frame in frames:
        image = frame.quantize(palette=palette, dither=Image.Dither.NONE)
        image = image.point(lambda value: value + 1)
        image.putpalette(gif_palette)
        image.paste(0, mask=transparent_corners)
        indexed.append(image)

    indexed[0].save(
        output,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        # Keep the previous frame in place between optimized partial updates,
        # so the title artwork never gets cleared while only the petal moves.
        disposal=1,
        transparency=0,
        background=0,
    )
    animation = Image.open(output)
    durations = []
    for frame_index in range(animation.n_frames):
        animation.seek(frame_index)
        durations.append(animation.info.get('duration', 0))
    print(f'Wrote {output.name}: {base.width}x{base.height}, '
          f'{animation.n_frames} frames, {sum(durations)} ms loop, '
          f'{output.stat().st_size} bytes')


def main() -> None:
    opaque_shape = rounded_rect_mask()
    transparent_corners = Image.eval(opaque_shape, lambda value: 255 - value)
    petal = make_petal()
    for stem in HEADER_STEMS:
        build_gif(stem, petal, opaque_shape, transparent_corners)


if __name__ == '__main__':
    main()
