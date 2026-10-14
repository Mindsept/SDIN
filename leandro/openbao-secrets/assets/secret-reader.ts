// Lecteur serveur KV v2 : un seul appel GET, aucun provisioning ou fallback.
export type SecretErrorCode = "configuration" | "forbidden_path" | "access_denied"
  | "not_found" | "unavailable" | "invalid_secret" | "cancelled";

export class SecretReadError extends Error {
  readonly code: SecretErrorCode;
  readonly status?: number;
  constructor(code: SecretErrorCode, status?: number) {
    super(`Secret store: ${code}`);
    this.name = "SecretReadError";
    this.code = code;
    this.status = status;
  }
}

const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const segment = (value: unknown): value is string =>
  typeof value === "string" && /^[a-z][a-z0-9-]*$/.test(value);

export function createSecretReader(options: {
  app: string;
  address: string;
  token: string;
  allowedSecrets: readonly string[];
  allowLocalHttp?: boolean;
  // Liste fournie par l'opérateur, jamais depuis une requête utilisateur.
  approvedHttpsOrigins?: readonly string[];
  timeoutMs?: number;
  maxResponseBytes?: number;
}, transport: typeof fetch = fetch) {
  const { app, token } = options;
  const address = options.address.replace(/\/$/, "");
  const allowed = new Set(options.allowedSecrets);
  const timeout = options.timeoutMs ?? 5000;
  const maxBytes = options.maxResponseBytes ?? 65536;
  let url: URL;
  try { url = new URL(address); } catch { throw new SecretReadError("configuration"); }
  const httpsApproved = url.protocol === "https:" &&
    (options.approvedHttpsOrigins ?? []).includes(url.origin);
  const localHttp = options.allowLocalHttp === true &&
    ["http://openbao.internal:8200", "http://localhost:8200"].includes(address);
  if (!segment(app) || app === "core" || !token.trim() || /[\r\n]/.test(token) ||
      url.username || url.password || url.search || url.hash || url.pathname !== "/" ||
      (!httpsApproved && !localHttp) || !allowed.size ||
      [...allowed].some((name) => !segment(name)) ||
      !Number.isSafeInteger(timeout) || timeout < 1 ||
      !Number.isSafeInteger(maxBytes) || maxBytes < 1) {
    throw new SecretReadError("configuration");
  }
  return {
    async read(name: string, cancellation?: AbortSignal): Promise<{
      values: Readonly<Record<string, unknown>>; version: number;
    }> {
      if (!segment(name) || !allowed.has(name)) throw new SecretReadError("forbidden_path");
      if (cancellation?.aborted) throw new SecretReadError("cancelled");
      const deadline = AbortSignal.timeout(timeout);
      const signal = cancellation ? AbortSignal.any([deadline, cancellation]) : deadline;
      try {
        const response = await transport(`${address}/v1/secret/data/${app}/${name}`, {
          method: "GET", redirect: "error", headers: { "X-Vault-Token": token }, signal,
        });
        if (!response.ok) {
          await response.body?.cancel();
          const status = response.status;
          throw new SecretReadError(status === 401 || status === 403 ? "access_denied"
            : status === 404 ? "not_found" : "unavailable", status);
        }
        if (!response.body) throw new SecretReadError("invalid_secret");
        const reader = response.body.getReader();
        const chunks: Uint8Array[] = [];
        let size = 0;
        try {
          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            size += value.byteLength;
            if (size > maxBytes) {
              await reader.cancel();
              throw new SecretReadError("invalid_secret");
            }
            chunks.push(value);
          }
        } finally { reader.releaseLock(); }
        const bytes = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
        let body: unknown;
        try { body = JSON.parse(new TextDecoder().decode(bytes)); }
        catch { throw new SecretReadError("invalid_secret"); }
        if (!record(body) || !record(body.data) || !record(body.data.data) ||
            !record(body.data.metadata)) throw new SecretReadError("invalid_secret");
        const metadata = body.data.metadata;
        const version = metadata.version;
        if (typeof version !== "number" || !Number.isSafeInteger(version) || version < 1 ||
            metadata.destroyed === true ||
            (typeof metadata.deletion_time === "string" && metadata.deletion_time !== "")) {
          throw new SecretReadError("invalid_secret");
        }
        return { values: Object.freeze({ ...body.data.data }), version };
      } catch (error) {
        if (cancellation?.aborted) throw new SecretReadError("cancelled");
        if (error instanceof SecretReadError) throw error;
        // Ne pas copier le corps d'erreur ou l'exception réseau contenant un token.
        throw new SecretReadError("unavailable");
      }
    },
  };
}
