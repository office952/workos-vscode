import { pickIntakeV6SvgFileFromFileList } from "@/lib/intakeV6/intakeV6SvgUploadFlow";

export const DEFAULT_SVG_ACCEPT = ".svg,image/svg+xml";

export interface WorkOsSvgFilePickerGuardState {
  ready: boolean;
  busy: boolean;
  notReadyMessage?: string;
  busyMessage?: string;
}

export function resolveWorkOsSvgFilePickerBlockMessage(
  state: WorkOsSvgFilePickerGuardState,
): string | null {
  if (state.busy) {
    return state.busyMessage ?? "Procesare SVG în curs — așteaptă.";
  }
  if (!state.ready) {
    return state.notReadyMessage ?? "Workspace indisponibil — reîncarcă pagina.";
  }
  return null;
}

export function processWorkOsSvgFilePickerSelection(
  files: FileList | File[] | null | undefined,
  state: WorkOsSvgFilePickerGuardState,
): { file: File | null; error: string | null; warning: string | null; blocked: boolean } {
  const blockedMessage = resolveWorkOsSvgFilePickerBlockMessage(state);
  if (blockedMessage) {
    return { file: null, error: blockedMessage, warning: null, blocked: true };
  }

  const picked = pickIntakeV6SvgFileFromFileList(files);
  if (!picked.file) {
    return { file: null, error: picked.error ?? "No file selected.", warning: null, blocked: false };
  }

  return {
    file: picked.file,
    error: null,
    warning: picked.error,
    blocked: false,
  };
}
