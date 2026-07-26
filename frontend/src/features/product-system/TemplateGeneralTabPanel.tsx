import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Archive,
  BookOpen,
  Calculator,
  ClipboardList,
  Clock,
  ExternalLink,
  FileText,
  Fingerprint,
  Inbox,
  Info,
  Layers,
  Lightbulb,
  Package,
  StickyNote,
  Workflow,
} from "lucide-react";
import type { ProductFamily } from "@/api/productFamilies";
import {
  CALIBRATION_DURATION_TOOLTIP,
  UNIT_PRICING_NOTE,
  formatInternalTemplateHours,
} from "@/features/product-system/templateCalibrationDisplay";
import { isVolumetricLettersTemplate } from "@/features/product-system/componentTypeDisplay";

type DraftLike = {
  template_code: string;
  family_id: string;
  family_name: string;
  description: string;
  notes: string;
  estimated_hours: number;
  base_labor_rate: number;
  base_margin_pct: number;
};

function hasLegacyTechnicalNotes(notes: string): boolean {
  const n = notes.trim().toLowerCase();
  return (
    n.includes("input params") ||
    n.includes("ref docs") ||
    n.includes("save-smoke") ||
    n.includes("downstream") ||
    n.includes("docs/production/")
  );
}

function SectionCard({
  title,
  icon,
  children,
  className = "",
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-4 space-y-2.5 h-full ${className}`}
    >
      <div className="flex items-center gap-2">
        <span className="w-7 h-7 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-300 shrink-0">
          {icon}
        </span>
        <h3 className="text-[12px] font-bold text-wo-text-primary">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5 text-[12px] text-wo-text-muted leading-relaxed list-disc pl-4">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function VolumetricHumanOverview() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <SectionCard title="Cum se folosește acest șablon" icon={<BookOpen className="w-3.5 h-3.5" />}>
        <p className="text-[12px] text-wo-text-muted leading-relaxed">
          Acest șablon descrie cum se construiesc literele volumetrice luminoase: fața din
          plexiglas 3mm PMMA - opal, cantul din profil aluminiu, spatele din Forex, iluminarea LED și finisajul
          final.
        </p>
      </SectionCard>

      <SectionCard title="Flux de producție" icon={<Workflow className="w-3.5 h-3.5" />}>
        <BulletList
          items={[
            "Fața literelor se taie din plexiglas 3mm PMMA - opal (CNC/laser).",
            "Cantul/lateralul se realizează din profil aluminiu.",
            "Spatele este din Forex 10 mm.",
            "LED-urile se montează pe spate.",
            "Finisarea include vopsire, asamblare și verificări finale.",
          ]}
        />
      </SectionCard>

      <SectionCard title="Ce se calculează la ofertare" icon={<Calculator className="w-3.5 h-3.5" />}>
        <BulletList
          items={[
            "Materiale pe mp, ml sau buc (față plexiglas 3mm PMMA - opal, profil aluminiu, Forex, surse LED).",
            "Operații pe ml, buc sau set (tăiere, modelare, lipire, montaj LED).",
            "LED-uri estimate din perimetrul literelor.",
            "Surse LED pe buc, în funcție de configurație.",
            "Șablon de montaj din Forex 3 mm, când este cazul.",
          ]}
        />
      </SectionCard>

      <SectionCard title="Date necesare la ofertare" icon={<ClipboardList className="w-3.5 h-3.5" />}>
        <BulletList
          items={[
            "Text sau grafică (font / vector)",
            "Lățime totală a ansamblului",
            "Înălțime totală",
            "Adâncime cant (profil lateral)",
            "Suprafața feței literelor",
            "Perimetrul literelor",
            "Număr de litere",
            "Tip iluminare (față / lateral / spate)",
            "Finisaj (vopsire, colantare, RAL)",
            "Tip montaj (perete, premontaj, suport)",
          ]}
        />
      </SectionCard>
    </div>
  );
}

function GenericTemplateOverview({ description }: { description: string }) {
  return (
    <SectionCard title="Despre acest șablon" icon={<Lightbulb className="w-3.5 h-3.5" />}>
      <p className="text-[12px] text-wo-text-muted leading-relaxed">
        {description.trim() ||
          "Șablon de produs configurabil. Structura detaliată (componente, materiale, operații) se editează în tab-ul Structură produs."}
      </p>
    </SectionCard>
  );
}

export function TemplateGeneralTabPanel({
  draft,
  readOnly,
  saving,
  isNew,
  familyList,
  internalHoursLabel,
  componentCount,
  operationCount,
  materialCount,
  isArchivedForQuote,
  canArchive,
  archiveBlockReason,
  onNotesChange,
  onDescriptionChange,
  onArchive,
  onFieldChange,
}: {
  draft: DraftLike;
  readOnly: boolean;
  saving: boolean;
  isNew: boolean;
  familyList: ProductFamily[];
  internalHoursLabel: string | null;
  componentCount: number;
  operationCount: number;
  materialCount: number;
  isArchivedForQuote: boolean;
  canArchive: boolean;
  archiveBlockReason: string | null;
  onNotesChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onArchive?: () => void;
  onFieldChange?: <K extends keyof DraftLike>(key: K, value: DraftLike[K]) => void;
}) {
  const volumetric = isVolumetricLettersTemplate(draft.template_code);
  const familyLabel =
    draft.family_name.trim() ||
    familyList.find((f) => f.family_id === draft.family_id)?.label ||
    "—";
  const legacyNotes = hasLegacyTechnicalNotes(draft.notes);

  return (
    <div className="space-y-4 w-full">
      <div className="bg-gradient-to-r from-[#111827] to-[#131B2E] border border-purple-500/20 rounded-xl p-4 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <span className="w-10 h-10 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center shrink-0">
            <Package className="w-5 h-5 text-purple-300" />
          </span>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wide text-purple-400/90 mb-0.5">
              Prezentare șablon
            </p>
            <p className="text-[14px] font-bold text-wo-text-primary font-mono truncate">
              {draft.template_code || "Șablon nou"}
            </p>
            <p className="text-[12px] text-wo-text-muted truncate">{familyLabel}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle text-[11px] text-wo-text-secondary">
            <Layers className="w-3 h-3 text-purple-400" />
            {componentCount} componente
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle text-[11px] text-wo-text-secondary">
            <Workflow className="w-3 h-3 text-blue-400" />
            {operationCount} operații
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle text-[11px] text-wo-text-secondary">
            <Package className="w-3 h-3 text-emerald-400" />
            {materialCount} materiale
          </span>
        </div>
      </div>

      {volumetric ? (
        <VolumetricHumanOverview />
      ) : (
        <GenericTemplateOverview description={draft.description} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SectionCard title="Ce rămâne intern / orientativ" icon={<Clock className="w-3.5 h-3.5" />}>
          <p className="text-[12px] text-wo-text-muted leading-relaxed">{UNIT_PRICING_NOTE}</p>
          <p className="text-[12px] text-wo-text-muted leading-relaxed mt-2">
            Duratele sunt pentru verificare și planificare internă. Nu sunt baza principală de preț.
          </p>
          {internalHoursLabel ? (
            <p className="text-[11px] text-wo-text-dim mt-2">
              Estimare internă șablon: {internalHoursLabel}
            </p>
          ) : null}
          <p className="text-[10px] text-wo-text-dim mt-1">{CALIBRATION_DURATION_TOOLTIP}</p>
        </SectionCard>

        <SectionCard title="Identitate șablon" icon={<Fingerprint className="w-3.5 h-3.5" />}>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[12px]">
            <div>
              <dt className="text-wo-text-muted text-[10px] uppercase tracking-wide mb-0.5">Cod</dt>
              <dd className="font-mono text-purple-300">{draft.template_code || "—"}</dd>
            </div>
            <div>
              <dt className="text-wo-text-muted text-[10px] uppercase tracking-wide mb-0.5">Familie</dt>
              <dd className="text-wo-text-secondary">{familyLabel}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-wo-text-muted text-[10px] uppercase tracking-wide mb-1">Descriere</dt>
              <dd>
                {readOnly || !onFieldChange ? (
                  <p className="text-wo-text-muted leading-relaxed">
                    {draft.description.trim() || "—"}
                  </p>
                ) : (
                  <textarea
                    value={draft.description}
                    onChange={(e) => onDescriptionChange(e.target.value)}
                    rows={3}
                    placeholder="Descriere scurtă, vizibilă pentru echipă..."
                    className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-purple-500/50 resize-none"
                  />
                )}
              </dd>
            </div>
          </dl>
          {!readOnly && onFieldChange ? (
            <p className="text-[10px] text-wo-text-dim flex items-start gap-1.5 pt-1">
              <Info className="w-3 h-3 shrink-0 mt-0.5" />
              Codul și familia se editează din Structură produs. Pentru a scoate un șablon din
              ofertare, folosește arhivarea de mai jos.
            </p>
          ) : null}
        </SectionCard>
      </div>

      <SectionCard title="Note interne" icon={<StickyNote className="w-3.5 h-3.5" />}>
        <p className="text-[11px] text-wo-text-muted">
          Observații utile pentru producție, ofertare sau verificare. Nu apar în oferta clientului.
        </p>
        {legacyNotes ? (
          <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-900/10 border border-amber-800/25 text-[11px] text-amber-300/90">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            Conținut tehnic vechi detectat în note. Poți înlocui cu observații clare pentru echipă.
          </div>
        ) : null}
        <textarea
          value={draft.notes}
          onChange={(e) => onNotesChange(e.target.value)}
          readOnly={readOnly}
          rows={5}
          placeholder="Adaugă observații utile pentru producție, ofertare sau verificare."
          className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-purple-500/50 resize-y min-h-[100px] disabled:opacity-70"
        />
      </SectionCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SectionCard title="Legături utile" icon={<ExternalLink className="w-3.5 h-3.5" />}>
          <div className="space-y-2">
            <Link
              to="/product-system/blueprint-dossier"
              className="flex items-center gap-2.5 px-3 py-2.5 bg-wo-surface-inset border border-wo-border-subtle rounded-lg text-[12px] font-semibold text-purple-300 hover:border-purple-500/40 transition-colors"
            >
              <FileText className="w-4 h-4 shrink-0 text-purple-400" />
              Deschide dosarul tehnic (Blueprint Dossier)
            </Link>
            <Link
              to="/intake-v6/operator"
              data-testid="product-system-intake-v6-link"
              className="flex items-center gap-2.5 px-3 py-2.5 bg-wo-surface-inset border border-wo-border-subtle rounded-lg text-[12px] font-semibold text-purple-300 hover:border-purple-500/40 transition-colors"
            >
              <Inbox className="w-4 h-4 shrink-0 text-purple-400" />
              Vezi cererile Intake V6 (operator) pentru această familie
            </Link>
          </div>
        </SectionCard>

        {!isNew ? (
          <SectionCard title="Administrare șablon" icon={<Archive className="w-3.5 h-3.5" />}>
            {isArchivedForQuote ? (
              <div className="flex items-start gap-2 text-[12px] text-wo-text-muted">
                <Archive className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <p>
                  Acest șablon este <strong className="text-amber-300/90">arhivat</strong>. Nu apare
                  în fluxurile active de ofertare. Datele rămân păstrate pentru referință.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-[12px] text-wo-text-muted leading-relaxed">
                  Șablonul va fi mutat în <strong className="text-wo-text-secondary">Arhivate</strong> și nu
                  va mai apărea în fluxurile active de ofertare. Datele rămân păstrate — nu se
                  șterge nimic din sistem.
                </p>
                {archiveBlockReason ? (
                  <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-900/15 border border-amber-800/30 text-[11px] text-amber-300">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    {archiveBlockReason}
                  </div>
                ) : null}
                {onArchive ? (
                  <button
                    type="button"
                    onClick={onArchive}
                    disabled={saving || !canArchive}
                    className="flex items-center gap-1.5 px-3 py-2 bg-amber-900/25 hover:bg-amber-900/40 text-amber-200 border border-amber-700/40 rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Archive className="w-3.5 h-3.5" /> Arhivează șablon
                  </button>
                ) : null}
              </div>
            )}
          </SectionCard>
        ) : (
          <SectionCard title="Administrare șablon" icon={<Archive className="w-3.5 h-3.5" />}>
            <p className="text-[12px] text-wo-text-muted">
              Disponibil după salvarea șablonului nou.
            </p>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
