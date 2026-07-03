"""Ensure Intake V3 operator workspace sub-routes are mounted on the real FastAPI app."""

from __future__ import annotations

from main import app

REQUIRED_OPERATOR_WORKSPACE_ROUTES: tuple[str, ...] = (
    "/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
    "/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments",
    "/api/v1/intake-v3/workspaces/{workspace_id}/layer-finish-assignments/targets",
    "/api/v1/intake-v3/workspaces/{workspace_id}/lighting-plan",
)


def _registered_paths() -> set[str]:
    paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
    return paths


class TestIntakeV3OperatorWorkspaceRuntimeRoutes:
    def test_operator_workspace_subroutes_are_registered(self):
        registered = _registered_paths()
        missing = [path for path in REQUIRED_OPERATOR_WORKSPACE_ROUTES if path not in registered]
        assert not missing, f"Missing operator workspace routes on app: {missing}"

    def test_openapi_includes_layer_finish_and_lighting_paths(self):
        schema = app.openapi()
        paths = set(schema.get("paths", {}).keys())
        for path in REQUIRED_OPERATOR_WORKSPACE_ROUTES:
            assert path in paths, f"OpenAPI missing route: {path}"
