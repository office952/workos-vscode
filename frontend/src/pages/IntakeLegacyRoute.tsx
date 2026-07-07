import { Navigate, useParams } from "react-router-dom";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";

/**
 * Legacy /intake/:id entry is retired from the active flow.
 * Any direct request link now bridges into Intake V6.
 */
export default function IntakeLegacyRoute() {
  const { id } = useParams<{ id: string }>();
  return <Navigate to={buildIntakeV6Path(id)} replace />;
}
