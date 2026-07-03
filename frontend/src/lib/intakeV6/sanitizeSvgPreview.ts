/** Strip active content before inline SVG preview (client-side display only). */
export function sanitizeIntakeV4SvgPreviewSource(source: string): string {
  return source
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, "")
    .replace(/javascript:/gi, "");
}

export { sanitizeIntakeV4SvgPreviewSource as sanitizeIntakeV6SvgPreviewSource };
