#!/usr/bin/env python3
"""Refresh <lastmod> in sitemap.xml from each page's last git commit date.

Pages with uncommitted changes get today's date. Run before committing:
    python3 scripts/update-sitemap.py
"""
import datetime
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://bastetravels.com/'
today = datetime.date.today().isoformat()


def lastmod(path):
    if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', path], cwd=ROOT).returncode:
        return today
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or today


def replace(match):
    path = match.group(1).replace(SITE, '') or 'index.html'
    return f'<loc>{match.group(1)}</loc>{match.group(2)}<lastmod>{lastmod(path)}</lastmod>'


sitemap = ROOT / 'sitemap.xml'
text = re.sub(r'<loc>([^<]+)</loc>(\s*)<lastmod>[^<]*</lastmod>', replace, sitemap.read_text())
sitemap.write_text(text)
print('sitemap.xml updated')
