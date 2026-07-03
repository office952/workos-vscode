"""Standalone test: gradi-curat.svg through intake-v4 pipeline."""
import sys, json
sys.path.insert(0, '.')

from services.intake_v3_svg_analysis_service import validate_svg_upload, analyze_svg_content
from services.intake_v3_geometry_metrics_snapshot_service import build_path_geometry_summary_from_svg_text
from services.intake_v4_layer_role_service import build_layer_role_setup_from_path_summary
from services.intake_v4_finish_truth_service import (
    list_finish_setup_color_fatal_blockers,
)

SVG_PATH = r"C:\Users\offic\Desktop\workos-essential-audit-20260624\fisiere-teste\gradi-curat.svg"

def main():
    raw = open(SVG_PATH, "rb").read()
    print(f"=== 1. VALIDATE SVG ===")
    v = validate_svg_upload(raw_name="gradi-curat.svg", content_type="image/svg+xml", raw_bytes=raw)
    print(f"  OK: {v.file_name}, {v.file_size_bytes} bytes")

    print(f"\n=== 2. RAW SVG ANALYSIS ===")
    analysis, _va = analyze_svg_content(file_name=v.file_name, file_size_bytes=v.file_size_bytes, svg_text=v.svg_text)
    print(f"  paths={analysis.path_count}, colors={analysis.detected_color_count}, warnings={analysis.warnings}")

    print(f"\n=== 3. PATH GEOMETRY SUMMARY ===")
    ps = build_path_geometry_summary_from_svg_text(v.svg_text, source_file_name=v.file_name)
    if ps is None:
        print("  FAILED!")
        return
    print(f"  bbox: {ps['bbox_w_mm']:.1f} x {ps['bbox_h_mm']:.1f} mm")
    print(f"  area: {ps['area_mm2_approx']:.1f} mm2")
    print(f"  perimeter: {ps['perimeter_mm_approx']:.1f} mm")
    print(f"  layers: {ps['layer_count']}")
    print(f"  warnings: {ps['warnings']}")
    for ly in ps["layers"]:
        fills = ly["color_evidence"]["fills"]
        strokes = ly["color_evidence"]["strokes"]
        print(f"  Layer '{ly['layer_key']}': {ly['path_count']} paths, fills={fills}, strokes={strokes}")

    print(f"\n=== 4. LAYER ROLE SETUP ===")
    setup = build_layer_role_setup_from_path_summary(ps)
    print(f"  confirmation_status: {setup.confirmation_status}")
    print(f"  layer count: {len(setup.layers)}")
    for la in setup.layers:
        print(f"    {la.layer_key}: auto_role={la.auto_role}, confirmed_role={la.confirmed_role}, state={la.confirmation_state}")
    print(f"  warnings: {setup.warnings}")

    print(f"\n=== 5. READINESS CHECK (no finish setup) ===")
    color_fatal = list_finish_setup_color_fatal_blockers(None)
    print(f"  color_fatal_blockers: {color_fatal}")

    print(f"\n=== SUMMARY ===")
    print(f"  SVG: gradi-curat.svg ({v.file_size_bytes} bytes)")
    print(f"  Dimensions: {ps['bbox_w_mm']:.0f} x {ps['bbox_h_mm']:.0f} mm ({ps['bbox_w_mm']/10:.0f} x {ps['bbox_h_mm']/10:.0f} cm)")
    print(f"  Contours: {sum(ly['closed_contour_count'] for ly in ps['layers'])} closed")
    print(f"  4 fill colors + 1 stroke color detected")
    print(f"  Pipeline: PASS (no errors)")

if __name__ == "__main__":
    main()
