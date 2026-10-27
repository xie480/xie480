"""Render portable SVG UI components. All lettering is outlined, no remote fonts."""
from pathlib import Path
from html import escape
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/ui'
OUT.mkdir(parents=True, exist_ok=True)
PALETTE = {'paper':'#F6F2F0', 'ink':'#24212A', 'rose':'#9B4E66',
           'blush':'#EAD5DD', 'muted':'#75636E', 'white':'#FFFFFF'}
CSS = '''.paper{fill:#F6F2F0}.ink{fill:#24212A}.rose{fill:#9B4E66}
.blush{fill:#EAD5DD}.muted{fill:#75636E}.white{fill:#FFFFFF}
.icon{fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}'''
(OUT / 'theme.css').write_text(CSS + '\n', encoding='utf-8')
fonts = {
    'serif': TTFont('C:/Windows/Fonts/georgia.ttf'),
    'italic': TTFont('C:/Windows/Fonts/georgiai.ttf'),
    'sans': TTFont('C:/Windows/Fonts/msyh.ttc', fontNumber=0),
    'cjk': TTFont('C:/Windows/Fonts/simsun.ttc', fontNumber=0),
}

def select(char, family):
    for key in [family, 'cjk', 'sans', 'serif']:
        font = fonts[key]
        name = font.getBestCmap().get(ord(char))
        if name:
            return font, name
    raise ValueError(f'Missing glyph: {char!r}')

def text_width(text, size, family='sans'):
    return sum(select(c, family)[0]['hmtx'][select(c, family)[1]][0] * size /
               select(c, family)[0]['head'].unitsPerEm for c in text)

def text(text, x, baseline, size, family='sans', color='ink'):
    parts = []
    for char in text:
        font, glyph_name = select(char, family)
        glyphs = font.getGlyphSet()
        pen = SVGPathPen(glyphs)
        glyphs[glyph_name].draw(pen)
        scale = size / font['head'].unitsPerEm
        if pen.getCommands():
            parts.append(f'<path class="{color}" transform="translate({x:.3f},{baseline}) scale({scale:.7f},-{scale:.7f})" d="{pen.getCommands()}"/>')
        x += font['hmtx'][glyph_name][0] * scale
    return ''.join(parts)

def svg(name, w, h, title, body):
    content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{escape(title)}</title><style>{CSS}</style>{body}</svg>'
    (OUT / name).write_text(content, encoding='utf-8')

def icon(path, x, y, color, scale=1):
    return f'<g class="icon" style="color:{color}" transform="translate({x},{y}) scale({scale})">{path}</g>'

book = '<path d="M3 4h7a4 4 0 0 1 4 4v14a4 4 0 0 0-4-4H3z"/><path d="M25 4h-7a4 4 0 0 0-4 4v14a4 4 0 0 1 4-4h7z"/>'
mail = '<rect x="2" y="5" width="25" height="19" rx="3"/><path d="m3 7 11.5 8L26 7"/>'
arrow = '<path d="M2 14 15 1M3 1h12v12"/>'

svg('blog-button.svg', 264, 68, '夢の終着駅 · Blog',
    '<rect width="264" height="68" rx="9" class="ink"/>' +
    icon(book, 19, 21, PALETTE['paper']) +
    text('夢の終着駅', 66, 31, 21, 'cjk', 'paper') +
    text('Blog & thoughts', 66, 53, 14, 'serif', 'blush') +
    icon(arrow, 229, 26, PALETTE['blush']))

svg('mail-button.svg', 264, 68, 'Write to me · yilena0505@163.com',
    '<rect width="264" height="68" rx="9" class="blush"/>' +
    icon(mail, 18, 21, PALETTE['rose']) +
    text('Write to me', 64, 31, 22, 'serif', 'ink') +
    text('yilena0505@163.com', 64, 53, 13, 'sans', 'ink') +
    icon(arrow, 231, 25, PALETTE['rose']))

def section(name, jp, en, note):
    body = '<rect width="900" height="108" rx="10" class="paper"/>'
    body += '<path d="M815 78c-31-14-28-43-7-52 20 17 26 34 7 52Z" class="blush"/>'
    body += '<path d="M818 78c17-27 42-25 49-9-20 18-36 24-49 9Z" class="blush"/>'
    body += text(jp, 32, 73, 49, 'cjk', 'rose')
    body += text(en, 160, 73, 48, 'italic', 'ink')
    svg(name, 900, 108, f'{jp} · {en}', body)

section('section-activity.svg', '足跡', 'Activity', '')
section('section-insights.svg', '観測', 'Insights', '')

line = 'また、次のコミットで。'
svg('signoff.svg', 700, 92, '桜のように、散っても美しく。また、次のコミットで。',
    '<rect width="700" height="92" rx="8" class="paper"/>' +
    text('桜のように、散っても美しく。', 135, 35, 25, 'cjk', 'rose') +
    text(line, (700-text_width(line, 29, 'cjk'))/2, 74, 29, 'cjk', 'ink'))
print('Rendered five SVG components and editable theme.css')
