"""Regenerate the GitHub activity card from the public GitHub API.

Runs weekly in .github/workflows/refresh-profile.yml. Locally:
    GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/refresh_metrics.py
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from build_static import ACCENT, EDGE, MUTED, NODE, PAPER, SOFT, frame
from svgtext import text, text_width

LOGIN = "muratcan-ates"
API = "https://api.github.com"
ASSETS = Path(__file__).resolve().parents[2] / "assets"
BAR_COLORS = [ACCENT, PAPER, SOFT, MUTED, NODE]
CAPTIONS = [
    "Contributions\npast 12 months",
    "Commits\npublic repositories",
    "Merged pull requests\npublic repositories",
    "Project repositories\npublic, owned",
]
SNAPSHOT = ASSETS / "metrics-data.json"


def _request(url, body=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{LOGIN}-profile-metrics",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def owned_public_repos():
    repos = []
    page = 1
    while True:
        batch = _request(f"{API}/users/{LOGIN}/repos?type=owner&per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


# "is:public" keeps the card identical whichever token runs it: a personal
# token would otherwise also count work in private repositories.
def merged_pull_requests():
    query = f"author:{LOGIN}+is:pr+is:merged+is:public"
    return _request(f"{API}/search/issues?q={query}&per_page=1")["total_count"]


def authored_commits():
    """Commits on default branches of public repositories, as indexed by search."""
    return _request(f"{API}/search/commits?q=author:{LOGIN}+is:public&per_page=1")["total_count"]


def yearly_contributions():
    query = (
        "query($login: String!) { user(login: $login) { contributionsCollection "
        "{ contributionCalendar { totalContributions } } } }"
    )
    result = _request(f"{API}/graphql", {"query": query, "variables": {"login": LOGIN}})
    collection = result["data"]["user"]["contributionsCollection"]
    return collection["contributionCalendar"]["totalContributions"]


def collect():
    # Project repositories only: no forks, no archives, not this profile
    # repository and nothing that is still an empty placeholder.
    projects = [
        r for r in owned_public_repos()
        if not (r["private"] or r["fork"] or r["archived"])
        and r["name"] != LOGIN and r["size"] > 1
    ]
    languages = Counter(r["language"] for r in projects if r["language"])
    return {
        "stats": [
            (f"{yearly_contributions():,}", CAPTIONS[0]),
            (f"{authored_commits():,}", CAPTIONS[1]),
            (f"{merged_pull_requests():,}", CAPTIONS[2]),
            (f"{len(projects):,}", CAPTIONS[3]),
        ],
        "languages": languages.most_common(),
    }


def _language_rows(languages, limit):
    """Top languages plus "Other", rounded so the shares add up to 100."""
    languages = [(name, count) for name, count in languages if count > 0]
    total = sum(count for _, count in languages)
    if not total:
        return []
    top = languages[:limit]
    rest = total - sum(count for _, count in top)
    rows = [(name, count) for name, count in top] + ([("Other", rest)] if rest else [])
    exact = [count * 100 / total for _, count in rows]
    whole = [int(value) for value in exact]
    order = sorted(range(len(rows)), key=lambda i: exact[i] - whole[i], reverse=True)
    for i in order[: 100 - sum(whole)]:
        whole[i] += 1
    return [(name, count / total, pct) for (name, count), pct in zip(rows, whole)]


def _wrap(caption, size, max_width):
    lines = []
    for paragraph in caption.split("\n"):
        words = paragraph.split()
        if not words:
            continue
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if text_width(candidate, size) <= max_width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def card(data, width, columns, number_size, label_size):
    pad = 40 if width > 800 else 36
    inner = width - pad * 2
    stats = data["stats"]
    col_width = inner / columns
    captions = [_wrap(caption, label_size, col_width - 32) for _, caption in stats]
    caption_lines = max((len(lines) for lines in captions), default=0)
    line_gap = label_size * 1.35
    row_height = number_size * 0.82 + 28 + max(caption_lines - 1, 0) * line_gap
    rows = (len(stats) + columns - 1) // columns
    row_gap = 28
    top = 28
    body = []
    for i, ((value, _), lines) in enumerate(zip(stats, captions)):
        row, col = divmod(i, columns)
        x = pad + col * col_width
        y = top + row * (row_height + row_gap)
        if col:
            body.append(f'<rect x="{x - 16:.1f}" y="{y:.1f}" width="1" height="{row_height:.1f}" fill="{EDGE}"/>')
        body.append(text(value, x - 2, y + number_size * 0.82, number_size, PAPER, tracking=-1.2))
        for n, line in enumerate(lines):
            color = PAPER if n == 0 else MUTED
            body.append(text(line, x, y + number_size * 0.82 + 28 + n * line_gap, label_size, color))
    bar_top = top + rows * row_height + max(rows - 1, 0) * row_gap + 32
    body.append(f'<rect x="{pad}" y="{bar_top - 12:.1f}" width="{inner}" height="1" fill="{EDGE}"/>')
    body.append(text("Primary language by repository", pad, bar_top + 20, label_size, MUTED))
    languages = _language_rows(data["languages"], 4)
    if not languages:
        body.append(text("No language data available", pad, bar_top + 52, label_size, SOFT))
        summary = ", ".join(f"{value} {caption}".replace("\n", " ") for value, caption in stats)
        return frame(width, int(bar_top + 82), "".join(body), f"GitHub in numbers: {summary}")
    x = pad
    bar_y = bar_top + 36
    for index, (_, share, _) in enumerate(languages):
        seg = inner * share
        color = BAR_COLORS[min(index, len(BAR_COLORS) - 1)]
        gap = min(3, seg / 4) if index < len(languages) - 1 else 0
        body.append(f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{seg - gap:.1f}" height="6" rx="1" fill="{color}"/>')
        x += seg
    lx, ly = pad, bar_y + 34
    for index, (name, _, pct) in enumerate(languages):
        caption = f"{name} {pct}%"
        item_width = 16 + text_width(caption, label_size)
        if lx > pad and lx + item_width > pad + inner:
            lx, ly = pad, ly + label_size * 1.8
        color = BAR_COLORS[min(index, len(BAR_COLORS) - 1)]
        body.append(f'<rect x="{lx:.1f}" y="{ly - label_size * 0.54:.1f}" width="6" height="6" rx="1" fill="{color}"/>')
        body.append(text(caption, lx + 16, ly, label_size, PAPER))
        lx += item_width + 30
    height = int(ly + 30)
    summary = ", ".join(f"{value} {caption}".replace("\n", " ") for value, caption in stats)
    return frame(width, height, "".join(body), f"GitHub in numbers: {summary}")


def existing_snapshot():
    """Read saved values, without treating a redesign as a new API refresh."""
    svg = ET.parse(ASSETS / "metrics.svg")
    title = svg.getroot().find("{http://www.w3.org/2000/svg}title")
    if title is None or not title.text:
        raise ValueError("The existing numbers card has no readable title")
    patterns = [
        r"([\d,]+)\s+contributions\b",
        r"([\d,]+)\s+(?:commits|public commits)\b",
        r"([\d,]+)\s+merged (?:PRs|pull requests)\b",
        r"([\d,]+)\s+(?:public project repositories|project repositories)\b",
    ]
    values = []
    for pattern in patterns:
        match = re.search(pattern, title.text, re.IGNORECASE)
        if match is None:
            raise ValueError("Cannot recover all four values from the existing card")
        values.append(f"{int(match.group(1).replace(',', '')):,}")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return {"stats": list(zip(values, CAPTIONS)), "languages": snapshot["languages"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-existing", action="store_true",
        help="Re-render saved values and language counts without requesting GitHub data",
    )
    args = parser.parse_args(argv)
    try:
        data = existing_snapshot() if args.render_existing else collect()
    except (urllib.error.URLError, KeyError, TypeError, ValueError, OSError, ET.ParseError) as error:
        operation = "Saved snapshot rendering" if args.render_existing else "GitHub API request"
        print(f"{operation} failed, keeping the previous card: {error}", file=sys.stderr)
        return 1
    if any(value == "0" for value, _ in data["stats"]):
        print(f"Implausible zero in {data['stats']}, keeping the previous card", file=sys.stderr)
        return 1
    ASSETS.mkdir(exist_ok=True)
    outputs = {
        "metrics.svg": card(data, 1280, 4, 56, 19),
        "metrics-mobile.svg": card(data, 720, 2, 72, 25),
    }
    for name, svg in outputs.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
    SNAPSHOT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.render_existing:
        print("Re-rendered the existing snapshot; no GitHub requests made.")
    for value, caption in data["stats"]:
        print(f"{value:>8}  {caption}".replace("\n", " "))
    print("languages:", ", ".join(f"{n} {c}" for n, c in data["languages"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
