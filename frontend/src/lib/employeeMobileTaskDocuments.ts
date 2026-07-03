import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

export interface EmployeeMobileTaskDocument {
  id?: string;
  name?: string;
  type?: string;
  url?: string;
  source?: string;
  downloadable?: boolean;
}

export function taskInstructionsText(task: EmployeeMobileTaskDTO): string | null {
  const instructions = task.instructions?.trim();
  const description = task.description?.trim();
  if (instructions && description && instructions !== description) {
    return `${instructions}\n\n${description}`;
  }
  return instructions || description || null;
}

export function normalizeTaskDocuments(
  documents?: EmployeeMobileTaskDTO["documents"],
): EmployeeMobileTaskDocument[] {
  if (!documents?.length) return [];
  return documents.map((raw, index) => {
    const doc = raw as Record<string, unknown>;
    const name =
      (typeof doc.name === "string" && doc.name) ||
      (typeof doc.label === "string" && doc.label) ||
      `Document ${index + 1}`;
    const type =
      (typeof doc.type === "string" && doc.type) ||
      (typeof doc.document_type === "string" && doc.document_type) ||
      "file";
    const source = typeof doc.source === "string" ? doc.source : "task";
    const urlRaw = doc.url ?? doc.href ?? doc.download_url;
    const url = typeof urlRaw === "string" && urlRaw.trim() ? urlRaw.trim() : undefined;
    const id =
      (typeof doc.id === "string" && doc.id) ||
      (typeof doc.file_id === "string" && doc.file_id) ||
      `doc-${index + 1}`;
    return { id, name, type, source, url, downloadable: doc.downloadable === true };
  });
}

export function documentSourceLabel(source?: string): string {
  switch (source) {
    case "intake_work_file":
      return "Fișier comandă";
    case "task":
      return "Task";
    case "production_plan":
      return "Plan producție";
    default:
      return source ? source.replace(/_/g, " ") : "Document";
  }
}

export function documentTypeLabel(type?: string): string {
  if (!type) return "Fișier";
  const normalized = type.toLowerCase();
  if (normalized.includes("pdf")) return "PDF";
  if (normalized.includes("svg")) return "SVG";
  if (normalized.includes("png") || normalized.includes("jpg") || normalized.includes("jpeg")) {
    return "Imagine";
  }
  return type;
}
