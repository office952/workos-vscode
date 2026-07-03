import fs from "node:fs";
import path from "node:path";

const distDir = path.resolve("dist");
const banned = ["Mega Image", "Dedeman", "Kaufland"];

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...walk(full));
    } else {
      out.push(full);
    }
  }
  return out;
}

if (!fs.existsSync(distDir)) {
  console.error("[bundle-hygiene] dist folder not found. Run build first.");
  process.exit(1);
}

const files = walk(distDir).filter((f) => /\.(js|css|html|map|txt)$/i.test(f));
const hits = [];

for (const file of files) {
  let content = "";
  try {
    content = fs.readFileSync(file, "utf8");
  } catch {
    continue;
  }
  for (const needle of banned) {
    if (content.includes(needle)) {
      hits.push({ file: path.relative(process.cwd(), file), needle });
    }
  }
}

if (hits.length > 0) {
  console.error("[bundle-hygiene] banned demo strings found in production bundle:");
  for (const hit of hits) {
    console.error(`- ${hit.needle} in ${hit.file}`);
  }
  process.exit(2);
}

console.log("[bundle-hygiene] PASS: no banned demo strings found in dist bundle.");
