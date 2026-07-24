"""Build Figure 1 deterministically from the locked manuscript wording.

Outputs SVG, PDF, EPS (when Inkscape is available), and a 1000-dpi PNG at
190-mm final width. The figure has no internal title; the caption belongs in
the manuscript.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import subprocess


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_block(lines, x, y, size=25.2, gap=29.2, weight="400", fill="#111111", anchor="start"):
    attrs = (
        f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
    )
    parts = [f'<text x="{x}" y="{y}" {attrs}>']
    for i, line in enumerate(lines):
        parts.append(f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{esc(line)}</tspan>')
    parts.append("</text>")
    return "\n".join(parts)


def bullets(items, x, y, accent="#1F4E79"):
    out, cy = [], y
    for lines in items:
        out.append(f'<circle cx="{x}" cy="{cy-7}" r="4.2" fill="{accent}"/>')
        out.append(text_block(lines, x + 18, cy))
        cy += 29.2 * len(lines) + 5
    return "\n".join(out)


def build_svg() -> str:
    width, height = 1900, 1225
    panel_w, panel_h, gap_x = 560, 430, 55
    left, top1, top2 = 55, 38, 515
    footer_y, footer_h = 985, 205
    xs = [left, left + panel_w + gap_x, left + 2 * (panel_w + gap_x)]
    accent, white, line = "#1F4E79", "#FFFFFF", "#7A7A7A"
    panels = [
        (1, ["Candidate signals"], [["Oil rents (t−1)"], ["Regulatory Quality estimate", "(WGI 2025 Revision;", "standard-unit scale, t−1)"], ["Trade excluded: wholly missing", "for Nigeria and Trinidad and Tobago"]]),
        (2, ["Construct provenance", "& coverage audit"], [["Annual inward FDI net flow,", "not inward FDI stock"], ["Signed asinh retains zero and", "504 negative-flow years"], ["31 oil-rent-intensive economies", "restored; Nigeria included"], ["RQ is a perception-based national", "proxy; construct validity is not", "established by this audit"]]),
        (3, ["Benchmark competitiveness"], [["Oil-rents test: M2 versus", "strongest naïve benchmark"], ["RQ test: M3 versus", "strongest naïve benchmark"], ["Benchmarks: zero flow,", "training-sample mean, lagged flow"], ["Question: is the surrounding model", "useful out of sample?"]]),
        (4, ["Matched signal increment"], [["Oil rents: ΔR² = R²(M2) − R²(M1)"], ["Regulatory Quality:", "ΔR² = R²(M3) − R²(M2)"], ["Adjacent rungs evaluated on", "identical country-year observations"], ["Question: what does the signal add", "beyond the preceding model rung?"]]),
        (5, ["Validation & uncertainty"], [["3 algorithms × 6 validation", "environments = 18 units/setup"], ["1 pooled unseen-country unit", "+ 5 future cutoffs"], ["2,000-replicate paired", "country-cluster bootstrap"], ["Final grid fixed before verdict", "generation and interpretation"]]),
        (6, ["Admissibility decision"], [["Five unit verdicts: material,", "marginal, setup-dependent,", "unsupported, coverage-limited"], ["10 setups per signal aggregated", "by locked cross-setup rules"], ["Output: candidate pre-weighting", "role; no AI–MCDM weights assigned"], ["Domain review and preference", "elicitation follow only after admission"]]),
    ]
    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="190mm" height="122.5mm" viewBox="0 0 {width} {height}">
<rect x="0" y="0" width="{width}" height="{height}" fill="{white}"/>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="{accent}"/></marker></defs>''']
    for idx, (num, title, body) in enumerate(panels):
        col, row = idx % 3, idx // 3
        x, y = xs[col], top1 if row == 0 else top2
        fill = "#F7F7F7" if idx % 2 == 0 else "#F1F3F5"
        svg.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="24" fill="{fill}" stroke="{line}" stroke-width="2.3"/>')
        svg.append(f'<circle cx="{x+52}" cy="{y+52}" r="29" fill="{accent}"/>')
        svg.append(text_block([str(num)], x + 52, y + 62, size=31, weight="700", fill=white, anchor="middle"))
        svg.append(text_block(title, x + 98, y + 47, size=31.5, gap=36, weight="700", fill=accent))
        divider = y + (112 if len(title) > 1 else 104)
        svg.append(f'<line x1="{x+26}" y1="{divider}" x2="{x+panel_w-26}" y2="{divider}" stroke="{line}" stroke-width="1.5"/>')
        svg.append(bullets(body, x + 38, divider + 42, accent))
    top_mid, bottom_mid = top1 + panel_h / 2, top2 + panel_h / 2
    for a, b, yy in [(0, 1, top_mid), (1, 2, top_mid), (0, 1, bottom_mid), (1, 2, bottom_mid)]:
        svg.append(f'<line x1="{xs[a]+panel_w}" y1="{yy}" x2="{xs[b]-12}" y2="{yy}" stroke="{accent}" stroke-width="3.2" marker-end="url(#arrow)"/>')
    route_y = top2 - 24
    svg.append(f'<path d="M {xs[2]+panel_w-18},{top_mid+72} L {xs[2]+panel_w+28},{top_mid+72} L {xs[2]+panel_w+28},{route_y} L {left-28},{route_y} L {left-28},{bottom_mid} L {left-4},{bottom_mid}" fill="none" stroke="{accent}" stroke-width="3.2" marker-end="url(#arrow)"/>')
    svg.append(f'<rect x="{left}" y="{footer_y}" width="{width-2*left}" height="{footer_h}" rx="24" fill="#EAF1F7" stroke="{accent}" stroke-width="2.3"/>')
    svg.append(text_block(["Audit principles"], left + 34, footer_y + 39, size=31.5, weight="700", fill=accent))
    principles = [
        ["Benchmark competitiveness is", "necessary but insufficient for", "signal admissibility."],
        ["Admissibility belongs to a", "signal within a defensible setup;", "it is not intrinsic to the variable."],
        ["Weighting follows empirical", "admission and domain review;", "weighting cannot repair a weak signal."],
    ]
    for n, (px, lines) in enumerate(zip([left+32, left+610, left+1188], principles), start=1):
        svg.append(f'<circle cx="{px+20}" cy="{footer_y+91}" r="20" fill="{accent}"/>')
        svg.append(text_block([str(n)], px + 20, footer_y + 100, size=23, weight="700", fill=white, anchor="middle"))
        svg.append(text_block(lines, px + 54, footer_y + 81))
    svg.append("</svg>")
    return "\n".join(svg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "figures")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    svg_text = build_svg()
    svg_path = args.output_dir / "Figure1_Validation_First_Architecture.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg_text.encode(), write_to=str(args.output_dir / "Figure1_Validation_First_Architecture.pdf"))
        cairosvg.svg2png(bytestring=svg_text.encode(), write_to=str(args.output_dir / "Figure1_Validation_First_Architecture_1000dpi.png"), output_width=7480)
    except ImportError as exc:
        raise SystemExit("Install CairoSVG to export PDF/PNG") from exc
    if shutil.which("inkscape"):
        subprocess.run(["inkscape", str(svg_path), "--export-type=eps", f"--export-filename={args.output_dir / 'Figure1_Validation_First_Architecture.eps'}"], check=True)


if __name__ == "__main__":
    main()
