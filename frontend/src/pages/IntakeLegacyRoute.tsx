import { Loader2 } from "lucide-react";
import { Navigate, useParams } from "react-router-dom";
import { useBackendData } from "@/hooks/useBackendData";
import {
  buildIntakeV6Path,
  shouldUseVolumetricIntakePage,
} from "@/lib/volumetricIntakeRoute";
import IntakeDetail from "./IntakeDetail";

/**
 * Legacy /intake/:id entry — redirects volumetric intakes to Intake V6.
 * Non-volumetric intakes still render IntakeDetail.
 */
export default function IntakeLegacyRoute() {
  const { id } = useParams<{ id: string }>();
  const { intakes, loading } = useBackendData();
  const request = intakes.find((r) => r.id === id);

  if (loading && !request) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Se încarcă…
      </div>
    );
  }

  if (
    request &&
    shouldUseVolumetricIntakePage(
      request.confirmedTemplateCode,
      request.productFamily
    )
  ) {
    return <Navigate to={buildIntakeV6Path(id)} replace />;
  }

  return <IntakeDetail />;
}
