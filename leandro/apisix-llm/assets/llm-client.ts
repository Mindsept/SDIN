// Exemple serveur TypeScript/Bun : chat texte JSON, une tentative, aucun SDK.
// Adapter les limites au cas d'usage ; ne pas importer dans le frontend.
export type TextTask = "task:cheap" | "task:quality" | "task:reasoning";
export type LlmConfig = { baseUrl: string; virtualKey: string };
export type TextPolicy = {
  outputTokens: Partial<Record<TextTask, number>>;
  maxInputChars: number;
  maxResponseBytes: number;
  timeoutMs: number;
};
export type ErrorCode =
  | "configuration" | "invalid_request" | "access_denied" | "rate_limited"
  | "unavailable" | "deadline_exceeded" | "cancelled"
  | "invalid_response" | "incomplete_response";

export class LlmGatewayError extends Error {
  readonly code: ErrorCode;
  readonly status?: number;

  constructor(code: ErrorCode, status?: number) {
    // Ne pas recopier le corps HTTP, les headers ou l'erreur réseau sous-jacente.
    super(`LLM gateway: ${code}`);
    this.name = "LlmGatewayError";
    this.code = code;
    this.status = status;
  }
}

// Liste fermée pour la plateforme de dev. En production : gateways approuvés
// en HTTPS dans une configuration opérateur, jamais une URL choisie par l'usager.
const GATEWAYS = new Set([
  "http://llm.internal:9080/v1",
  "http://localhost:9080/v1",
]);
const TASKS = new Set<TextTask>(["task:cheap", "task:quality", "task:reasoning"]);
const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const positiveInteger = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value > 0;

export function createTextGateway(
  config: LlmConfig,
  policy: TextPolicy,
  transport: typeof fetch = fetch,
) {
  // Capturer les valeurs validées : une mutation ultérieure de config/policy
  // ne doit pas déplacer le gateway ni changer les limites.
  const baseUrl = config.baseUrl;
  const virtualKey = config.virtualKey;
  const limits = { ...policy.outputTokens };
  const { maxInputChars, maxResponseBytes, timeoutMs } = policy;
  if (!GATEWAYS.has(baseUrl) || typeof virtualKey !== "string" ||
      !virtualKey.trim() || /[\r\n]/.test(virtualKey) ||
      ![maxInputChars, maxResponseBytes, timeoutMs].every(positiveInteger) ||
      Object.keys(limits).length === 0 ||
      Object.entries(limits).some(([task, limit]) =>
        !TASKS.has(task as TextTask) || !positiveInteger(limit))) {
    throw new LlmGatewayError("configuration");
  }

  return {
    async completeText(request: {
      task: TextTask;
      system: string;
      input: string;
      signal?: AbortSignal;
    }): Promise<{ text: string; usage?: { totalTokens: number } }> {
      const maxTokens = Object.hasOwn(limits, request.task) ? limits[request.task] : undefined;
      if (!positiveInteger(maxTokens) || typeof request.system !== "string" ||
          typeof request.input !== "string" || !request.input.trim() ||
          request.system.length + request.input.length > maxInputChars) {
        throw new LlmGatewayError("invalid_request");
      }
      if (request.signal?.aborted) throw new LlmGatewayError("cancelled");
      const deadline = AbortSignal.timeout(timeoutMs);
      const signal = request.signal ? AbortSignal.any([deadline, request.signal]) : deadline;
      try {
        const response = await transport(`${baseUrl}/chat/completions`, {
          method: "POST",
          redirect: "error",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${virtualKey}`,
          },
          // Aucun spread d'un objet utilisateur et aucun header d'auth utilisateur.
          body: JSON.stringify({
            model: request.task,
            max_tokens: maxTokens,
            stream: false,
            messages: [
              { role: "system", content: request.system },
              { role: "user", content: request.input },
            ],
          }),
          signal,
        });
        if (!response.ok) {
          await response.body?.cancel();
          const status = response.status;
          const code: ErrorCode = status === 401 || status === 403 ? "access_denied"
            : status === 429 ? "rate_limited"
            : status >= 400 && status < 500 ? "invalid_request" : "unavailable";
          throw new LlmGatewayError(code, status);
        }

        // Borner la mémoire de réponse, même si Content-Length est absent.
        if (!response.body) throw new LlmGatewayError("invalid_response");
        const reader = response.body.getReader();
        const chunks: Uint8Array[] = [];
        let size = 0;
        try {
          for (;;) {
            const chunk = await reader.read();
            if (chunk.done) break;
            size += chunk.value.byteLength;
            if (size > maxResponseBytes) {
              await reader.cancel();
              throw new LlmGatewayError("invalid_response");
            }
            chunks.push(chunk.value);
          }
        } finally {
          reader.releaseLock();
        }
        const bytes = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
        let data: unknown;
        try { data = JSON.parse(new TextDecoder().decode(bytes)); }
        catch { throw new LlmGatewayError("invalid_response"); }
        const choice = record(data) && Array.isArray(data.choices) ? data.choices[0] : undefined;
        if (!record(choice) || typeof choice.finish_reason !== "string") {
          throw new LlmGatewayError("invalid_response");
        }
        if (choice.finish_reason !== "stop") throw new LlmGatewayError("incomplete_response");
        if (!record(choice.message) || typeof choice.message.content !== "string" ||
            !choice.message.content.trim()) throw new LlmGatewayError("invalid_response");
        const total = record(data) && record(data.usage) ? data.usage.total_tokens : undefined;
        const usage = typeof total === "number" && Number.isSafeInteger(total) && total >= 0
          ? { totalTokens: total } : undefined;
        return { text: choice.message.content, usage };
      } catch (error) {
        if (signal.aborted) {
          throw new LlmGatewayError(request.signal?.aborted ? "cancelled" : "deadline_exceeded");
        }
        if (error instanceof LlmGatewayError) throw error;
        throw new LlmGatewayError("unavailable");
      }
    },
  };
}
