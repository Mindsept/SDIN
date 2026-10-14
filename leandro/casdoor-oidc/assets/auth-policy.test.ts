import assert from "node:assert/strict";
import { test } from "node:test";
import {
  principalFromVerifiedIdentity, canAccessDocument, safeReturnPath,
  assertCallbackLocation, assertMutationOrigin, AccessError,
} from "./auth-policy.ts";
import type { Role } from "./auth-policy.ts";

const policy = {
  expectedIssuer: "https://identity.example.test", tenantId: "tenant-a",
  groupRoles: {
    "built-in/mon-app-lecteur": "reader" as Role,
    "built-in/mon-app-redacteur": "editor" as Role,
  },
};
const identity = { issuer: policy.expectedIssuer, subject: "subject-a", groups: ["built-in/mon-app-lecteur"] };
const document = { tenantId: "tenant-a", ownerIssuer: identity.issuer, ownerSubject: "subject-a" };
const isAccessError = (error: unknown) => error instanceof AccessError;

test("seuls les groupes explicitement mappés donnent des rôles", () => {
  const principal = principalFromVerifiedIdentity({ ...identity,
    groups: ["admin", "built-in/autre-app-redacteur", "built-in/mon-app-lecteur", "built-in/mon-app-lecteur"],
  }, policy);
  assert.deepEqual(principal.roles, ["reader"]);
  assert.deepEqual(principalFromVerifiedIdentity({ ...identity, groups: ["admin"] }, policy).roles, []);
});

test("issuer incorrect ou identité vide refusés", () => {
  for (const bad of [
    { ...identity, issuer: "https://other.example.test" },
    { ...identity, issuer: policy.expectedIssuer + "/" }, { ...identity, subject: "" },
  ]) assert.throws(() => principalFromVerifiedIdentity(bad, policy), isAccessError);
});

test("un lecteur lit son document mais ne peut ni l'éditer ni lire celui d'un autre", () => {
  const principal = principalFromVerifiedIdentity(identity, policy);
  assert.equal(canAccessDocument(principal, document, "read"), true);
  assert.equal(canAccessDocument(principal, document, "edit"), false);
  assert.equal(canAccessDocument(principal, { ...document, ownerSubject: "subject-b" }, "read"), false);
});

test("même sub avec un autre issuer n'est pas le même propriétaire", () => {
  const principal = principalFromVerifiedIdentity(identity, policy);
  assert.equal(canAccessDocument(principal, { ...document, ownerIssuer: "https://other.example.test" }, "read"), false);
});

test("un rédacteur reste limité à son tenant", () => {
  const principal = principalFromVerifiedIdentity({ ...identity, groups: ["built-in/mon-app-redacteur"] }, policy);
  assert.equal(canAccessDocument(principal, { ...document, ownerSubject: "subject-b" }, "edit"), true);
  assert.equal(canAccessDocument(principal, { ...document, tenantId: "tenant-b" }, "edit"), false);
  assert.equal(canAccessDocument(principal, { ...document, tenantId: "tenant-b" }, "read"), false);
});

test("absence de rôle et action inconnue refusées", () => {
  const principal = principalFromVerifiedIdentity({ ...identity, groups: [] }, policy);
  assert.equal(canAccessDocument(principal, document, "read"), false);
  assert.equal(canAccessDocument(principal, document, "edit"), false);
  assert.equal(canAccessDocument(principal, document, "delete" as "read"), false);
});

test("le principal ne suit pas une mutation ultérieure des groupes", () => {
  const mutable = { ...identity, groups: [...identity.groups] };
  const principal = principalFromVerifiedIdentity(mutable, policy);
  mutable.groups.push("built-in/mon-app-redacteur");
  assert.deepEqual(principal.roles, ["reader"]);
  assert.ok(Object.isFrozen(principal));
  assert.ok(Object.isFrozen(principal.roles));
});

test("retours externes, encodés et routes non approuvées retombent sur /", () => {
  for (const path of [
    "https://attacker.invalid", "//attacker.invalid", "/\\attacker.invalid",
    "/%2f%2fattacker.invalid", "/%5cattacker.invalid", "/admin", null,
  ]) assert.equal(safeReturnPath(path, ["/", "/documents"]), "/");
  assert.equal(safeReturnPath("/documents?next=https://attacker.invalid#x", ["/documents"]), "/documents");
});

test("callback exact autorisé, hôte/port/chemin inattendu ou doublons refusés", () => {
  const registered = "https://app.example.test/auth/callback";
  assert.doesNotThrow(() => assertCallbackLocation(new URL(registered + "?code=fake&state=fake"), registered));
  for (const url of [
    "https://attacker.invalid/auth/callback?code=fake",
    "https://app.example.test:8443/auth/callback?code=fake",
    "https://app.example.test/other?code=fake",
    registered + "?state=a&state=b", registered + "?code=a&code=b",
    registered + "?code=a#token", "https://user:pass@app.example.test/auth/callback",
  ]) assert.throws(() => assertCallbackLocation(new URL(url), registered), isAccessError);
});

test("mutations : origine exacte et validation CSRF requises", () => {
  assert.doesNotThrow(() => assertMutationOrigin("https://app.example.test", "https://app.example.test", true));
  for (const origin of [null, "https://attacker.invalid", "https://app.example.test:8443", "null"]) {
    assert.throws(() => assertMutationOrigin(origin, "https://app.example.test", true), isAccessError);
  }
  assert.throws(() => assertMutationOrigin("https://app.example.test", "https://app.example.test", false), isAccessError);
});
