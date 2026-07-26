import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import {
  isValidIntakeV6SvgFile,
  pickIntakeV6SvgFileFromFileList,
} from "@/lib/intakeV6/intakeV6SvgUploadFlow";

interface IntakeV6OperatorWorkspaceFileDropProps {
  workspaceId: string | undefined;
  workspaceLoaded: boolean;
  disabled?: boolean;
  onFileSelected: (file: File) => boolean | void | Promise<boolean | void>;
  onImportError?: (message: string) => void;
  children: ReactNode;
}

export default function IntakeV6OperatorWorkspaceFileDrop({
  workspaceId,
  workspaceLoaded,
  disabled = false,
  onFileSelected,
  onImportError,
  children,
}: IntakeV6OperatorWorkspaceFileDropProps) {
  const dragDepthRef = useRef(0);
  const [dragActive, setDragActive] = useState(false);
  const [importing, setImporting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const importDisabled = disabled || !workspaceLoaded || !workspaceId || importing;

  const processFiles = useCallback(
    async (files: FileList | File[] | null | undefined) => {
      if (importDisabled || !workspaceId) return;

      const picked = pickIntakeV6SvgFileFromFileList(files);
      if (!picked.file) {
        const message = picked.error ?? "Selecteaza un fisier SVG valid.";
        setNotice(message);
        onImportError?.(message);
        return;
      }

      setNotice(picked.error);
      setImporting(true);
      try {
        const ok = await onFileSelected(picked.file);
        if (ok === false) {
          setNotice("Import SVG esuat - vezi mesajul de eroare in pasul Layers.");
          return;
        }
        setNotice(`SVG analizat - ${picked.file.name}`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Import SVG esuat.";
        setNotice(message);
        onImportError?.(message);
      } finally {
        setImporting(false);
        dragDepthRef.current = 0;
        setDragActive(false);
      }
    },
    [importDisabled, onFileSelected, onImportError, workspaceId],
  );

  const handleDragEnter = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (importDisabled) return;
      event.preventDefault();
      event.stopPropagation();
      dragDepthRef.current += 1;
      if (event.dataTransfer.types.includes("Files")) {
        setDragActive(true);
      }
    },
    [importDisabled],
  );

  const handleDragOver = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (importDisabled) return;
      event.preventDefault();
      event.stopPropagation();
      event.dataTransfer.dropEffect = "copy";
    },
    [importDisabled],
  );

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (importDisabled) return;
      event.preventDefault();
      event.stopPropagation();
      dragDepthRef.current = 0;
      setDragActive(false);

      const dropped = [...event.dataTransfer.files];
      const svgFiles = dropped.filter((file) => isValidIntakeV6SvgFile(file));
      void processFiles(svgFiles.length > 0 ? svgFiles : dropped);
    },
    [importDisabled, processFiles],
  );

  useEffect(() => {
    const resetDragState = () => {
      dragDepthRef.current = 0;
      setDragActive(false);
    };
    window.addEventListener("dragend", resetDragState);
    window.addEventListener("drop", resetDragState);
    return () => {
      window.removeEventListener("dragend", resetDragState);
      window.removeEventListener("drop", resetDragState);
    };
  }, []);

  return (
    <div
      className="relative min-h-full"
      data-testid="intake-v6-operator-workspace-file-drop"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {children}
      {dragActive ? (
        <div
          className="pointer-events-none absolute inset-0 z-30 flex items-center justify-center border-2 border-dashed border-sky-400/70 bg-sky-500/10 backdrop-blur-[1px]"
          data-testid="intake-v6-operator-workspace-file-drop-overlay"
        >
          <div className="rounded-lg border border-sky-400/40 bg-wo-surface-inset/90 px-6 py-4 text-center shadow-lg">
            <p className="text-[13px] font-semibold text-sky-100">Trage fisierul SVG aici</p>
            <p className="mt-1 text-[10px] text-sky-200/80">
              Analiza imediata (ca SVG Analyzer), apoi salvare in workspace V6.
            </p>
          </div>
        </div>
      ) : null}
      {notice ? (
        <p
          className="pointer-events-none absolute bottom-16 right-3 z-20 max-w-sm rounded-md border border-sky-500/30 bg-wo-surface-inset/95 px-3 py-2 text-[10px] text-sky-100"
          data-testid="intake-v6-operator-workspace-file-drop-notice"
        >
          {notice}
        </p>
      ) : null}
      {importing ? (
        <p
          className="pointer-events-none absolute bottom-16 left-3 z-20 rounded-md border border-slate-600/40 bg-wo-surface-inset/95 px-3 py-2 text-[10px] text-slate-200"
          data-testid="intake-v6-operator-workspace-file-drop-importing"
        >
          Procesez SVG...
        </p>
      ) : null}
    </div>
  );
}



