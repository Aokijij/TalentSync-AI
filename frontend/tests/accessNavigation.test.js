import test from "node:test";
import assert from "node:assert/strict";
import { invitationPath, invitationTokenFromPath, loginDestination, registrationDestination } from "../src/utils/accessNavigation.js";

test("invited registration returns to acceptance with or without MFA", () => {
  const args = { company: true, invitation: "test-token+with/slash", accessOptions: { mode: "session", company_mfa_required: false } };
  assert.equal(registrationDestination(args), invitationPath(args.invitation));
  assert.equal(registrationDestination({ ...args, accessOptions: { mode: "session" } }), "/seguridad?invitation=test-token%2Bwith%2Fslash");
  assert.equal(registrationDestination({ ...args, invitation: null }), "/empresa/equipo");
  assert.equal(registrationDestination({ ...args, company: false }), "/bienvenida");
});

test("existing invited accounts retain their invitation through login and MFA setup", () => {
  const from = invitationPath("test-token+with/slash");
  const args = { company: true, from, user: { mfa_enabled: false }, accessOptions: { mode: "session", company_mfa_required: false } };
  assert.equal(loginDestination(args), from);
  assert.equal(loginDestination({ ...args, accessOptions: { mode: "session" } }), "/seguridad?invitation=test-token%2Bwith%2Fslash");
  assert.equal(loginDestination({ ...args, user: { mfa_enabled: true }, accessOptions: { mode: "session" } }), from);
  assert.equal(invitationTokenFromPath(from), "test-token+with/slash");
});

test("login return paths cannot redirect offsite or across access portals", () => {
  const args = { company: true, user: { mfa_enabled: true }, accessOptions: { mode: "session" } };
  for (const from of ["https://example.com/equipo/invitacion?token=x", "//example.com/equipo/invitacion?token=x", "/\\example.com/equipo/invitacion?token=x"]) {
    assert.equal(invitationTokenFromPath(from), null);
    assert.equal(loginDestination({ ...args, from }), "/empresa");
  }
  assert.equal(loginDestination({ ...args, from: "/empresa/vacantes" }), "/empresa/vacantes");
  assert.equal(loginDestination({ ...args, company: false, from: invitationPath("x") }), "/candidato");
  assert.equal(loginDestination({ ...args, company: false, from: "/vacantes/7" }), "/vacantes/7");
});
