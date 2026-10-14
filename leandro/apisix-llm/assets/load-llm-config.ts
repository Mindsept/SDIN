// Exemple serveur limité au contrat KV v2 du TD ; réutiliser le loader de l'app
// s'il existe. Aucun accès à secret/core/<provider> ni aux maps globales.
import { LlmGatewayError } from "./llm-client.ts";
import type { LlmConfig } from "./llm-client.ts";

export async function loadLlmConfig(
  options: { app: string; vaultAddr: string; vaultToken: string },
  transport: typeof fetch = fetch,
): Promise<LlmConfig> {
  if (!/^[a-z][a-z0-9-]*$/.test(options.app) || !options.vaultToken.trim() ||
      /[\r\n]/.test(options.vaultToken)) throw new LlmGatewayError("configuration");
  const allowed = new Set(["http://openbao.internal:8200", "http://localhost:8200"]);
  const address = options.vaultAddr.replace(/\/$/, "");
  if (!allowed.has(address)) throw new LlmGatewayError("configuration");
  try {
    const response = await transport(`${address}/v1/secret/data/${options.app}/llm`, {
      headers: { "X-Vault-Token": options.vaultToken },
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      await response.body?.cancel();
      throw new LlmGatewayError("configuration", response.status);
    }
    const document = await response.json();
    const data = document?.data?.data;
    if (typeof data?.base_url !== "string" || typeof data?.virtual_key !== "string" ||
        !data.virtual_key.trim()) throw new LlmGatewayError("configuration");
    // La destination et la vkey sont également validées par createTextGateway.
    return { baseUrl: data.base_url, virtualKey: data.virtual_key };
  } catch (error) {
    if (error instanceof LlmGatewayError) throw error;
    throw new LlmGatewayError("configuration");
  }
}
