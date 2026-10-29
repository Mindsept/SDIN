// Tests du contrat applicatif, pas d'une instance APISIX. Aucun appel externe.
import assert from "node:assert/strict";
import { test } from "node:test";
import { createTextGateway, LlmGatewayError } from "./llm-client.ts";
import type { ErrorCode, TextPolicy } from "./llm-client.ts";
import { loadLlmConfig } from "./load-llm-config.ts";

const config = { baseUrl: "http://llm.internal:9080/v1", virtualKey: "fake-app-vkey" };
const policy: TextPolicy = {
  outputTokens: { "task:cheap": 256 }, maxInputChars: 8000,
  maxResponseBytes: 65536, timeoutMs: 1000,
};
const request = { task: "task:cheap" as const, system: "Résumé", input: "Document" };
const successful = (finish = "stop") => Response.json({
  choices: [{ finish_reason: finish, message: { content: "Un résumé." } }],
  usage: { total_tokens: 23 },
});
const hasCode = (code: ErrorCode) => (error: unknown) =>
  error instanceof LlmGatewayError && error.code === code;

test("une requête utilise la vkey, l'alias et les limites serveur sans champs injectés", async () => {
  let calls = 0;
  const transport = (async (url, init) => {
    calls++;
    assert.equal(url, "http://llm.internal:9080/v1/chat/completions");
    assert.equal(init?.redirect, "error");
    assert.equal(new Headers(init?.headers).get("Authorization"), "Bearer fake-app-vkey");
    const body = JSON.parse(String(init?.body));
    assert.equal(body.model, "task:cheap");
    assert.equal(body.max_tokens, 256);
    assert.equal(body.stream, false);
    assert.equal(body.api_key, undefined);
    return successful();
  }) as typeof fetch;
  const client = createTextGateway(config, policy, transport);
  const result = await client.completeText({ ...request, model: "unapproved", max_tokens: 90000 } as typeof request);
  assert.deepEqual(result, { text: "Un résumé.", usage: { totalTokens: 23 } });
  assert.equal(calls, 1);
});

test("une URL fournisseur ou une clé absente sont refusées avant toute requête", () => {
  for (const invalid of [
    { ...config, baseUrl: "https://api.openai.com/v1" },
    { ...config, virtualKey: "" },
    { ...config, baseUrl: "http://llm.internal:9080/v1?redirect=other" },
  ]) assert.throws(() => createTextGateway(invalid, policy), hasCode("configuration"));
});

test("les modèles bruts, aliases non autorisés et entrées longues n'appellent pas le réseau", async () => {
  let calls = 0;
  const transport = (async () => { calls++; return successful(); }) as typeof fetch;
  const client = createTextGateway(config, policy, transport);
  for (const invalid of [
    { ...request, task: "gpt-unapproved" },
    { ...request, task: "task:quality" },
    { ...request, input: "x".repeat(8001) },
  ]) await assert.rejects(client.completeText(invalid as typeof request), hasCode("invalid_request"));
  assert.equal(calls, 0);
});

test("une mutation de configuration ne change pas la destination ou le plafond capturés", async () => {
  const mutableConfig = { ...config };
  const mutablePolicy = { ...policy, outputTokens: { "task:cheap": 256 } };
  const client = createTextGateway(mutableConfig, mutablePolicy, (async (url, init) => {
    assert.equal(url, "http://llm.internal:9080/v1/chat/completions");
    assert.equal(JSON.parse(String(init?.body)).max_tokens, 256);
    return successful();
  }) as typeof fetch);
  mutableConfig.baseUrl = "https://api.openai.com/v1";
  mutablePolicy.outputTokens["task:cheap"] = 999999;
  await client.completeText(request);
});

for (const [status, code] of [
  [401, "access_denied"], [403, "access_denied"], [429, "rate_limited"],
  [400, "invalid_request"], [503, "unavailable"], [302, "unavailable"],
] as const) {
  test(`HTTP ${status} : erreur typée, sans corps sensible, retry ou fallback`, async () => {
    let calls = 0;
    const client = createTextGateway(config, policy, (async () => {
      calls++;
      return new Response("fake-secret-and-private-prompt", { status });
    }) as typeof fetch);
    await assert.rejects(client.completeText(request), (error: unknown) => {
      assert.ok(error instanceof LlmGatewayError);
      assert.equal(error.code, code);
      assert.equal(error.status, status);
      assert.ok(!String(error).includes("fake-secret"));
      return true;
    });
    assert.equal(calls, 1);
  });
}

test("une erreur réseau n'expose pas les credentials de son message", async () => {
  const client = createTextGateway(config, policy, (async () => {
    throw new Error("fake-app-vkey in upstream details");
  }) as typeof fetch);
  await assert.rejects(client.completeText(request), (error: unknown) => {
    assert.ok(hasCode("unavailable")(error));
    assert.ok(!String(error).includes("fake-app-vkey"));
    return true;
  });
});

test("une sortie tronquée ou non textuelle n'est pas un succès", async () => {
  for (const response of [successful("length"), successful("tool_calls")]) {
    const client = createTextGateway(config, policy, (async () => response) as typeof fetch);
    await assert.rejects(client.completeText(request), hasCode("incomplete_response"));
  }
  const client = createTextGateway(config, policy, (async () => Response.json({ choices: [] })) as typeof fetch);
  await assert.rejects(client.completeText(request), hasCode("invalid_response"));
});

test("une réponse volumineuse ou un JSON invalide sont rejetés", async () => {
  for (const body of ["x".repeat(100), "not-json"]) {
    const client = createTextGateway(config, { ...policy, maxResponseBytes: 64 },
      (async () => new Response(body)) as typeof fetch);
    await assert.rejects(client.completeText(request), hasCode("invalid_response"));
  }
});

test("une requête déjà annulée ne part pas", async () => {
  let calls = 0;
  const client = createTextGateway(config, policy, (async () => { calls++; return successful(); }) as typeof fetch);
  await assert.rejects(client.completeText({ ...request, signal: AbortSignal.abort() }), hasCode("cancelled"));
  assert.equal(calls, 0);
});

test("la deadline est transmise au transport et produit une erreur bornée", async () => {
  const client = createTextGateway(config, { ...policy, timeoutMs: 10 }, (async (_url, init) => {
    // Le timer garde le double actif ; la vraie requête fetch réagit au signal.
    await new Promise((resolve) => setTimeout(resolve, 30));
    init?.signal?.throwIfAborted();
    return successful();
  }) as typeof fetch);
  await assert.rejects(client.completeText(request), hasCode("deadline_exceeded"));
});

test("le loader lit seulement le secret de l'app en KV v2", async () => {
  const loaded = await loadLlmConfig({
    app: "mon-app", vaultAddr: "http://openbao.internal:8200", vaultToken: "fake-bao-token",
  }, (async (url, init) => {
    assert.equal(url, "http://openbao.internal:8200/v1/secret/data/mon-app/llm");
    assert.equal(init?.redirect, "error");
    assert.equal(new Headers(init?.headers).get("X-Vault-Token"), "fake-bao-token");
    return Response.json({ data: { data: { base_url: config.baseUrl, virtual_key: config.virtualKey } } });
  }) as typeof fetch);
  assert.deepEqual(loaded, config);
});

test("un secret absent ou mal formé rend la configuration indisponible", async () => {
  for (const response of [new Response("fake-sensitive", { status: 404 }), Response.json({ data: {} })]) {
    await assert.rejects(loadLlmConfig({
      app: "mon-app", vaultAddr: "http://openbao.internal:8200", vaultToken: "fake-bao-token",
    }, (async () => response) as typeof fetch), hasCode("configuration"));
  }
});
