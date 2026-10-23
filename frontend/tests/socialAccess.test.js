import test from "node:test";
import assert from "node:assert/strict";
import { socialFailure } from "../src/utils/socialAccess.js";

test("Social failures distinguish recoverable attempts from configuration and existing accounts", () => {
  assert.equal(socialFailure("failed", "expired", "google").retry, true);
  assert.match(socialFailure("failed", "expired", "google").message, /venció/);
  assert.equal(socialFailure("failed", "provider_configuration", "github").retry, false);
  assert.equal(socialFailure("existing", "expired", "google").retry, false);
  assert.match(socialFailure("existing", "expired", "google").message, /vincular/);
});

test("Untrusted reason and provider parameters never echo through error references", () => {
  const value = socialFailure("failed", "token=private", "<script>");
  assert.equal(value.reference, null);
  assert.equal(value.provider, undefined);
  assert.ok(!JSON.stringify(value).includes("private"));
  for (const parameter of ["__proto__", "constructor", "toString"]) {
    const unknown = socialFailure("failed", parameter, parameter);
    assert.equal(unknown.provider, undefined);
    assert.equal(unknown.reference, null);
    assert.equal(typeof unknown.message, "string");
    assert.equal(socialFailure("failed", parameter, "google").reference, null);
  }
});
