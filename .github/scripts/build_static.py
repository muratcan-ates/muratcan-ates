"""Build the navy profile artwork using the vendored font.

Run locally after changing the copy below:
    python3 .github/scripts/build_static.py
"""

from html import escape
from pathlib import Path

from svgtext import text, text_width

ASSETS = Path(__file__).resolve().parents[2] / "assets"

INK = "#10263F"
EDGE = "#2B4663"
PAPER = "#F3F6FB"
MUTED = "#B5C6DC"
SOFT = "#D1DFF0"
ACCENT = "#8CB9E8"
NODE = "#5D7B9D"

TECHNOLOGIES = [
    ("Development", ["Python", "FastAPI", "TypeScript", "Next.js"]),
    ("Data & AI", ["PostgreSQL", "pgvector", "scikit-learn", "MCP"]),
    ("Cloud & delivery", ["Azure", "Docker", "Bicep", "GitHub Actions"]),
]

PROJECTS = {
    "cloudsentinel": ("CloudSentinel", "Team project", "Cloud operations", "Cost & security review"),
    "dou-synapse": ("DOU-Synapse", "Graduation project", "Course assistant", "Answers from course material"),
    "istanbul-nabiz": ("İstanbul Nabız", "Internship project", "City assistant", "İstanbul open data"),
}


def frame(width, height, body, title, defs=""):
    safe_title = escape(title, quote=True)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{safe_title}">'
        f"<title>{safe_title}</title>"
        f"<defs>{defs}</defs>"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" '
        f'fill="{INK}" stroke="{EDGE}"/>'
        f"{body}</svg>\n"
    )


def rule(x, y, width, color=EDGE):
    return f'<path d="M{x} {y}h{width}" stroke="{color}" stroke-width="1"/>'


def hero_desktop():
    body = [
        text("Istanbul, Türkiye", 56, 56, 22, MUTED),
        text("Doğuş University", 1224, 56, 22, MUTED, anchor="end"),
        text("Muratcan Ateş", 50, 183, 108, PAPER, tracking=-2.8),
        rule(56, 228, 1168),
        f'<rect x="56" y="272" width="36" height="4" fill="{ACCENT}"/>',
        text("Python APIs · Applied AI · Cloud systems", 112, 286, 30, SOFT),
        text("Computer Engineering", 1224, 281, 22, PAPER, anchor="end"),
        text("Final-year student", 1224, 315, 20, MUTED, anchor="end"),
    ]
    return frame(1280, 360, "".join(body), "Muratcan Ateş — Computer Engineering student at Doğuş University, Istanbul. Python APIs, applied AI and cloud systems.")


def hero_mobile():
    body = [
        text("Istanbul · Doğuş University", 40, 60, 23, MUTED),
        text("Muratcan Ateş", 36, 174, 78, PAPER, tracking=-1.7),
        text("Computer Engineering student", 40, 233, 28, SOFT),
        rule(40, 278, 640),
        f'<rect x="40" y="324" width="28" height="4" fill="{ACCENT}"/>',
        text("Python APIs · Applied AI", 88, 339, 30, PAPER),
        text("Cloud systems", 88, 386, 30, PAPER),
    ]
    return frame(720, 430, "".join(body), "Muratcan Ateş — Computer Engineering student at Doğuş University, Istanbul. Python APIs, applied AI and cloud systems.")


def project_banner(key, mobile=False):
    name, context, category, description = PROJECTS[key]
    if mobile:
        width, height = 720, 290
        body = [
            text(context, 40, 53, 23, MUTED),
            text(name, 36, 126, 58, PAPER, tracking=-1.1),
            rule(40, 162, 640),
            text(category, 40, 210, 28, ACCENT),
            text(description, 40, 252, 26, SOFT),
        ]
    else:
        width, height = 1280, 176
        body = [
            text(context, 48, 48, 20, MUTED),
            text(name, 44, 120, 58, PAPER, tracking=-1.4),
            f'<path d="M728 40v96" stroke="{EDGE}" stroke-width="1"/>',
            text(category, 772, 78, 28, ACCENT),
            text(description, 772, 119, 24, SOFT),
        ]
    return frame(width, height, "".join(body), f"{name}: {category}. {description}.")


def toolchain(mobile=False):
    width, height = (720, 514) if mobile else (1280, 246)
    body = []
    for index, (group, items) in enumerate(TECHNOLOGIES):
        if mobile:
            top = 28 + index * 159
            if index:
                body.append(rule(40, top - 10, 640))
            body.append(text(group, 40, top + 32, 25, ACCENT))
            body.append(text(" · ".join(items[:2]), 40, top + 81, 28, PAPER))
            body.append(text(" · ".join(items[2:]), 40, top + 124, 28, PAPER))
        else:
            baseline = 58 + index * 68
            if index:
                body.append(rule(48, baseline - 39, 1184))
            body.append(text(group, 48, baseline, 23, ACCENT))
            x = 314
            for i, item in enumerate(items):
                body.append(text(item, x, baseline, 27, PAPER))
                x += text_width(item, 27) + 40
                if i != len(items) - 1:
                    body.append(f'<circle cx="{x - 20:.1f}" cy="{baseline - 8}" r="2" fill="{NODE}"/>')
    names = "; ".join(f"{group}: {', '.join(items)}" for group, items in TECHNOLOGIES)
    return frame(width, height, "".join(body), f"Technologies. {names}.")


def project_outputs():
    outputs = {}
    for key in PROJECTS:
        outputs[f"{key}-banner.svg"] = project_banner(key)
        outputs[f"{key}-banner-mobile.svg"] = project_banner(key, mobile=True)
    return outputs


def write_outputs(outputs):
    ASSETS.mkdir(exist_ok=True)
    for name, svg in outputs.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"assets/{name}: {len(svg.encode()) / 1024:.1f} KB")


def main():
    write_outputs({
        "hero.svg": hero_desktop(),
        "hero-mobile.svg": hero_mobile(),
        "toolchain.svg": toolchain(),
        "toolchain-mobile.svg": toolchain(mobile=True),
        **project_outputs(),
    })


if __name__ == "__main__":
    main()
