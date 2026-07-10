import { useEffect, useMemo, useRef, useState } from "react";
import {
  filterColorRegistry,
  formatColorRegistryLabel,
  searchColorRegistry,
  ALL_COLOR_REGISTRY_ITEMS,
} from "@/lib/colorRegistry/colorRegistry";
import type { ColorRegistryFilter } from "@/lib/colorRegistry/colorRegistry";
import type { ColorRegistryItem } from "@/lib/colorRegistry/colorRegistryTypes";

const fieldClass =
  "w-full bg-[#0A0F1A] border border-[#2A3548] rounded-lg px-3 py-2.5 text-[13px] font-medium text-slate-100 outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30";
const labelClass =
  "text-[10px] uppercase tracking-wide text-slate-500 font-semibold mb-1 block";
const helperClass = "text-[9px] text-slate-600 leading-snug";

/** Shared Intake V6 color row — card flex + fixed Schimbă button. */
const colorRowClass = "flex h-9 items-stretch gap-2";
const colorCardButtonClass =
  "flex h-9 min-h-9 min-w-0 flex-1 items-center gap-2 rounded-md border border-[#2A3548] bg-[#0A0F1A]/80 px-2 text-left transition hover:border-cyan-500/40 hover:bg-[#0A0F1A] disabled:opacity-50";
const colorChangeButtonClass =
  "inline-flex h-9 w-[4.75rem] shrink-0 items-center justify-center rounded-md border border-[#2A3548] bg-[#1E293B] px-2 text-[10px] font-semibold uppercase tracking-wide text-slate-300 transition hover:border-cyan-500/40 hover:text-cyan-200 disabled:opacity-50 whitespace-nowrap";
const colorBadgeClass =
  "inline-flex h-5 max-w-[4.25rem] shrink-0 items-center justify-center truncate rounded border border-purple-500/30 bg-purple-500/10 px-1 py-0.5 text-[7px] font-bold uppercase tracking-wide text-purple-300/90";
const colorChooseButtonClass =
  "flex h-9 w-full items-center rounded-md border border-dashed border-[#2A3548] bg-[#0A0F1A]/40 px-3 text-left text-[11px] font-semibold text-cyan-300/90 transition hover:border-cyan-500/40 hover:bg-[#0A0F1A] disabled:opacity-50";
const reviewLabelClass =
  "mb-1 block min-h-[2rem] text-[10px] font-semibold uppercase leading-tight tracking-wide text-slate-500";

export interface ColorRegistrySelectProps {
  label: string;
  valueCode?: string | null;
  filter: ColorRegistryFilter;
  onChange: (item: ColorRegistryItem | null) => void;
  disabled?: boolean;
  testId?: string;
  showApproxNote?: boolean;
  /** Fixed label height for paired Față / Cant review rows. */
  reviewAlign?: boolean;
}

function ColorSwatch({ hex }: { hex: string }) {
  return (
    <span
      className="inline-block h-5 w-5 shrink-0 rounded border border-slate-600"
      style={{ backgroundColor: hex }}
      aria-hidden
    />
  );
}

function colorCodeLabel(item: ColorRegistryItem): string {
  if (item.system === "RAL") return `RAL ${item.code}`;
  return `Oracal ${item.series}-${item.code}`;
}

function colorNameLabel(item: ColorRegistryItem): string {
  if (item.romanianName) return `${item.name} / ${item.romanianName}`;
  return item.name;
}

function seriesBadge(item: ColorRegistryItem): string | null {
  if (item.system === "RAL") return "RAL";
  if (item.series === "8500") return "8500 translucent";
  if (item.series === "651") return "651 colored";
  return null;
}

/** Hide series pill when the selected card label already carries the series (e.g. Oracal 651-010). */
function showSelectedSeriesBadge(item: ColorRegistryItem): boolean {
  if (item.system === "RAL") return false;
  if (item.series === "651") return false;
  return seriesBadge(item) != null;
}

export default function ColorRegistrySelect({
  label,
  valueCode,
  filter,
  onChange,
  disabled = false,
  testId = "color-registry-select",
  showApproxNote = false,
  reviewAlign = false,
}: ColorRegistrySelectProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const baseItems = useMemo(
    () => filterColorRegistry(ALL_COLOR_REGISTRY_ITEMS, filter),
    [filter],
  );

  const filtered = useMemo(
    () => searchColorRegistry(baseItems, query),
    [baseItems, query],
  );

  const selected = useMemo(() => {
    if (!valueCode) return undefined;
    return baseItems.find((item) => item.code === valueCode);
  }, [baseItems, valueCode]);

  function openPicker() {
    if (disabled) return;
    setQuery("");
    setOpen(true);
  }

  function closePicker() {
    setOpen(false);
    setQuery("");
  }

  function selectItem(item: ColorRegistryItem) {
    onChange(item);
    closePicker();
  }

  useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        closePicker();
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  return (
    <div
      className={`relative ${reviewAlign ? "space-y-1" : "space-y-1.5"}`}
      data-testid={testId}
      ref={rootRef}
    >
      <span className={reviewAlign ? reviewLabelClass : labelClass}>{label}</span>

      {!open && selected ? (
        <div className={colorRowClass} data-testid={`${testId}-row`}>
          <button
            type="button"
            className={colorCardButtonClass}
            disabled={disabled}
            onClick={openPicker}
            data-testid={`${testId}-trigger`}
            aria-expanded={open}
            aria-haspopup="listbox"
          >
            <ColorSwatch hex={selected.previewHex} />
            <span className="min-w-0 flex-1 overflow-hidden leading-tight">
              <span className="block truncate text-[11px] font-semibold text-slate-100">
                {colorCodeLabel(selected)}
              </span>
              <span className="block truncate text-[9px] text-slate-400">
                {colorNameLabel(selected)}
              </span>
            </span>
            {showSelectedSeriesBadge(selected) ? (
              <span className={colorBadgeClass} title={seriesBadge(selected) ?? undefined}>
                {seriesBadge(selected)}
              </span>
            ) : null}
          </button>
          <button
            type="button"
            className={colorChangeButtonClass}
            disabled={disabled}
            onClick={openPicker}
            data-testid={`${testId}-change`}
          >
            Schimbă
          </button>
        </div>
      ) : null}

      {!open && !selected ? (
        <button
          type="button"
          className={colorChooseButtonClass}
          disabled={disabled}
          onClick={openPicker}
          data-testid={`${testId}-choose`}
        >
          Alege culoare
        </button>
      ) : null}

      {showApproxNote && !open ? (
        <p className={helperClass} data-testid={`${testId}-approx-note`}>
          Preview HEX/RGB este aproximativ — culoarea RAL reală depinde de vopsea, material și lumină.
        </p>
      ) : null}

      {open && !disabled ? (
        <div
          className="rounded-lg border border-[#2A3548] bg-[#0D1321] p-2 shadow-lg"
          data-testid={`${testId}-panel`}
        >
          <input
            id={`${testId}-search`}
            type="search"
            className={`${fieldClass} mb-2`}
            placeholder="Caută cod sau denumire…"
            value={query}
            autoFocus
            onChange={(event) => setQuery(event.target.value)}
            data-testid={`${testId}-search`}
          />
          <p className={helperClass} data-testid={`${testId}-list-count`}>
            {filtered.length} {filtered.length === 1 ? "culoare" : "culori"}
            {query.trim() ? ` pentru „${query.trim()}”` : ""}
          </p>
          <ul
            className="mt-1 max-h-72 overflow-y-auto rounded-lg border border-[#2A3548] bg-[#0A0F1A] divide-y divide-[#1E293B]"
            data-testid={`${testId}-list`}
            role="listbox"
            aria-label={label}
          >
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-[11px] text-slate-500">Niciun rezultat.</li>
            ) : (
              filtered.map((item) => (
                <li key={`${item.system}-${item.series ?? ""}-${item.code}`}>
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-[11px] text-slate-200 hover:bg-[#1E293B]/80 disabled:opacity-40"
                    disabled={!item.active}
                    onClick={() => selectItem(item)}
                    data-testid={`${testId}-option-${item.system}-${item.series ?? "ral"}-${item.code}`}
                  >
                    <ColorSwatch hex={item.previewHex} />
                    <span className="flex-1">{formatColorRegistryLabel(item)}</span>
                    <span className="text-[9px] uppercase text-slate-500">
                      {item.system}
                      {item.series ? ` ${item.series}` : ""}
                    </span>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}

      {selected && !open ? (
        <span className="sr-only" data-testid={`${testId}-selected`}>
          {formatColorRegistryLabel(selected)}
        </span>
      ) : null}
    </div>
  );
}
