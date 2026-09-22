"""Build the static profile artwork: the hero banner and the toolchain card.

Run locally after changing the copy below:
    python3 .github/scripts/build_static.py
"""

import math
from pathlib import Path

from svgtext import label, text, text_width

ASSETS = Path(__file__).resolve().parents[2] / "assets"

INK = "#0b0d11"
EDGE = "#1d212b"
PAPER = "#f3f4f6"
MUTED = "#8b93a4"
SOFT = "#b9c0cc"
ACCENT = "#ff5b4a"
WIRE = "#2a303c"
NODE = "#465063"

HERO = {
    "first": "Muratcan",
    "last": "Ateş",
    "top_left": "Istanbul · Doğuş University",
    "top_right": "AI · Cloud · Agentic systems",
    "role": "Computer Engineering · AI & cloud",
    "line": "Agentic AI and cloud systems that show their evidence.",
}

TOOLCHAIN = [
    ("Build", ["Python", "FastAPI", "TypeScript", "Next.js"]),
    ("Data", ["PostgreSQL", "pgvector", "SQL ETL", "Power BI"]),
    ("AI", ["RAG", "MCP", "LLM agents", "scikit-learn"]),
    ("Cloud", ["Azure", "Bicep", "Docker", "Render"]),
    ("Verify", ["pytest", "Bun test", "Ruff", "GitHub Actions"]),
]

def _rng(seed):
    state = seed & 0xFFFFFFFF

    def next_value():
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 0x100000000

    return next_value


def synapse_graph(x0, y0, x1, y1, count, seed, min_gap):
    """Deterministic point cloud with nearest-neighbour wiring."""
    rand = _rng(seed)
    nodes = []
    attempts = 0
    while len(nodes) < count and attempts < count * 400:
        attempts += 1
        x = x0 + rand() * (x1 - x0)
        y = y0 + rand() * (y1 - y0)
        if all(math.hypot(x - a, y - b) >= min_gap for a, b in nodes):
            nodes.append((x, y))
    edges = set()
    for i, (x, y) in enumerate(nodes):
        nearest = sorted(
            (math.hypot(x - a, y - b), j) for j, (a, b) in enumerate(nodes) if j != i
        )
        for _, j in nearest[:3]:
            edges.add((min(i, j), max(i, j)))
    return nodes, sorted(edges)


def _shortest_path(nodes, edges, start, goal):
    graph = {i: [] for i in range(len(nodes))}
    for a, b in edges:
        weight = math.dist(nodes[a], nodes[b])
        graph[a].append((b, weight))
        graph[b].append((a, weight))
    best = {start: 0.0}
    previous = {}
    frontier = [(0.0, start)]
    while frontier:
        frontier.sort()
        cost, node = frontier.pop(0)
        if node == goal:
            break
        if cost > best.get(node, math.inf):
            continue
        for other, weight in graph[node]:
            candidate = cost + weight
            if candidate < best.get(other, math.inf):
                best[other] = candidate
                previous[other] = node
                frontier.append((candidate, other))
    path = [goal]
    while path[-1] != start:
        if path[-1] not in previous:
            return []
        path.append(previous[path[-1]])
    return path[::-1]


def network(box, count, seed, min_gap, fade_id):
    x0, y0, x1, y1 = box
    nodes, edges = synapse_graph(x0, y0, x1, y1, count, seed, min_gap)
    w, h = x1 - x0, y1 - y0
    start = min(range(len(nodes)), key=lambda i: math.dist(nodes[i], (x0 + w * 0.42, y0 + h * 0.52)))
    targets = [(x1, y0 + h * 0.18), (x1, y0 + h * 0.82), (x0 + w * 0.7, y0), (x0 + w * 0.12, y0 + h * 0.2)]
    signal = []
    signal_edges = set()
    for target in targets:
        goal = min(range(len(nodes)), key=lambda i: math.dist(nodes[i], target))
        route = _shortest_path(nodes, edges, start, goal)
        signal.extend(i for i in route if i not in signal)
        signal_edges.update(tuple(sorted(pair)) for pair in zip(route, route[1:]))

    def fmt(v):
        return f"{v:.1f}"

    wires = "".join(
        f"M{fmt(nodes[a][0])} {fmt(nodes[a][1])}L{fmt(nodes[b][0])} {fmt(nodes[b][1])}"
        for a, b in edges
        if (a, b) not in signal_edges
    )
    fired = "".join(
        f"M{fmt(nodes[a][0])} {fmt(nodes[a][1])}L{fmt(nodes[b][0])} {fmt(nodes[b][1])}"
        for a, b in signal_edges
    )
    rand = _rng(seed + 7)
    dots = []
    for i, (x, y) in enumerate(nodes):
        if i in signal:
            continue
        radius = 1.4 + rand() * 1.8
        dots.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{radius:.1f}"/>')
    halos = []
    sparks = []
    for i in signal:
        x, y = nodes[i]
        halos.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="9"/>')
        sparks.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="3.2"/>')
    return (
        f'<g mask="url(#{fade_id})">'
        f'<path d="{wires}" stroke="{WIRE}" stroke-width="1" fill="none"/>'
        f'<g fill="{NODE}">{"".join(dots)}</g>'
        f'<path d="{fired}" stroke="{ACCENT}" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        f'<g fill="{ACCENT}" fill-opacity="0.16">{"".join(halos)}</g>'
        f'<g fill="{ACCENT}">{"".join(sparks)}</g>'
        "</g>"
    )


def frame(width, height, body, title, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        f"<title>{title}</title>"
        f"<defs>{defs}</defs>"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="18" '
        f'fill="{INK}" stroke="{EDGE}"/>'
        f"{body}</svg>\n"
    )


def dot_grid(pattern_id, step=22):
    return (
        f'<pattern id="{pattern_id}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="1" fill="{PAPER}" fill-opacity="0.07"/></pattern>'
    )


def fade_mask(mask_id, width, height, x_from, x_to, vertical=False):
    if vertical:
        gradient = f'<linearGradient id="{mask_id}-g" x1="0" y1="{x_from}" x2="0" y2="{x_to}" gradientUnits="userSpaceOnUse">'
    else:
        gradient = f'<linearGradient id="{mask_id}-g" x1="{x_from}" y1="0" x2="{x_to}" y2="0" gradientUnits="userSpaceOnUse">'
    return (
        gradient
        + '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        + '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
        + f'<mask id="{mask_id}"><rect width="{width}" height="{height}" fill="url(#{mask_id}-g)"/></mask>'
    )


def hero_desktop():
    width, height = 1280, 480
    defs = dot_grid("dots") + fade_mask("fade", width, height, 560, 860)
    body = [
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="url(#dots)" mask="url(#fade)"/>',
        network((680, 116, 1232, 420), 50, 20260922, 42, "fade"),
        label(HERO["top_left"], 64, 76, 18, MUTED),
        label(HERO["top_right"], width - 64, 76, 18, MUTED, anchor="end"),
        text(HERO["first"], 56, 226, 136, PAPER, tracking=-2.5),
        text(HERO["last"], 56, 352, 136, PAPER, tracking=-2.5),
        f'<rect x="64" y="393" width="32" height="3" fill="{ACCENT}"/>',
        label(HERO["role"], 112, 401, 18, PAPER),
        text(HERO["line"], 64, 444, 26, SOFT),
    ]
    return frame(width, height, "".join(body), "Muratcan Ateş, AI and cloud builder", defs)


def hero_mobile():
    width, height = 720, 820
    defs = dot_grid("dots") + fade_mask("fade", width, height, 440, 260, vertical=True)
    body = [
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="17" fill="url(#dots)" mask="url(#fade)"/>',
        network((48, 118, 672, 400), 38, 20260922, 48, "fade"),
        label(HERO["top_left"], 48, 72, 18, MUTED),
        text(HERO["first"], 42, 540, 146, PAPER, tracking=-3),
        text(HERO["last"], 42, 672, 146, PAPER, tracking=-3),
        f'<rect x="48" y="716" width="32" height="3" fill="{ACCENT}"/>',
        label(HERO["role"], 96, 724, 18, PAPER),
        text("Agentic AI and cloud systems", 48, 766, 26, SOFT),
        text("that show their evidence.", 48, 800, 26, SOFT),
    ]
    return frame(width, height, "".join(body), "Muratcan Ateş, AI and cloud builder", defs)


def toolchain(columns, width, row_height, first_col, title_size, item_size):
    rows = len(TOOLCHAIN)
    pad_top = 36
    height = pad_top * 2 + rows * row_height
    body = []
    col_width = (width - first_col - 48) / columns
    for r, (group, items) in enumerate(TOOLCHAIN):
        top = pad_top + r * row_height
        mid = top + row_height / 2
        if r:
            body.append(f'<rect x="48" y="{top:.1f}" width="{width - 96}" height="1" fill="{EDGE}"/>')
        body.append(label(group, 48, mid + title_size * 0.36, title_size, MUTED))
        per_row = columns
        for i, item in enumerate(items):
            line = i // per_row
            col = i % per_row
            lines = math.ceil(len(items) / per_row)
            y = mid + item_size * 0.36 + (line - (lines - 1) / 2) * item_size * 1.9
            x = first_col + col * col_width
            body.append(f'<rect x="{x:.1f}" y="{y - item_size * 0.42:.1f}" width="6" height="6" rx="1" fill="{ACCENT}"/>')
            body.append(text(item, x + 18, y + item_size * 0.08, item_size, PAPER))
    names = ", ".join(item for _, items in TOOLCHAIN for item in items)
    return frame(width, height, "".join(body), f"Toolchain: {names}")


def main():
    ASSETS.mkdir(exist_ok=True)
    outputs = {
        "hero.svg": hero_desktop(),
        "hero-mobile.svg": hero_mobile(),
        "toolchain.svg": toolchain(4, 1280, 84, 250, 18, 25),
        "toolchain-mobile.svg": toolchain(2, 720, 112, 190, 16, 24),
    }
    for name, svg in outputs.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"assets/{name}: {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
