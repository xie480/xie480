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
.shadow-dark{fill:#493943}.shadow-rose{fill:#CDA6B5}
.panel-dark{fill:#302832}.panel-paper{fill:#F6F2F0}
.arrow-dark{fill:#302832;stroke:#806B77}.arrow-paper{fill:#F6F2F0;stroke:#D0A9B7}
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

def text(text, x, baseline, size, family='sans', color='ink', tracking=0):
    parts = []
    for char in text:
        font, glyph_name = select(char, family)
        glyphs = font.getGlyphSet()
        pen = SVGPathPen(glyphs)
        glyphs[glyph_name].draw(pen)
        scale = size / font['head'].unitsPerEm
        if pen.getCommands():
            parts.append(f'<path class="{color}" transform="translate({x:.3f},{baseline}) scale({scale:.7f},-{scale:.7f})" d="{pen.getCommands()}"/>')
        x += font['hmtx'][glyph_name][0] * scale + tracking
    return ''.join(parts)

def svg(name, w, h, title, body):
    content = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>{escape(title)}</title><style>{CSS}</style>{body}</svg>'
    (OUT / name).write_text(content, encoding='utf-8')

def icon(path, x, y, color, scale=1):
    return f'<g class="icon" style="color:{color}" transform="translate({x},{y}) scale({scale})">{path}</g>'

book = '<path d="M3 4h7a4 4 0 0 1 4 4v14a4 4 0 0 0-4-4H3z"/><path d="M25 4h-7a4 4 0 0 0-4 4v14a4 4 0 0 1 4-4h7z"/>'
mail = '<rect x="2" y="5" width="25" height="19" rx="3"/><path d="m3 7 11.5 8L26 7"/>'
arrow = '<path d="M2 14 15 1M3 1h12v12"/>'

blog_button = (
    '<rect x="1" y="4" width="262" height="63" rx="10" class="shadow-dark"/>'
    '<rect width="264" height="64" rx="10" class="ink"/>'
    '<rect x="0.75" y="0.75" width="262.5" height="62.5" rx="9.5" fill="none" stroke="#76616D" stroke-width="0.8"/>'
    '<path d="M12 2.5H252" stroke="#9B4E66" stroke-width="1.2" opacity="0.78"/>'
    '<rect x="12" y="11" width="41" height="42" rx="8" class="panel-dark"/>'
    '<rect x="12.5" y="11.5" width="40" height="41" rx="7.5" fill="none" stroke="#66515E" stroke-width="0.7"/>'
    '<path d="M63 14V50" stroke="#6C5864" stroke-width="0.8"/>'
    '<circle cx="239" cy="32" r="11" class="arrow-dark" stroke-width="0.8"/>'
    '<path d="M231 18H241" stroke="#9B4E66" stroke-width="1.4" stroke-linecap="round"/>'
    + icon(book, 19, 20, PALETTE['paper'], 0.92)
    + text('JOURNAL · 01', 73, 16, 7, 'sans', 'rose', tracking=0.65)
    + text('夢の終着駅', 73, 35, 19, 'cjk', 'paper')
    + text('Blog & thoughts', 73, 53, 13, 'serif', 'blush')
    + icon(arrow, 232, 25, PALETTE['blush'], 0.9)
)
svg('blog-button.svg', 264, 68, '夢の終着駅 · Blog', blog_button)

mail_button = (
    '<rect x="1" y="4" width="262" height="63" rx="10" class="shadow-rose"/>'
    '<rect width="264" height="64" rx="10" class="blush"/>'
    '<rect x="0.75" y="0.75" width="262.5" height="62.5" rx="9.5" fill="none" stroke="#C89EAE" stroke-width="0.8"/>'
    '<path d="M12 2.5H252" stroke="#FFFFFF" stroke-width="1.2" opacity="0.86"/>'
    '<rect x="12" y="11" width="41" height="42" rx="8" class="panel-paper"/>'
    '<rect x="12.5" y="11.5" width="40" height="41" rx="7.5" fill="none" stroke="#D6BAC4" stroke-width="0.7"/>'
    '<path d="M63 14V50" stroke="#D1AEBB" stroke-width="0.8"/>'
    '<circle cx="239" cy="32" r="11" class="arrow-paper" stroke-width="0.8"/>'
    '<path d="M231 18H241" stroke="#FFFFFF" stroke-width="1.4" stroke-linecap="round"/>'
    + icon(mail, 18, 20, PALETTE['rose'], 0.92)
    + text('CONTACT · 02', 73, 16, 7, 'sans', 'rose', tracking=0.55)
    + text('Write to me', 73, 35, 18, 'serif', 'ink')
    + text('yilena0505@163.com', 73, 53, 12, 'sans', 'muted')
    + icon(arrow, 232, 25, PALETTE['rose'], 0.9)
)
svg('mail-button.svg', 264, 68, 'Write to me · yilena0505@163.com', mail_button)

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
