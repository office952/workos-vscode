export function isValidIntakeV4SvgFile(file: File): boolean {
  const name = file.name.toLowerCase();
  if (name.endsWith(".svg")) return true;
  return file.type === "image/svg+xml";
}

export function pickIntakeV4SvgFileFromFileList(
  files: FileList | File[] | null | undefined,
): {
  file: File | null;
  error: string | null;
} {
  if (!files || files.length === 0) {
    return { file: null, error: "No file selected." };
  }
  if (files.length > 1) {
    const first = files[0];
    if (first && isValidIntakeV4SvgFile(first)) {
      return { file: first, error: "Multiple files dropped — using the first SVG only." };
    }
    return { file: null, error: "Please drop a single SVG file." };
  }
  const file = files[0];
  if (!file || !isValidIntakeV4SvgFile(file)) {
    return { file: null, error: "Please select a valid SVG file." };
  }
  return { file, error: null };
}
