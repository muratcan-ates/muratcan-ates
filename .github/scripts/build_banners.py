"""Build the project banners shown in the profile README.

CloudSentinel keeps the team's own banner. DOU-Synapse is composed from the
project's brand art. İstanbul Nabız gets a drawn banner. Needs rsvg-convert
and sips (macOS), so it runs locally only:
    python3 .github/scripts/build_banners.py <DOU-Synapse checkout> <cloudsentinel checkout>
"""

import base64
import subprocess
import sys
import tempfile
from pathlib import Path

from build_static import dot_grid
from svgtext import label, text

ASSETS = Path(__file__).resolve().parents[2] / "assets"
WIDTH = 1600


def _run(*args):
    subprocess.run(args, check=True, capture_output=True)


def _to_jpeg(source, target, width=WIDTH, quality=84):
    _run("sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
         "--resampleWidth", str(width), str(source), "--out", str(target))


def _svg_to_jpeg(svg, target):
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = Path(tmp) / "banner.svg"
        png_path = Path(tmp) / "banner.png"
        svg_path.write_text(svg, encoding="utf-8")
        _run("rsvg-convert", str(svg_path), "-o", str(png_path))
        _to_jpeg(png_path, target)


def cloudsentinel(repo):
    _to_jpeg(Path(repo) / "docs/img/banner.png", ASSETS / "cloudsentinel-banner.jpg")


def dou_synapse(repo):
    navy, gold, ivory = "#051c30", "#e6c36e", "#f3f1e8"
    height = 600
    with tempfile.TemporaryDirectory() as tmp:
        art = Path(tmp) / "hands.jpg"
        _to_jpeg(Path(repo) / "apps/web/public/brand/art/hands-dark.png", art, quality=88)
        encoded = base64.b64encode(art.read_bytes()).decode()
    art_height = round(WIDTH * 724 / 2172)
    body = [
        f'<rect width="{WIDTH}" height="{height}" fill="{navy}"/>',
        f'<image href="data:image/jpeg;base64,{encoded}" x="0" y="{height - art_height}" '
        f'width="{WIDTH}" height="{art_height}"/>',
        label("DOU-Synapse · Graduation project · Doğuş University", 80, 78, 17, ivory, opacity=0.62),
        text("Synapse", 74, 172, 92, ivory, tracking=-2),
        f'<circle cx="{80 + 350}" cy="163" r="9" fill="{gold}"/>',
        label("Cited answers · Socratic hints · Course isolation", WIDTH - 80, 78, 17, gold,
              anchor="end", opacity=0.9),
    ]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}">{"".join(body)}</svg>'
    )
    _svg_to_jpeg(svg, ASSETS / "dou-synapse-banner.jpg")


def _pulse(x0, x1, baseline, beats):
    """A heartbeat trace: flat runs with a QRS-style spike at each beat."""
    points = [(x0, baseline)]
    for x, amp in beats:
        points += [
            (x - 34, baseline), (x - 22, baseline - amp * 0.18), (x - 14, baseline),
            (x - 6, baseline + amp * 0.22), (x, baseline - amp), (x + 7, baseline + amp * 0.34),
            (x + 14, baseline), (x + 30, baseline - amp * 0.12), (x + 44, baseline),
        ]
    points.append((x1, baseline))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def istanbul_nabiz():
    ink, paper, muted, wire, pulse = "#0a0d12", "#f3f4f6", "#8b93a4", "#253041", "#f96388"
    height = 600
    baseline = 420
    sources = [("İSPARK", 150), ("İETT", 190), ("Metro", 120), ("Traffic", 170), ("Air", 110)]
    first, step = 770, 192
    beats = [(first + i * step, amp) for i, (_, amp) in enumerate(sources)]
    trace = _pulse(0, WIDTH, baseline, beats)
    body = [
        f'<rect width="{WIDTH}" height="{height}" fill="{ink}"/>',
        f'<rect width="{WIDTH}" height="{height}" fill="url(#dots)"/>',
        f'<path d="M0 {baseline}H{WIDTH}" stroke="{wire}" stroke-width="1"/>',
        f'<path d="{trace}" stroke="{pulse}" stroke-opacity="0.25" stroke-width="10" fill="none" stroke-linejoin="round"/>',
        f'<path d="{trace}" stroke="{pulse}" stroke-width="3" fill="none" stroke-linejoin="round"/>',
    ]
    for (name, amp), (x, _) in zip(sources, beats):
        peak = baseline - amp
        body.append(f'<path d="M{x} {peak - 18}V{peak - 64}" stroke="{wire}" stroke-width="1"/>')
        body.append(f'<circle cx="{x}" cy="{peak}" r="6" fill="{paper}"/>')
        body.append(label(name, x, peak - 78, 17, paper, anchor="middle"))
    body += [
        label("İstanbul Nabız · Microsoft AI Innovators 2026", 80, 78, 17, muted),
        text("Nabız", 74, 176, 104, paper, tracking=-2.5),
        text("MCP server + city agent over İstanbul's live open data", 80, 232, 26, muted),
        label("Every number carries its source and timestamp", 80, 540, 16, muted),
    ]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}"><defs>{dot_grid("dots", 24)}</defs>{"".join(body)}</svg>'
    )
    _svg_to_jpeg(svg, ASSETS / "istanbul-nabiz-banner.jpg")


def main():
    dou_repo, cloudsentinel_repo = sys.argv[1], sys.argv[2]
    ASSETS.mkdir(exist_ok=True)
    cloudsentinel(cloudsentinel_repo)
    dou_synapse(dou_repo)
    istanbul_nabiz()
    for name in ("cloudsentinel-banner.jpg", "dou-synapse-banner.jpg", "istanbul-nabiz-banner.jpg"):
        print(f"assets/{name}: {(ASSETS / name).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
