import assert from "node:assert/strict";
import { test } from "node:test";
import { createSecretReader, SecretReadError } from "./secret-reader.ts";

const options = {
  app: "mon-app", address: "http://openbao.internal:8200", token: "fake-bao-token",
  allowedSecrets: ["postgres", "llm"], allowLocalHttp: true,
};
const success = () => Response.json({ data: {
  data: { password: "fake-password" }, metadata: { version: 2, deletion_time: "", destroyed: false },
} });
const code = (expected: string) => (error: unknown) =>
  error instanceof SecretReadError && error.code === expected;

test("lecture KV v2 précise, token dans un header, aucune redirection", async () => {
  const client = createSecretReader(options, (async (url, init) => {
    assert.equal(url, "http://openbao.internal:8200/v1/secret/data/mon-app/postgres");
    assert.equal(init?.method, "GET");
    assert.equal(init?.redirect, "error");
    assert.equal(new Headers(init?.headers).get("X-Vault-Token"), "fake-bao-token");
    return success();
  }) as typeof fetch);
  assert.deepEqual(await client.read("postgres"), { values: { password: "fake-password" }, version: 2 });
});

test("chemins arbitraires et secrets inutiles refusés sans réseau", async () => {
  let calls = 0;
  const client = createSecretReader(options, (async () => { calls++; return success(); }) as typeof fetch);
  for (const name of ["../core/idp", "core/idp", "oidc", "%2e%2e", "postgres?version=1"]) {
    await assert.rejects(client.read(name), code("forbidden_path"));
  }
  assert.equal(calls, 0);
});

test("la configuration ne permet ni namespace core, ni token absent, ni HTTP implicite", () => {
  for (const invalid of [
    { ...options, app: "core" }, { ...options, app: "mon-app/../core" },
    { ...options, token: "" }, { ...options, allowLocalHttp: false },
    { ...options, address: "http://untrusted.invalid:8200" },
    { ...options, address: "https://untrusted.invalid" },
    { ...options, allowedSecrets: ["../core"] },
  ]) assert.throws(() => createSecretReader(invalid), code("configuration"));
});

test("un endpoint HTTPS doit être approuvé par la configuration opérateur", async () => {
  const client = createSecretReader({ ...options, address: "https://secrets.example.test",
    allowLocalHttp: false, approvedHttpsOrigins: ["https://secrets.example.test"],
  }, (async (url) => {
    assert.equal(url, "https://secrets.example.test/v1/secret/data/mon-app/llm");
    return success();
  }) as typeof fetch);
  await client.read("llm");
});

for (const [status, expected] of [[403, "access_denied"], [404, "not_found"],
  [503, "unavailable"], [302, "unavailable"]] as const) {
  test(`HTTP ${status} ne provoque ni défaut, ni écriture, ni retry`, async () => {
    let calls = 0;
    const client = createSecretReader(options, (async () => {
      calls++; return new Response("fake-bao-token secret error", { status });
    }) as typeof fetch);
    await assert.rejects(client.read("postgres"), (error: unknown) => {
      assert.ok(code(expected)(error));
      assert.ok(!String(error).includes("fake-bao-token"));
      return true;
    });
    assert.equal(calls, 1);
  });
}

test("enveloppe KV v1 ou version supprimée rejetées", async () => {
  for (const body of [
    { data: { password: "fake" } },
    { data: { data: {}, metadata: { version: 1, destroyed: true } } },
    { data: { data: {}, metadata: { version: 1, deletion_time: "2026-10-14" } } },
  ]) {
    const client = createSecretReader(options, (async () => Response.json(body)) as typeof fetch);
    await assert.rejects(client.read("postgres"), code("invalid_secret"));
  }
});

test("réponse trop volumineuse bornée", async () => {
  const client = createSecretReader({ ...options, maxResponseBytes: 32 },
    (async () => new Response("x".repeat(100))) as typeof fetch);
  await assert.rejects(client.read("postgres"), code("invalid_secret"));
});

test("annulation préalable sans réseau et exception réseau sans fuite", async () => {
  let calls = 0;
  const client = createSecretReader(options, (async () => {
    calls++; throw new Error("fake-bao-token in transport details");
  }) as typeof fetch);
  await assert.rejects(client.read("postgres", AbortSignal.abort()), code("cancelled"));
  assert.equal(calls, 0);
  await assert.rejects(client.read("postgres"), (error: unknown) => {
    assert.ok(code("unavailable")(error));
    assert.ok(!String(error).includes("fake-bao-token"));
    return true;
  });
});

test("muter la liste de chemins ou l'adresse après création ne change pas les accès", async () => {
  const mutable = { ...options, allowedSecrets: ["postgres"] };
  const client = createSecretReader(mutable, (async (url) => {
    assert.equal(url, "http://openbao.internal:8200/v1/secret/data/mon-app/postgres");
    return success();
  }) as typeof fetch);
  mutable.address = "https://untrusted.invalid";
  mutable.allowedSecrets.push("oidc");
  await assert.rejects(client.read("oidc"), code("forbidden_path"));
  await client.read("postgres");
});
