/**
 * BUILD 17 — Roles, Permissions & Operator Safety.
 * BUILD 24 — RBAC Authorization Parity Hardening (P1-002).
 *
 * Roles (aligned with backend):
 *  - operator : shop-floor view, can start/complete/block tasks, no pricing/config access
 *  - manager  : full operational + commercial (intake/quotes/orders/inventory)
 *  - sales    : intake, quotes, orders (create), reports (no profit)
 *  - admin    : all permissions + settings, user mgmt
 *  - viewer   : read-only fallback
 *
 * Role resolution order (BUILD 24 hardening):
 *   1. Backend-provided role from /api/v1/auth/me (authoritative)
 *   2. In dev/local/test only: "user" -> "admin" for backward compat
 *   3. In staging/production: "user" -> "viewer" (fail-closed)
 *   4. Unknown -> "viewer" (fail-closed)
 *   5. Email-like values -> "viewer" in non-dev (was "manager" — over-permissive)
 */

export type Role = "operator" | "manager" | "sales" | "admin" | "viewer";

export type Permission =
  // Dashboard
  | "view:dashboard"
  // Shop Floor
  | "view:shopfloor"
  // Operator
  | "view:operator"
  | "action:task_start"
  | "action:task_complete"
  | "action:task_block"
  // Intake
  | "view:intake"
  | "edit:intake"
  // Quotes
  | "view:quotes"
  | "edit:quotes"
  | "accept:quote"
  | "view:quote_cost"
  // Orders
  | "view:orders"
  | "edit:orders"
  | "lock:order"
  | "create:order_from_quote"
  // Inventory
  | "view:inventory"
  | "edit:inventory"
  | "action:deduct_stock"
  | "view:stock_movements"
  // Reports
  | "view:reports"
  | "view:reports_profit"
  // Settings
  | "view:settings"
  | "edit:settings"
  // Governance
  | "view:governance"
  // Modules
  | "view:modules"
  // Wave 0 — shell nav surfaces (route URLs unchanged)
  | "view:products"
  | "view:execution"
  | "view:clients"
  | "view:documents"
  | "view:employees"
  | "view:hr"
  | "view:payments"
  | "view:advances"
  | "view:colaboratori"
  | "view:utilaje"
  | "view:pricing"
  // Reality Quality (BUILD 18)
  | "reality.invalidate"
  | "reality.restore_valid";

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  viewer: ["view:dashboard"],

  operator: [
    // U7: operator production home is Atelier (/shop-floor); Control producție is management.
    "view:shopfloor",
    "view:operator",
    "action:task_start",
    "action:task_complete",
    "action:task_block",
    "view:inventory",
    "view:stock_movements",
    "view:utilaje",
  ],

  sales: [
    "view:dashboard",
    "view:intake",
    "edit:intake",
    "view:products",
    "view:quotes",
    "edit:quotes",
    "accept:quote",
    "view:orders",
    "create:order_from_quote",
    "view:execution",
    "view:clients",
    "view:documents",
    "view:inventory",
    "view:stock_movements",
    "view:reports",
  ],

  manager: [
    "view:dashboard",
    "view:shopfloor",
    "view:operator",
    "action:task_start",
    "action:task_complete",
    "action:task_block",
    "view:intake",
    "edit:intake",
    "view:products",
    "view:quotes",
    "edit:quotes",
    "accept:quote",
    "view:quote_cost",
    "view:orders",
    "edit:orders",
    "lock:order",
    "create:order_from_quote",
    "view:execution",
    "view:clients",
    "view:documents",
    "view:inventory",
    "edit:inventory",
    "action:deduct_stock",
    "view:stock_movements",
    "view:utilaje",
    "view:colaboratori",
    "view:employees",
    "view:hr",
    "view:payments",
    "view:reports",
    "view:reports_profit",
    "reality.invalidate",
  ],

  admin: [
    "view:dashboard",
    "view:shopfloor",
    "view:operator",
    "action:task_start",
    "action:task_complete",
    "action:task_block",
    "view:intake",
    "edit:intake",
    "view:products",
    "view:quotes",
    "edit:quotes",
    "accept:quote",
    "view:quote_cost",
    "view:orders",
    "edit:orders",
    "lock:order",
    "create:order_from_quote",
    "view:execution",
    "view:clients",
    "view:documents",
    "view:inventory",
    "edit:inventory",
    "action:deduct_stock",
    "view:stock_movements",
    "view:utilaje",
    "view:colaboratori",
    "view:employees",
    "view:hr",
    "view:payments",
    "view:advances",
    "view:pricing",
    "view:reports",
    "view:reports_profit",
    "view:settings",
    "edit:settings",
    "view:governance",
    "view:modules",
    "reality.invalidate",
    "reality.restore_valid",
  ],
};

/**
 * BUILD 24 — Environment-aware dev auth detection for frontend role resolution.
 *
 * Returns true ONLY when BOTH conditions are met:
 *   1. VITE_ENABLE_DEV_AUTH === "true" (dev auth explicitly enabled)
 *   2. NOT a production build (import.meta.env.PROD is false)
 *
 * In production builds (.env.production sets VITE_ENABLE_DEV_AUTH=false),
 * this always returns false — fail-closed.
 */
function isDevEnvironment(): boolean {
  // Production builds: VITE_ENABLE_DEV_AUTH is "false" and import.meta.env.PROD is true
  if (import.meta.env.PROD) return false;
  return import.meta.env.VITE_ENABLE_DEV_AUTH === "true";
}

// Dev-only fallback: "user" -> "admin" (backward compat, dev only)
const _ROLE_FALLBACK_MAP_DEV: Record<string, Role> = {
  user: "admin",
};

// Production fallback: "user" -> "viewer" (fail-closed)
const _ROLE_FALLBACK_MAP_PROD: Record<string, Role> = {
  user: "viewer",
};

/**
 * Resolve a raw role string to a valid Role.
 *
 * BUILD 24 hardening:
 * - In dev: "user" → "admin", email-like → "manager" (backward compat)
 * - In staging/production: "user" → "viewer", email-like → "viewer" (fail-closed)
 * - Unknown always → "viewer"
 */
export function resolveRole(roleOrEmail?: string | null): Role {
  if (!roleOrEmail) return "viewer";

  // Check if it's a valid role directly
  const lower = roleOrEmail.toLowerCase();
  if (lower in ROLE_PERMISSIONS) return lower as Role;

  // Select fallback map based on environment
  const fallbackMap = isDevEnvironment()
    ? _ROLE_FALLBACK_MAP_DEV
    : _ROLE_FALLBACK_MAP_PROD;

  const mapped = fallbackMap[lower];
  if (mapped) return mapped;

  // Legacy: if it looks like an email
  if (roleOrEmail.includes("@")) {
    // BUILD 24: only grant manager in dev, fail-closed to viewer in prod
    if (isDevEnvironment()) return "manager";
    return "viewer";
  }

  return "viewer";
}

export function can(role: Role, permission: Permission): boolean {
  const perms = ROLE_PERMISSIONS[role];
  if (!perms) return false;
  return perms.includes(permission);
}

/**
 * Check multiple permissions — returns true if ALL are granted.
 */
export function canAll(role: Role, permissions: Permission[]): boolean {
  return permissions.every((p) => can(role, p));
}

/**
 * Check multiple permissions — returns true if ANY is granted.
 */
export function canAny(role: Role, permissions: Permission[]): boolean {
  return permissions.some((p) => can(role, p));
}

/**
 * Get all permissions for a role.
 */
export function getPermissions(role: Role): Permission[] {
  return ROLE_PERMISSIONS[role] || [];
}

/**
 * Navigation items visibility per role.
 * Unknown keys fail closed (no entry → not visible).
 */
export type NavItem =
  | "dashboard"
  | "shopfloor"
  | "operator"
  | "tablet"
  | "execution"
  | "ops_graph"
  | "intake"
  | "products"
  | "quotes"
  | "orders"
  | "clients"
  | "documents"
  | "inventory"
  | "pricing"
  | "utilaje"
  | "colaboratori"
  | "employees"
  | "employees_records"
  | "attendance"
  | "payments"
  | "advances"
  | "reports"
  | "settings"
  | "modules"
  | "governance"
  | "demos";

const NAV_PERMISSION_MAP: Partial<Record<NavItem, Permission>> = {
  dashboard: "view:dashboard",
  shopfloor: "view:shopfloor",
  operator: "view:operator",
  tablet: "view:shopfloor",
  execution: "view:execution",
  ops_graph: "view:execution",
  intake: "view:intake",
  products: "view:products",
  quotes: "view:quotes",
  orders: "view:orders",
  clients: "view:clients",
  documents: "view:documents",
  inventory: "view:inventory",
  pricing: "view:pricing",
  utilaje: "view:utilaje",
  colaboratori: "view:colaboratori",
  employees: "view:employees",
  employees_records: "view:hr",
  attendance: "view:hr",
  payments: "view:payments",
  advances: "view:advances",
  reports: "view:reports",
  settings: "view:settings",
  modules: "view:modules",
  governance: "view:governance",
  // demos: gated by isDevEnvironment() in canViewNav (not a Permission)
};

/**
 * Wave 0 — unknown nav keys and missing permissions fail closed.
 * DEV tooling (`demos`) is visible only when VITE_ENABLE_DEV_AUTH is on (non-prod).
 * Ops-Graph stays under Planificare but is manager/admin only.
 */
export function canViewNav(role: Role, navItem: NavItem | string): boolean {
  if (!(role in ROLE_PERMISSIONS)) return false;

  // U7: diagnostic/demo chrome only for admin when DEV auth is on — never for viewer/operator/sales.
  if (navItem === "demos") {
    return isDevEnvironment() && role === "admin";
  }

  if (navItem === "ops_graph") {
    return (
      (role === "manager" || role === "admin") && can(role, "view:execution")
    );
  }

  if (!(navItem in NAV_PERMISSION_MAP)) return false;
  const requiredPermission = NAV_PERMISSION_MAP[navItem as NavItem];
  if (!requiredPermission) return false;
  return can(role, requiredPermission);
}

const ALL_NAV_ITEMS: NavItem[] = [
  "dashboard",
  "shopfloor",
  "operator",
  "tablet",
  "execution",
  "ops_graph",
  "intake",
  "products",
  "quotes",
  "orders",
  "clients",
  "documents",
  "inventory",
  "pricing",
  "utilaje",
  "colaboratori",
  "employees",
  "employees_records",
  "attendance",
  "payments",
  "advances",
  "reports",
  "settings",
  "modules",
  "governance",
  "demos",
];

/**
 * Get visible nav items for a role.
 */
export function getVisibleNavItems(role: Role): NavItem[] {
  return ALL_NAV_ITEMS.filter((item) => canViewNav(role, item));
}