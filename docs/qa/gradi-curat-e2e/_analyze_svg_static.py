"""Read-only static inspection of gradi-curat.svg — diagnostic only."""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

SRC = Path(r"C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg")
OUT = Path(__file__).with_name("svg_static_analysis.json")


def local(tag: str) -> str:
    return tag.split("}")[-1] if isinstance(tag, str) else str(tag)


def main() -> None:
    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest().upper()
    text = raw.decode("utf-8", errors="replace")
    out: dict = {
        "path": str(SRC),
        "filename": SRC.name,
        "size_bytes": len(raw),
        "sha256": sha,
        "mtime": datetime.fromtimestamp(SRC.stat().st_mtime).isoformat(),
        "original_unchanged": True,
        "xml_valid": False,
        "parse_error": None,
    }

    try:
        root = ET.fromstring(raw)
        out["xml_valid"] = True
    except Exception as exc:  # noqa: BLE001
        out["parse_error"] = str(exc)
        OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps(out, indent=2))
        return

    out["tag"] = root.tag
    out["attrib"] = dict(root.attrib)
    out["width"] = root.attrib.get("width")
    out["height"] = root.attrib.get("height")
    out["viewBox"] = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    out["xmlns_default"] = None
    m_ns = re.search(r'xmlns="([^"]+)"', text)
    if m_ns:
        out["xmlns_default"] = m_ns.group(1)
    out["namespaces"] = sorted(
        {
            f"{m.group(1) or 'default'}={m.group(2)}"
            for m in re.finditer(r'xmlns(?::([A-Za-z0-9_-]+))?="([^"]+)"', text)
        }
    )

    counts: Counter[str] = Counter()
    ids: list[str] = []
    transforms = 0
    nested_transform_depth = 0
    style_blocks = 0
    images: list[dict] = []
    uses: list[str | None] = []
    fonts_text: list[dict] = []
    hidden = 0
    clip_mask = 0
    external_refs: list[str] = []

    stack = [(root, False)]
    while stack:
        node, anc_tf = stack.pop()
        name = local(node.tag)
        counts[name] += 1
        atr = node.attrib
        if "id" in atr:
            ids.append(atr["id"])
        tf = "transform" in atr
        if tf:
            transforms += 1
            if anc_tf:
                nested_transform_depth += 1
        style = atr.get("style", "")
        style_compact = style.replace(" ", "")
        if (
            "display:none" in style_compact
            or atr.get("visibility") == "hidden"
            or atr.get("display") == "none"
        ):
            hidden += 1
        if name == "style":
            style_blocks += 1
        if name == "image":
            href = (
                atr.get("{http://www.w3.org/1999/xlink}href")
                or atr.get("href")
                or atr.get("xlink:href")
            )
            images.append(
                {
                    "href_prefix": (href or "")[:80],
                    "embedded_data": bool(href and str(href).startswith("data:")),
                }
            )
            if href and not str(href).startswith("data:") and (
                "http" in str(href) or str(href).startswith("//")
            ):
                external_refs.append(str(href))
        if name == "use":
            href = (
                atr.get("{http://www.w3.org/1999/xlink}href")
                or atr.get("href")
                or atr.get("xlink:href")
            )
            uses.append(href)
        if name in ("text", "tspan"):
            fonts_text.append(
                {
                    "tag": name,
                    "font_family": atr.get("font-family"),
                    "text": "".join(node.itertext())[:80],
                }
            )
        if name in ("clipPath", "mask"):
            clip_mask += 1
        for _k, v in atr.items():
            if isinstance(v, str) and (
                v.startswith("http://") or v.startswith("https://")
            ):
                if "w3.org" not in v and "inkscape" not in v.lower():
                    external_refs.append(v)
        for child in list(node):
            stack.append((child, anc_tf or tf))

    open_p = closed_p = stroke_only = fill_paths = 0
    path_samples: list[str] = []
    for el in root.iter():
        if local(el.tag) != "path":
            continue
        d = el.attrib.get("d", "")
        if len(path_samples) < 5:
            path_samples.append(d[:120])
        if re.search(r"[Zz]", d):
            closed_p += 1
        else:
            open_p += 1
        fill = el.attrib.get("fill", "")
        stroke = el.attrib.get("stroke", "")
        style = el.attrib.get("style", "")
        style_compact = style.replace(" ", "")
        if "fill:none" in style_compact or fill == "none":
            if (stroke and stroke != "none") or "stroke:" in style:
                stroke_only += 1
        else:
            fill_paths += 1

    id_counts = Counter(ids)
    dup_ids = [i for i, c in id_counts.items() if c > 1]

    units_hint = []
    for val in (out["width"], out["height"]):
        if not val:
            continue
        m = re.match(r"([0-9.]+)\s*([a-zA-Z%]*)", str(val))
        if m:
            units_hint.append(
                {
                    "raw": val,
                    "number": m.group(1),
                    "unit": m.group(2) or "unitless",
                }
            )

    wb = out["viewBox"]
    unsupported = sorted(
        k
        for k in counts
        if k
        not in {
            "svg",
            "g",
            "path",
            "rect",
            "circle",
            "ellipse",
            "polygon",
            "polyline",
            "line",
            "text",
            "tspan",
            "image",
            "use",
            "defs",
            "clipPath",
            "mask",
            "title",
            "desc",
            "metadata",
            "style",
            "linearGradient",
            "radialGradient",
            "stop",
            "pattern",
            "symbol",
            "marker",
            "filter",
            "feGaussianBlur",
            "feOffset",
            "feMerge",
            "feMergeNode",
            "feBlend",
            "feColorMatrix",
            "feFlood",
            "feComposite",
            "feMorphology",
            "sodipodi",
            "namedview",
        }
        and not k.startswith("sodipodi")
        and not k.startswith("inkscape")
        and k not in {"RDF", "Work", "format", "type", "title"}
    )

    geom = {
        "width": {
            "value": out["width"],
            "class": "directly_declared" if out["width"] else "unavailable",
        },
        "height": {
            "value": out["height"],
            "class": "directly_declared" if out["height"] else "unavailable",
        },
        "viewBox": {
            "value": out["viewBox"],
            "class": "directly_declared" if out["viewBox"] else "unavailable",
        },
        "physical_mm": {
            "value": None,
            "class": "ambiguous",
            "note": "Inspect units_on_root; no assumed mm without explicit unit",
        },
        "total_path_length": {"value": None, "class": "unavailable"},
        "closed_shape_area": {"value": None, "class": "unavailable"},
        "separate_shapes_letters": {
            "value": counts.get("path", 0),
            "class": "estimated",
            "note": "path element count only; not letter segmentation",
        },
    }

    usable = {
        "likely": bool(
            out["xml_valid"]
            and counts.get("path", 0) > 0
            and counts.get("image", 0) == 0
            and not fonts_text
        ),
        "notes": [],
    }
    if fonts_text:
        usable["notes"].append("contains_text_nodes")
    if images:
        usable["notes"].append("contains_images")
    if not out["viewBox"] and not out["width"]:
        usable["notes"].append("missing_dimensions")
        usable["likely"] = False
    if any(u.get("unit") == "unitless" for u in units_hint):
        usable["notes"].append("unitless_root_dimensions_px_mm_ambiguous")

    out.update(
        {
            "element_counts": dict(sorted(counts.items())),
            "path_count": counts.get("path", 0),
            "rect": counts.get("rect", 0),
            "circle": counts.get("circle", 0),
            "ellipse": counts.get("ellipse", 0),
            "polygon": counts.get("polygon", 0),
            "polyline": counts.get("polyline", 0),
            "line": counts.get("line", 0),
            "text_nodes": counts.get("text", 0) + counts.get("tspan", 0),
            "image": counts.get("image", 0),
            "use": counts.get("use", 0),
            "group_g": counts.get("g", 0),
            "clipPath": counts.get("clipPath", 0),
            "mask": counts.get("mask", 0),
            "transforms_count": transforms,
            "nested_transform_pairs": nested_transform_depth,
            "style_blocks": style_blocks,
            "has_css_style": style_blocks > 0 or "<style" in text.lower(),
            "hidden_elements_est": hidden,
            "clip_or_mask": clip_mask,
            "images": images,
            "uses_sample": uses[:10],
            "fonts_text_sample": fonts_text[:10],
            "external_refs": list(dict.fromkeys(external_refs))[:20],
            "open_paths_est": open_p,
            "closed_paths_est": closed_p,
            "stroke_only_paths_est": stroke_only,
            "fill_paths_est": fill_paths,
            "duplicate_ids": dup_ids[:20],
            "duplicate_id_count": len(dup_ids),
            "units_on_root": units_hint,
            "viewBox_parts": wb.split() if wb else None,
            "path_samples": path_samples,
            "unsupported_or_unusual_elements": unsupported[:40],
            "geometry_truth": geom,
            "production_vector_usable_without_modification": usable,
            "head_snippet": text[:400],
        }
    )

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("sha", sha)
    print("valid", out["xml_valid"], "w", out["width"], "h", out["height"], "vb", out["viewBox"])
    print("counts", {k: counts[k] for k in sorted(counts) if counts[k]})
    print(
        "paths open/closed",
        open_p,
        closed_p,
        "text",
        len(fonts_text),
        "images",
        len(images),
        "dup_ids",
        len(dup_ids),
    )
    print("usable", usable)


if __name__ == "__main__":
    main()
