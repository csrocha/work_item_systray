# -*- coding: utf-8 -*-
"""Utilidades compartidas por los proveedores de work_item_systray
(work_item_task, work_item_helpdesk, work_item_enterprise_task)."""
import re
from html import unescape

_TAG_RE = re.compile(r'<[^>]+>')
_SPACE_RE = re.compile(r'\s+')


def html_to_text(html_value, max_len=280):
    if not html_value:
        return ''
    text = unescape(_TAG_RE.sub(' ', html_value))
    text = _SPACE_RE.sub(' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + '…'
    return text
