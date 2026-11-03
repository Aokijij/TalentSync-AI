"""Recover independent CV columns using page-space text boxes, including forms."""
import re
from dataclasses import dataclass

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTContainer, LTTextBox

from app.domain.services.cv_periods import read_period
from app.infrastructure.nlp.cv_sections import HEADER


@dataclass(frozen=True)
class Block:
    left: float
    bottom: float
    right: float
    top: float
    text: str


def _blocks(node):
    for child in node:
        if isinstance(child, LTTextBox):
            value = child.get_text().strip()
            if value:
                yield Block(*child.bbox, value)
        elif isinstance(child, LTContainer):
            yield from _blocks(child)


def _heading(block):
    value = " ".join(block.text.split())
    match = HEADER.fullmatch(value)
    return match.lastgroup if match else None


def _column_groups(blocks):
    # A gutter must be empty over the full region, not merely a large gap
    # between start anchors. Long duty paragraphs therefore keep their dates.
    intervals = sorted((block.left, block.right) for block in blocks)
    if not intervals:
        return [blocks]
    end = intervals[0][1]
    cuts = []
    for left, right in intervals[1:]:
        if left - end >= 12:
            cuts.append((left + end) / 2)
        end = max(end, right)
    if not cuts:
        return [blocks]
    groups = [[] for _ in range(len(cuts) + 1)]
    for block in blocks:
        groups[sum(block.left > cut for cut in cuts)].append(block)
    # A single isolated date is an aligned field, not a separate CV column.
    return groups if all(len(group) >= 2 and not all(read_period(block.text) for block in group)
                         for group in groups) else [blocks]


def _rows(blocks, *, project=False):
    rows = []
    for block in sorted(blocks, key=lambda item: (-item.top, item.left)):
        row = next((row for row in reversed(rows[-2:])
                    if abs(row[0].top - block.top) <= 3
                    and (all("\n" not in item.text for item in [*row, block])
                         or any(read_period(item.text) for item in [*row, block]))), None)
        if row is None:
            rows.append([block])
        else:
            row.append(block)
    result = []
    for row in rows:
        value = " ".join(item.text.replace("\n", " ") if len(row) > 1 else item.text
                         for item in sorted(row, key=lambda item: item.left))
        if project and not result and not _heading(row[0]) and len(value) <= 120:
            value = "Proyecto: " + value
        result.append(value)
    return "\n".join(result)


def _ordered(blocks, *, project=False):
    groups = _column_groups(blocks)
    if len(groups) > 1:
        return "\n\n".join(_ordered(group, project=project) for group in groups)
    headings = sorted((block for block in blocks if _heading(block)), key=lambda b: -b.top)
    if headings:
        # Full-width headings delimit regions before looking for local columns
        # (e.g. two project cards underneath a single employment timeline).
        regions = [[] for _ in range(len(headings) + 1)]
        for block in blocks:
            index = sum(block.top <= heading.top + .1 for heading in headings)
            regions[index].append(block)
        rendered = []
        for index, region in enumerate(regions):
            if not region:
                continue
            heading = headings[index - 1] if index else None
            body = [block for block in region if block is not heading]
            if heading:
                rendered.append(heading.text)
            rendered.append(_ordered(body, project=_heading(heading) == "projects" if heading else False)
                            if body else "")
        return "\n".join(rendered)
    return _rows(blocks, project=project)


def positioned_pages(file_path, *, max_pages):
    """Return canonical text only for pages with confident independent columns.

    pdfminer applies the complete form transformation stack. The pypdf visitor
    can expose local form coordinates instead, even outside the page bounds.
    """
    result = []
    for page in extract_pages(file_path, maxpages=max_pages, laparams=LAParams(all_texts=True)):
        blocks = list(_blocks(page))
        # Reject incomplete/unsupported geometry rather than mixing two views.
        valid = [block for block in blocks if -2 <= block.left < block.right <= page.width + 2
                 and -2 <= block.bottom < block.top <= page.height + 2]
        has_columns = len(_column_groups(valid)) > 1
        header, body = [], valid
        headings = [block for block in valid if _heading(block)]
        if headings:
            top = max(block.top for block in headings)
            header = [block for block in valid if block.bottom >= top]
            body = [block for block in valid if block not in header]
            has_columns = has_columns or len(_column_groups(body)) > 1
        text = "\n".join(filter(None, [_rows(header), _ordered(body)])) if has_columns and len(valid) >= 8 and len(valid) >= len(blocks) * .95 else ""
        result.append(re.sub(r"[ \t]+", " ", text))
    return result
