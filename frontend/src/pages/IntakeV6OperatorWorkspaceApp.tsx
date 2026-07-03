import { useParams } from "react-router-dom";
import IntakeV6OperatorWorkspace from "@/components/workos/intake-v6/IntakeV6OperatorWorkspace";
import IntakeV6OperatorWorkspaceFileDrop from "@/components/workos/intake-v6/IntakeV6OperatorWorkspaceFileDrop";
import OperatorWorkspaceFontLoader from "@/components/workos/shared/OperatorWorkspaceFontLoader";
import { useIntakeV6Workspace } from "@/lib/intakeV6/useIntakeV6Workspace";

export default function IntakeV6OperatorWorkspaceApp() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const hook = useIntakeV6Workspace(workspaceId);

  return (
    <>
      <OperatorWorkspaceFontLoader />
      <div data-testid="intake-v6-operator-workspace-app" className="min-h-full">
        <IntakeV6OperatorWorkspaceFileDrop
          workspaceId={hook.state.workspace?.id ?? workspaceId}
          workspaceLoaded={Boolean(hook.state.workspace)}
          disabled={!hook.canImportSvg}
          onFileSelected={(file) => hook.importSvgFile(file)}
        >
          <IntakeV6OperatorWorkspace hook={hook} />
        </IntakeV6OperatorWorkspaceFileDrop>
      </div>
    </>
  );
}
