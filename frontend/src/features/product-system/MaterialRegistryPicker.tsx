import { useMemo, useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import type { InventoryMaterialEntity } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  formatMaterialRegistryShortName,
  sortMaterialsForPicker,
  splitMaterialsForPickerGroups,
} from "@/features/product-system/materialRegistryDisplay";

/** Hover/focus row — semantic hover wash, same family as app panels. */
const PICKER_ITEM =
  "data-[selected=true]:!bg-wo-hover data-[selected=true]:!text-wo-text-primary aria-selected:!bg-wo-hover aria-selected:!text-wo-text-primary";

const PICKER_COMMAND =
  "[&_[cmdk-group-heading]]:text-wo-text-muted [&_[cmdk-input]]:bg-wo-surface-inset [&_[cmdk-input]]:text-wo-text-primary";

type MaterialRegistryPickerProps = {
  materials: InventoryMaterialEntity[];
  value: string;
  onValueChange: (code: string) => void;
  componentId?: string;
  templateCode?: string;
  unknownCode?: string;
  disabled?: boolean;
  className?: string;
};

export function MaterialRegistryPicker({
  materials,
  value,
  onValueChange,
  componentId,
  templateCode,
  unknownCode,
  disabled = false,
  className,
}: MaterialRegistryPickerProps) {
  const [open, setOpen] = useState(false);
  const sorted = useMemo(
    () => sortMaterialsForPicker(materials, componentId, templateCode),
    [materials, componentId, templateCode]
  );
  const { suggested, other } = useMemo(
    () => splitMaterialsForPickerGroups(materials, componentId, templateCode),
    [materials, componentId, templateCode]
  );

  const selected = materials.find((m) => m.code === value);
  const selectedShort = selected
    ? formatMaterialRegistryShortName(selected.name)
    : value
      ? formatMaterialRegistryShortName(unknownCode ?? value)
      : null;

  const renderItem = (mat: InventoryMaterialEntity) => {
    const short = formatMaterialRegistryShortName(mat.name);
    return (
      <CommandItem
        key={mat.id}
        value={`${mat.code} ${mat.name} ${short}`}
        onSelect={() => {
          onValueChange(mat.code);
          setOpen(false);
        }}
        className={cn("flex items-start gap-2 py-2", PICKER_ITEM)}
      >
        <Check
          className={cn(
            "mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400",
            value === mat.code ? "opacity-100" : "opacity-0"
          )}
        />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-[11px] font-bold text-emerald-300 leading-tight">
            {mat.code}
          </p>
          <p className="text-[10px] text-wo-text-secondary leading-snug mt-0.5">{short}</p>
          <p className="text-[9px] text-wo-text-muted font-mono mt-0.5">{mat.unit}</p>
        </div>
      </CommandItem>
    );
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "flex-[2] h-auto min-h-9 justify-between gap-2 px-2 py-1.5",
            "bg-wo-surface-inset border-wo-border-strong hover:bg-wo-surface-raised hover:border-emerald-600/40",
            "text-left font-normal",
            className
          )}
        >
          {value ? (
            <div className="min-w-0 flex-1">
              <p className="font-mono text-[11px] font-bold text-emerald-300 truncate">
                {value}
              </p>
              <p className="text-[10px] text-wo-text-muted truncate">{selectedShort}</p>
            </div>
          ) : (
            <span className="text-[11px] text-wo-text-muted">— alege material —</span>
          )}
          <ChevronsUpDown className="h-3.5 w-3.5 shrink-0 text-wo-text-muted" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className="w-[min(calc(100vw-2rem),22rem)] p-0 bg-wo-surface-inset border-wo-border-strong text-wo-text-primary shadow-xl"
      >
        <Command className={cn("bg-wo-surface-inset text-wo-text-primary", PICKER_COMMAND)}>
          <CommandInput
            placeholder="Caută cod sau nume…"
            className="h-9 text-[12px] border-wo-border-strong placeholder:text-wo-text-muted"
          />
          <CommandList className="max-h-[min(50vh,280px)]">
            <CommandGroup>
              <CommandItem
                value="__clear__"
                onSelect={() => {
                  onValueChange("");
                  setOpen(false);
                }}
                className={cn("py-2 text-wo-text-muted", PICKER_ITEM)}
              >
                — fără material —
              </CommandItem>
            </CommandGroup>
            <CommandEmpty className="py-4 text-[11px] text-wo-text-muted">
              Niciun material găsit.
            </CommandEmpty>
            {suggested.length > 0 ? (
              <>
                <CommandGroup heading="Relevante pentru componentă">
                  {suggested.map(renderItem)}
                </CommandGroup>
                {other.length > 0 ? <CommandSeparator className="bg-[#334155]" /> : null}
              </>
            ) : null}
            <CommandGroup heading={suggested.length > 0 ? "Toate materialele" : undefined}>
              {(suggested.length > 0 ? other : sorted).map(renderItem)}
            </CommandGroup>
            {value && !selected ? (
              <CommandGroup heading="Șablon">
                <CommandItem
                  value={value}
                  onSelect={() => setOpen(false)}
                  className={cn("py-2", PICKER_ITEM)}
                >
                  <p className="font-mono text-[11px] text-amber-300">{value}</p>
                  <p className="text-[10px] text-wo-text-muted">Necunoscut în registru</p>
                </CommandItem>
              </CommandGroup>
            ) : null}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
