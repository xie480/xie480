"""Refresh fixed public GitHub statistics cards; preserve every failed card."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
import copy
import re
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


SVG = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', SVG[1:-1])
COLORS = {
    'title_color': '9B4E66', 'text_color': '24212A', 'bg_color': 'F6F2F0',
    'border_color': 'F6F2F0', 'icon_color': 'B7778E', 'chart_color': 'B7778E',
}
SUMMARY_BASE = 'https://github-profile-summary-cards.vercel.app/api/cards/'


@dataclass(frozen=True)
class Card:
    name: str
    url: str
    expected_text: tuple[str, ...]


def summary_card(name: str, expected_text: tuple[str, ...], **extra: str) -> Card:
    query = {'username': 'xie480', 'theme': 'default', **COLORS, **extra}
    return Card(name, SUMMARY_BASE + name + '?' + urlencode(query), expected_text)


CARDS = (
    summary_card('profile-details', ('xie480', 'Contributions on GitHub', 'Public Repos')),
    summary_card('repos-per-language', ('Top Languages by Repo',)),
    summary_card('most-commit-language', ('Top Languages by Commit',)),
    summary_card('stats', ('Total Stars:', 'Total Commits:', 'Contributed to:')),
    summary_card('productive-time', ('Commits (Asia/Shanghai)',), timeZone='Asia/Shanghai'),
    Card('streak', 'https://streak-stats.demolab.com/?' + urlencode({
        'user': 'xie480', 'theme': 'default', 'background': 'F6F2F0',
        'border': 'F6F2F0', 'stroke': 'DEC7CF', 'ring': 'B7778E',
        'fire': '9B4E66', 'currStreakNum': '24212A', 'sideNums': '24212A',
        'currStreakLabel': '9B4E66', 'sideLabels': '9B4E66', 'dates': '75616A',
        'hide_border': 'true', 'disable_animations': 'true', 'timezone': 'Asia/Shanghai',
    }), ('Total Contributions', 'Current Streak', 'Longest Streak')),
)


def fetch_http(url: str) -> bytes:
    request = Request(url, headers={'User-Agent': 'Yilena-Profile-Stats/1.0',
                                    'Accept': 'image/svg+xml'})
    with urlopen(request, timeout=35) as response:
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}')
        if 'image/svg+xml' not in response.headers.get('Content-Type', '').lower():
            raise ValueError('Response is not an SVG image')
        result = response.read(2_000_001)
    return result


def validate_svg(content: bytes, card: Card) -> None:
    if not 256 <= len(content) <= 2_000_000:
        raise ValueError('Empty, incomplete, or oversized SVG')
    upper = content.upper()
    if b'<!DOCTYPE' in upper or b'<!ENTITY' in upper:
        raise ValueError('Unexpected XML entity or document type')
    root = ET.fromstring(content)
    if root.tag != SVG + 'svg':
        raise ValueError('Response root is not SVG')
    if '#f6f2f0' not in content.decode('utf-8').lower():
        raise ValueError('Response does not use the requested background palette')
    readable = ' '.join(root.itertext())
    for expected in card.expected_text:
        if expected not in readable:
            raise ValueError(f'Missing expected statistics field: {expected}')
    lower = readable.lower()
    if any(term in lower for term in ('something went wrong', 'rate limit exceeded',
                                     'error fetching', 'user not found', 'please try again')):
        raise ValueError('Response contains an error card')
    for element in root.iter():
        if element.tag in {SVG + 'script', SVG + 'foreignObject', SVG + 'iframe'}:
            raise ValueError('Unexpected active content in SVG')
        for attribute, value in element.attrib.items():
            name = attribute.split('}')[-1].lower()
            if name.startswith('on'):
                raise ValueError('Unexpected SVG event handler')
            if name == 'href' and not value.startswith('#'):
                raise ValueError('Unexpected external SVG resource')
        if element.tag == SVG + 'style' and element.text:
            css = element.text.lower()
            if '@import' in css or 'javascript:' in css or 'url(http' in css:
                raise ValueError('Unexpected external or active SVG style')


def atomic_write(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise ValueError('Refusing to replace a symlink')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.stats-', delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


GRID_NAMES = ('repos-per-language', 'most-commit-language', 'stats', 'productive-time')


def compose_mobile_profile(original: ET.Element) -> bytes:
    """Reflow the confirmed 700x200 profile schema without changing its data."""
    profile = copy.deepcopy(original)
    if profile.attrib.get('viewBox') != '0 0 700 200':
        raise ValueError('Unexpected profile viewBox; preserve previous mobile card')
    roots = [child for child in profile if child.tag == SVG + 'g' and child.attrib.get('class') == 'gpsc-root']
    if len(roots) != 1:
        raise ValueError('Unexpected profile root schema')
    children = list(roots[0])
    if len(children) != 3 or [node.tag for node in children] != [SVG + 'rect', SVG + 'text', SVG + 'g']:
        raise ValueError('Unexpected profile card structure')
    background, title, body = children
    blocks = list(body)
    if len(blocks) != 2 or any(node.tag != SVG + 'g' for node in blocks):
        raise ValueError('Unexpected profile information/chart blocks')
    information, chart = blocks
    if information.attrib.get('transform') != 'translate(30,30)' or chart.attrib.get('transform') != 'translate(295,10)':
        raise ValueError('Unexpected profile transforms')
    info_text = [node for node in information.iter() if node.tag == SVG + 'text']
    labels = [node for node in chart.iter() if node.tag == SVG + 'text' and ''.join(node.itertext()) == 'contributions in the last year']
    if len(info_text) != 4 or len(labels) != 1:
        raise ValueError('Unexpected profile information or chart label schema')
    profile.attrib.update(width='340', height='340', viewBox='0 0 340 340')
    background.attrib.update(x='0', y='0', width='340', height='340')
    title.attrib.update(x='20', y='34')
    body.attrib.pop('transform', None)
    information.attrib['transform'] = 'translate(22,63)'
    for node in info_text:
        node.attrib['style'] = node.attrib.get('style', '').replace('font-size: 14px', 'font-size: 15px')
    chart.attrib['transform'] = 'translate(40,220) scale(.72)'
    for node in chart.iter():
        if node.attrib.get('font-size') == '10':
            node.attrib['font-size'] = '14'
        if 'style' in node.attrib:
            node.attrib['style'] = node.attrib['style'].replace('font-size: 10px', 'font-size: 14px')
    labels[0].attrib.update(x='30', y='-20')
    return ET.tostring(profile, encoding='utf-8', xml_declaration=True)


def refresh_mobile_profile(output_dir: Path) -> dict[str, str]:
    try:
        source = (output_dir / 'profile-details.svg').read_bytes()
        card = next(item for item in CARDS if item.name == 'profile-details')
        validate_svg(source, card)
        content = compose_mobile_profile(ET.fromstring(source))
        target = output_dir / 'profile-mobile.svg'
        if target.is_symlink():
            raise ValueError('Refusing to replace a mobile profile symlink')
        if target.exists() and target.read_bytes() == content:
            status = 'unchanged'
        else:
            atomic_write(target, content)
            status = 'updated'
        return {'name': 'profile-mobile.svg', 'status': status, 'detail': 'Original profile data reflowed for phones'}
    except (OSError, ValueError, ET.ParseError) as error:
        return {'name': 'profile-mobile.svg', 'status': 'retained', 'detail': str(error)}


def compose_grid(cards: list[tuple[str, ET.Element]], columns: int) -> bytes:
    """Embed whole source SVGs at their native size, without recalculating data."""
    gap, card_width, card_height = 16, 340, 200
    rows = (len(cards) + columns - 1) // columns
    width = columns * card_width + (columns - 1) * gap
    height = rows * card_height + (rows - 1) * gap
    grid = ET.Element(SVG + 'svg', {
        'width': str(width), 'height': str(height), 'viewBox': f'0 0 {width} {height}',
        'role': 'img', 'aria-labelledby': 'grid-title grid-description',
    })
    ET.SubElement(grid, SVG + 'title', {'id': 'grid-title'}).text = 'Yilena GitHub statistics'
    ET.SubElement(grid, SVG + 'desc', {'id': 'grid-description'}).text = (
        'Languages by repository, languages by commit, public statistics, and hourly commits in Asia/Shanghai.'
    )
    for index, (name, original) in enumerate(cards):
        source = copy.deepcopy(original)
        prefix = name + '-'
        ids = {element.attrib['id']: prefix + element.attrib['id'] for element in source.iter() if 'id' in element.attrib}
        for element in source.iter():
            if 'id' in element.attrib:
                element.attrib['id'] = ids[element.attrib['id']]
            for attribute, value in list(element.attrib.items()):
                value = re.sub(r'url\(#([^\)]+)\)', lambda match: 'url(#' + ids.get(match[1], match[1]) + ')', value)
                if attribute.split('}')[-1] == 'href' and value.startswith('#'):
                    value = '#' + ids.get(value[1:], value[1:])
                element.attrib[attribute] = value
            if element.tag == SVG + 'style' and element.text:
                for old, new in ids.items():
                    element.text = element.text.replace('url(#' + old + ')', 'url(#' + new + ')')
        source.attrib.update(x=str((index % columns) * (card_width + gap)),
                             y=str((index // columns) * (card_height + gap)),
                             width=str(card_width), height=str(card_height))
        grid.append(source)
    return ET.tostring(grid, encoding='utf-8', xml_declaration=True)


def refresh_grids(output_dir: Path) -> list[dict[str, str]]:
    try:
        sources = []
        by_name = {card.name: card for card in CARDS}
        for name in GRID_NAMES:
            content = (output_dir / (name + '.svg')).read_bytes()
            validate_svg(content, by_name[name])
            sources.append((name, ET.fromstring(content)))
        results = []
        for filename, columns in [('grid.svg', 2), ('grid-mobile.svg', 1)]:
            content = compose_grid(sources, columns)
            target = output_dir / filename
            if target.is_symlink():
                raise ValueError('Refusing to replace a grid symlink')
            if target.exists() and target.read_bytes() == content:
                status = 'unchanged'
            else:
                atomic_write(target, content)
                status = 'updated'
            results.append({'name': filename, 'status': status, 'detail': 'Native source cards composed without changing statistics'})
        return results
    except (OSError, ValueError, ET.ParseError) as error:
        return [{'name': 'grids', 'status': 'retained', 'detail': str(error)}]


def refresh_cards(output_dir: Path, fetcher: Callable[[str], bytes] = fetch_http) -> list[dict[str, str]]:
    if output_dir.is_symlink():
        raise ValueError('Output directory must not be a symlink')
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for card in CARDS:
        target = output_dir / (card.name + '.svg')
        try:
            content = fetcher(card.url)
            validate_svg(content, card)
            if target.is_symlink():
                raise ValueError('Refusing to replace a symlink')
            if target.exists() and target.read_bytes() == content:
                status = 'unchanged'
            else:
                atomic_write(target, content)
                status = 'updated'
            results.append({'name': card.name, 'status': status, 'detail': 'Validated public statistics SVG'})
        except (OSError, ValueError, ET.ParseError) as error:
            # No write occurs until the entire HTTP response and SVG are valid.
            # Keep the previous valid image rather than publish a service error.
            results.append({'name': card.name, 'status': 'retained', 'detail': str(error)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('assets/stats'))
    args = parser.parse_args()
    results = refresh_cards(args.output_dir)
    source_ok = any(item['status'] != 'retained' for item in results)
    results.append(refresh_mobile_profile(args.output_dir))
    results.extend(refresh_grids(args.output_dir))
    lines = ['### Public profile statistics', '', '| Card | Result |', '| --- | --- |']
    for result in results:
        print(f"{result['name']}: {result['status']} — {result['detail']}")
        lines.append(f"| {result['name']} | {result['status']} |")
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as output:
            output.write('\n'.join(lines) + '\n')
    return 0 if source_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
