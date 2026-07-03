/**
 * Generate technical SVG for Anne's Store volumetric sign (4000 x 700 mm).
 * Output: frontend/e2e/fixtures/annes-store-volumetric.svg
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "..", "e2e", "fixtures", "annes-store-volumetric.svg");

const W = 4000;
const H = 700;

function rectPath(x, y, w, h) {
  return `M ${x} ${y} H ${x + w} V ${y + h} H ${x} Z`;
}

/** Simplified block letter outlines (closed paths, mm). */
function letterPath(ch, x, y, w, h) {
  const cx = x + w / 2;
  const cy = y + h / 2;
  const t = Math.max(4, w * 0.12);
  switch (ch) {
    case "A":
      return [
        `M ${x} ${y + h} L ${cx} ${y} L ${x + w} ${y + h} Z`,
        `M ${x + t * 1.4} ${y + h * 0.62} H ${x + w - t * 1.4} L ${x + w - t} ${y + h * 0.62} H ${x + t} Z`,
      ].join(" ");
    case "N":
      return `M ${x} ${y + h} V ${y} H ${x + t} V ${y + h - t} L ${x + w - t} ${y} V ${y + h} H ${x + w} V ${y} H ${x + w - t} V ${y + h - t} L ${x + t} ${y} V ${y + h} H ${x} Z`;
    case "E":
      return `M ${x + w} ${y} H ${x} V ${y + h} H ${x + w} V ${y + h - t} H ${x + t} V ${cy + t / 2} H ${x + w * 0.72} V ${cy - t / 2} H ${x + t} V ${y + t} H ${x + w} Z`;
    case "S":
      return `M ${x + w} ${y + t} Q ${x + w} ${y} ${x + w * 0.55} ${y} H ${x + w * 0.4} Q ${x} ${y} ${x} ${cy - t} Q ${x} ${cy} ${x + w * 0.45} ${cy} H ${x + w * 0.6} Q ${x + w} ${cy} ${x + w} ${cy + t} Q ${x + w} ${y + h} ${x + w * 0.55} ${y + h} H ${x + w * 0.4} Q ${x} ${y + h} ${x} ${y + h - t} Q ${x} ${cy + t} ${x + w * 0.45} ${cy + t} H ${x + w * 0.6} Q ${x + w} ${cy + t} ${x + w} ${cy} Z`;
    case "T":
      return `M ${x} ${y} H ${x + w} V ${y + t} H ${cx + t} V ${y + h} H ${cx - t} V ${y + t} H ${x} Z`;
    case "O":
      return `M ${cx} ${y} A ${w / 2} ${h / 2} 0 1 1 ${cx - 0.01} ${y} Z M ${cx} ${y + t} A ${w / 2 - t} ${h / 2 - t} 0 1 0 ${cx + 0.01} ${y + t} Z`;
    case "R":
      return `M ${x} ${y + h} V ${y} H ${x + w * 0.62} Q ${x + w} ${y} ${x + w} ${y + h * 0.38} Q ${x + w} ${cy} ${x + w * 0.68} ${cy} L ${x + w} ${y + h} H ${x + w * 0.78} L ${x + w * 0.52} ${cy + t} H ${x + t} V ${y + h} Z`;
    case "C":
      return `M ${x + w} ${y + h * 0.28} Q ${x + w * 0.55} ${y} ${cx} ${y} Q ${x} ${y} ${x} ${cy} Q ${x} ${y + h} ${cx} ${y + h} Q ${x + w * 0.55} ${y + h} ${x + w} ${y + h * 0.72} L ${x + w - t} ${y + h * 0.68} Q ${x + w * 0.5} ${y + h - t} ${cx} ${y + h - t} Q ${x + t} ${y + h - t} ${x + t} ${cy} Q ${x + t} ${y + t} ${cx} ${y + t} Q ${x + w * 0.5} ${y + t} ${x + w - t} ${y + h * 0.32} Z`;
    case "H":
      return `M ${x} ${y + h} V ${y} H ${x + t} V ${cy - t / 2} H ${x + w - t} V ${y} H ${x + w} V ${y + h} H ${x + w - t} V ${cy + t / 2} H ${x + t} V ${y + h} H ${x} Z`;
    case "&":
      return `M ${x + w * 0.82} ${y + h} Q ${x + w} ${y + h * 0.55} ${x + w * 0.55} ${y + h * 0.48} Q ${x} ${y + h * 0.38} ${x + w * 0.18} ${y + h * 0.62} Q ${x + w * 0.42} ${y + h * 0.88} ${x + w * 0.72} ${y + h * 0.82} L ${x + w * 0.48} ${y + h * 0.2} Q ${x + w * 0.2} ${y + h * 0.05} ${x + w * 0.35} ${y + t} Q ${x + w * 0.72} ${y} ${x + w * 0.88} ${y + h * 0.28} Z`;
    case "'":
      return rectPath(x + w * 0.35, y, w * 0.3, h * 0.22);
    case " ":
      return "";
    default:
      return rectPath(x + t, y + t, w - 2 * t, h - 2 * t);
  }
}

function layoutLine(text, startX, endX, y, height, fillDefault) {
  const visible = [...text];
  const slots = visible.filter((c) => c !== " ").length;
  const totalWidth = endX - startX;
  const gap = totalWidth / Math.max(slots, 1);
  let slot = 0;
  const paths = [];

  for (const ch of visible) {
    if (ch === " ") {
      slot += 0.55;
      continue;
    }
    const lw = gap * 0.72;
    const lx = startX + slot * gap + (gap - lw) / 2;
    const d = letterPath(ch, lx, y, lw, height);
    if (!d) continue;
    const fill = ch === "A" && fillDefault === "main" ? "#E30613" : "#1A1A1A";
    const id = `letter_${fillDefault}_${ch}_${slot}`.replace(/[^a-zA-Z0-9_]/g, "_");
    paths.push(
      `  <path id="${id}" d="${d}" fill="${fill}" fill-rule="evenodd" stroke="none"/>`
    );
    slot += 1;
  }
  return paths;
}

/** Atypical Alucobond backing — stepped center tongue + right-edge notch. */
function backingPath() {
  const tongueL = 1180;
  const tongueR = 2820;
  const topH = 520;
  return [
    `M 0 0 H ${W} V ${topH - 30}`,
    `H ${W - 36}`,
    `A 36 36 0 0 0 ${W} ${topH + 24}`,
    `V ${topH} H ${tongueR} V ${H} H ${tongueL} V ${topH} H 0 Z`,
  ].join(" ");
}

const mainPaths = layoutLine("ANNE'S STORE", 100, 3720, 90, 400, "main");
const subPaths = layoutLine("CASH & CARRY", 1260, 2740, 545, 130, "sub");

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
  width="${W}mm" height="${H}mm"
  viewBox="0 0 ${W} ${H}"
  version="1.1">
  <title>Anne's Store — litere volumetrice 4000x700</title>
  <desc>Technical layout: ANNE'S STORE + CASH &amp; CARRY. A=red in drawing; production letters white except A. Dimensions mm.</desc>

  <g id="Fundal_Alucobond" data-role="support_panel">
    <path id="panou_fundal_atipic"
      d="${backingPath()}"
      fill="none"
      stroke="#64748B"
      stroke-width="2"
      vector-effect="non-scaling-stroke"/>
  </g>

  <g id="Litere_Volumetrice" data-role="volumetric_letters">
${mainPaths.join("\n")}
${subPaths.join("\n")}
  </g>
</svg>
`;

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, svg, "utf8");
console.log(`Wrote ${OUT}`);
console.log(`Letters: ${mainPaths.length + subPaths.length} paths, viewBox 0 0 ${W} ${H}`);
