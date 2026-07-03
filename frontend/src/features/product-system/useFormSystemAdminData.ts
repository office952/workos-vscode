import { useEffect, useState } from "react";
import {
  getProductDefinitionPreview,
  ProductDefinitionPreviewNotFoundError,
  type ProductDefinitionPreview,
} from "@/api/productDefinitionPreview";
import { getIntakeV6ModularFormContract } from "@/lib/intakeV6/intakeV6Api";
import type { IntakeV6ModularFormContractResponse } from "@/lib/intakeV6/intakeV6ModularFormContractTypes";

export type FormSystemAdminLoadStatus = "idle" | "loading" | "ready" | "unavailable";

export function useFormSystemAdminData(templateCode: string | null | undefined) {
  const [preview, setPreview] = useState<ProductDefinitionPreview | null>(null);
  const [formContract, setFormContract] = useState<IntakeV6ModularFormContractResponse | null>(null);
  const [status, setStatus] = useState<FormSystemAdminLoadStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = templateCode?.trim();
    if (!code) {
      setPreview(null);
      setFormContract(null);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    Promise.all([
      getProductDefinitionPreview(code),
      getIntakeV6ModularFormContract(code).catch(() => null),
    ])
      .then(([pd, contract]) => {
        if (cancelled) return;
        setPreview(pd);
        setFormContract(contract);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setPreview(null);
        setFormContract(null);
        setStatus("unavailable");
        if (err instanceof ProductDefinitionPreviewNotFoundError) {
          setError("ProductDefinition preview indisponibil pentru acest template.");
        } else {
          setError(err instanceof Error ? err.message : "Eroare la încărcarea Form System.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  return { preview, formContract, status, error, isLoading: status === "loading" };
}
