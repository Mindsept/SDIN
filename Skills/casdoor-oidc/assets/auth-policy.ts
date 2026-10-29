// Guards serveur d'exemple, pas un validateur JWT/OIDC. L'identité et les groupes
// doivent provenir d'une validation OIDC ou d'une source serveur de confiance.
export type Role = "reader" | "editor";
export type Principal = Readonly<{
  issuer: string; subject: string; tenantId: string; roles: readonly Role[];
}>;

export class AccessError extends Error {
  readonly code: "invalid_identity" | "invalid_callback" | "csrf_rejected";
  constructor(code: "invalid_identity" | "invalid_callback" | "csrf_rejected") {
    super(`Access control: ${code}`);
    this.code = code;
  }
}

export function principalFromVerifiedIdentity(
  verified: { issuer: string; subject: string; groups: readonly string[] },
  serverPolicy: {
    expectedIssuer: string; tenantId: string; groupRoles: Readonly<Record<string, Role>>;
  },
): Principal {
  if (!verified.issuer || verified.issuer !== serverPolicy.expectedIssuer ||
      !verified.subject.trim() || !serverPolicy.tenantId.trim() ||
      !Array.isArray(verified.groups) || verified.groups.some((group) => typeof group !== "string")) {
    throw new AccessError("invalid_identity");
  }
  const roles = new Set<Role>();
  for (const group of verified.groups) {
    if (!Object.hasOwn(serverPolicy.groupRoles, group)) continue;
    const role = serverPolicy.groupRoles[group];
    if (role !== "reader" && role !== "editor") throw new AccessError("invalid_identity");
    roles.add(role);
  }
  return Object.freeze({
    issuer: verified.issuer, subject: verified.subject, tenantId: serverPolicy.tenantId,
    roles: Object.freeze([...roles]),
  });
}

// Exemple produit : lecteur = ses documents ; rédacteur = documents de son tenant.
// Adapter à la règle métier réelle, et filtrer aussi les requêtes SQL en amont.
export function canAccessDocument(
  principal: Principal,
  document: { tenantId: string; ownerIssuer: string; ownerSubject: string },
  action: "read" | "edit",
): boolean {
  if (!principal.tenantId || principal.tenantId !== document.tenantId) return false;
  if (action === "edit") return principal.roles.includes("editor");
  if (action !== "read") return false;
  const own = principal.issuer === document.ownerIssuer && principal.subject === document.ownerSubject;
  return principal.roles.includes("editor") || (principal.roles.includes("reader") && own);
}

export function safeReturnPath(candidate: unknown, allowedPaths: readonly string[]): string {
  if (typeof candidate !== "string" || !candidate.startsWith("/") ||
      candidate.startsWith("//") || /[\\\r\n]/.test(candidate) ||
      /%(?:2f|5c|0a|0d)/i.test(candidate)) return "/";
  try {
    const url = new URL(candidate, "https://application.invalid");
    if (url.origin !== "https://application.invalid" || !allowedPaths.includes(url.pathname)) return "/";
    // Ne pas transporter une query/fragment qui pourrait servir de second redirect.
    return url.pathname;
  } catch { return "/"; }
}

export function assertCallbackLocation(current: URL, registeredCallback: string): void {
  let registered: URL;
  try { registered = new URL(registeredCallback); }
  catch { throw new AccessError("invalid_callback"); }
  if (current.username || current.password || current.hash ||
      registered.username || registered.password || registered.hash || registered.search ||
      current.origin !== registered.origin || current.pathname !== registered.pathname) {
    throw new AccessError("invalid_callback");
  }
  for (const name of ["state", "code", "error", "iss"]) {
    if (current.searchParams.getAll(name).length > 1) throw new AccessError("invalid_callback");
  }
  // State, nonce, code, issuer, audience, signature et PKCE restent vérifiés
  // par la transaction serveur et la bibliothèque OIDC, pas cette fonction.
}

export function assertMutationOrigin(
  requestOrigin: string | null,
  trustedOrigin: string,
  csrfValid: boolean,
): void {
  // csrfValid résulte du middleware CSRF, jamais d'un booléen du body client.
  if (!requestOrigin || requestOrigin !== trustedOrigin || !csrfValid) {
    throw new AccessError("csrf_rejected");
  }
}
