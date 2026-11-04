import test from "node:test";
import assert from "node:assert/strict";
import { invitationPath, invitationTokenFromPath, loginDestination, registrationDestination } from "../src/utils/accessNavigation.js";
import { accountHome } from "../src/utils/accountAccess.js";

test("Pending registration takes precedence over the company authenticator and saved destinations", () => {
  for (const company of [false, true]) for (const mfa_enabled of [false, true]) {
    assert.equal(loginDestination({ company, from: "/empresa/vacantes", user: { registration_pending: true, mfa_enabled }, accessOptions: { mode: "session", company_mfa_required: true } }), "/completar-cuenta");
  }
});

test("authenticated entry prioritizes incomplete registration, MFA and the user's own role", () => {
  assert.equal(accountHome(null), "/login");
  assert.equal(accountHome({ role: "candidate", registration_pending: true }), "/completar-cuenta");
  assert.equal(accountHome({ role: "company" }, { mode: "session", company_mfa_required: true }), "/empresa/bienvenida");
  assert.equal(accountHome({ role: "admin" }, { mode: "session", admin_mfa_required: true }), "/seguridad");
  for (const [role, path] of [["candidate", "/candidato"], ["company", "/empresa/bienvenida"], ["admin", "/admin"]]) assert.equal(accountHome({ role, mfa_enabled: true }), path);
});

test("invited registration returns to acceptance with or without MFA", () => {
  const args = { company: true, invitation: "test-token+with/slash", accessOptions: { mode: "session", company_mfa_required: false } };
  assert.equal(registrationDestination(args), invitationPath(args.invitation));
  assert.equal(registrationDestination({ ...args, accessOptions: { mode: "session" } }), "/seguridad?invitation=test-token%2Bwith%2Fslash");
  assert.equal(registrationDestination({ ...args, invitation: null }), "/empresa/bienvenida");
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
    assert.equal(loginDestination({ ...args, from }), "/empresa/bienvenida");
  }
  assert.equal(loginDestination({ ...args, from: "/empresa/vacantes" }), "/empresa/vacantes");
  assert.equal(loginDestination({ ...args, company: false, from: invitationPath("x") }), "/candidato");
  assert.equal(loginDestination({ ...args, company: false, from: "/vacantes/7" }), "/vacantes/7");
});
