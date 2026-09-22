"""Regenerate the "GitHub, in numbers" card from the public GitHub API.

Runs weekly in .github/workflows/refresh-profile.yml. Locally:
    GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/refresh_metrics.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from build_static import ACCENT, EDGE, MUTED, NODE, PAPER, SOFT, frame
from svgtext import label, text, text_width

LOGIN = "muratcan-ates"
API = "https://api.github.com"
ASSETS = Path(__file__).resolve().parents[2] / "assets"
BAR_COLORS = [ACCENT, PAPER, SOFT, MUTED, NODE]


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
            (f"{yearly_contributions():,}", "contributions\nin the last year"),
            (f"{authored_commits():,}", "commits in\npublic repositories"),
            (f"{merged_pull_requests():,}", "merged PRs in\nteam repositories"),
            (f"{len(projects):,}", "public project\nrepositories"),
        ],
        "languages": languages.most_common(),
    }


def _language_rows(languages, limit):
    """Top languages plus "Other", rounded so the shares add up to 100."""
    total = sum(count for _, count in languages)
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
    if "\n" in caption:
        return caption.upper().split("\n")
    words = caption.upper().split()
    lines = [words[0]]
    for word in words[1:]:
        candidate = f"{lines[-1]} {word}"
        if text_width(candidate, size, size * 0.14) <= max_width:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


def card(data, width, columns, number_size, label_size):
    pad = 48 if width > 800 else 44
    inner = width - pad * 2
    stats = data["stats"]
    col_width = inner / columns
    captions = [_wrap(caption, label_size, col_width - 40) for _, caption in stats]
    caption_lines = max(len(lines) for lines in captions)
    line_gap = label_size * 1.7
    row_height = number_size * 0.82 + label_size * 1.9 + (caption_lines - 1) * line_gap + 6
    rows = (len(stats) + columns - 1) // columns
    row_gap = 36
    top = 46
    body = []
    for i, ((value, _), lines) in enumerate(zip(stats, captions)):
        row, col = divmod(i, columns)
        x = pad + col * col_width
        y = top + row * (row_height + row_gap)
        if col:
            body.append(f'<rect x="{x - 24:.1f}" y="{y:.1f}" width="1" height="{row_height:.1f}" fill="{EDGE}"/>')
        body.append(text(value, x - 3, y + number_size * 0.82, number_size, PAPER, tracking=-1.5))
        for n, line in enumerate(lines):
            body.append(label(line, x, y + number_size * 0.82 + label_size * 1.9 + n * line_gap, label_size, MUTED))
    bar_top = top + rows * row_height + (rows - 1) * row_gap + 44
    body.append(f'<rect x="{pad}" y="{bar_top - 26}" width="{inner}" height="1" fill="{EDGE}"/>')
    body.append(label("Primary language by repository", pad, bar_top + 10, label_size, MUTED))
    languages = _language_rows(data["languages"], 4)
    x = pad
    bar_y = bar_top + 30
    for index, (_, share, _) in enumerate(languages):
        seg = inner * share
        color = BAR_COLORS[min(index, len(BAR_COLORS) - 1)]
        body.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(seg - 4, 2):.1f}" height="8" rx="2" fill="{color}"/>')
        x += seg
    lx, ly = pad, bar_y + 44
    for index, (name, _, pct) in enumerate(languages):
        caption = f"{name} {pct}%"
        item_width = 18 + text_width(caption.upper(), label_size, label_size * 0.14)
        if lx > pad and lx + item_width > pad + inner:
            lx, ly = pad, ly + label_size * 2.4
        color = BAR_COLORS[min(index, len(BAR_COLORS) - 1)]
        body.append(f'<rect x="{lx:.1f}" y="{ly - label_size * 0.78:.1f}" width="8" height="8" rx="2" fill="{color}"/>')
        body.append(label(caption, lx + 18, ly, label_size, PAPER))
        lx += item_width + 40
    height = int(ly + 42)
    summary = ", ".join(f"{value} {caption}".replace("\n", " ") for value, caption in stats)
    return frame(width, height, "".join(body), f"GitHub in numbers: {summary}")


def main():
    try:
        data = collect()
    except (urllib.error.URLError, KeyError, TypeError) as error:
        print(f"GitHub API request failed, keeping the previous card: {error}", file=sys.stderr)
        return 1
    if any(value == "0" for value, _ in data["stats"]) or not data["languages"]:
        print(f"Implausible zero in {data['stats']}, keeping the previous card", file=sys.stderr)
        return 1
    ASSETS.mkdir(exist_ok=True)
    outputs = {
        "metrics.svg": card(data, 1280, 4, 84, 18),
        "metrics-mobile.svg": card(data, 720, 2, 76, 17),
    }
    for name, svg in outputs.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
    for value, caption in data["stats"]:
        print(f"{value:>8}  {caption}".replace("\n", " "))
    print("languages:", ", ".join(f"{n} {c}" for n, c in data["languages"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
