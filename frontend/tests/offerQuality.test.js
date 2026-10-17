import test from "node:test";
import assert from "node:assert/strict";
import { offerDraft, offerPayload, salaryLabel } from "../src/utils/offerQuality.js";

test("offer payload preserves fixed salary and excludes server and identity fields", () => {
  const draft = offerDraft({ id: 9, company_id: 4, company_name: "Private", quality_revision: 3, salary: "3500000", skill_requirements: [{ skill: " SQL ", essential: true, weight: "4" }, { skill: "", essential: false, weight: 1 }] });
  draft.quality_details.salary_max = "4500000";
  draft.quality_details.missions = [{ outcome: "Tablero", measure: "Revisión", days: "60", skill: "sql" }];
  const payload = offerPayload(draft);
  assert.equal(payload.salary, 3500000);
  assert.equal(payload.quality_details.salary_max, 4500000);
  assert.equal(payload.quality_details.missions[0].days, 60);
  assert.deepEqual(payload.skill_requirements, [{ skill: "SQL", essential: true, weight: 4 }]);
  assert.equal(payload.company_id, undefined);
  assert.equal(payload.quality_revision, undefined);
  assert.equal(payload.id, undefined);
});

test("candidate salary labels distinguish guaranteed minimum, range and missing values", () => {
  assert.equal(salaryLabel({ salary: null }), "Salario no informado");
  assert.equal(salaryLabel({ salary: 3500000 }), "$3.500.000 COP / mes");
  assert.equal(salaryLabel({ salary: 3500000, quality_details: { salary_max: 4500000 } }), "$3.500.000 – $4.500.000 COP / mes");
});

test("guided offers declare salary units and only explicit weekly hours", () => {
  const draft = offerDraft();
  assert.equal(offerPayload(draft).quality_details.weekly_hours, null);
  draft.quality_details.weekly_hours = "37.5";
  const details = offerPayload(draft).quality_details;
  assert.equal(details.weekly_hours, 37.5);
  assert.equal(details.salary_currency, "COP");
  assert.equal(details.salary_period, "monthly");
  assert.equal(details.salary_basis, "gross_base");
  const legacy = offerDraft({ quality_details: { salary_currency: null, salary_period: null, salary_basis: null } });
  assert.equal(offerPayload(legacy).quality_details.salary_currency, "COP");
  assert.equal(offerPayload(legacy).quality_details.salary_period, "monthly");
  assert.equal(offerPayload(legacy).quality_details.salary_basis, "gross_base");
  assert.equal(offerPayload(legacy).quality_details.weekly_hours, null);
});

test("guided editing preserves education and private question scores", () => {
  const questions = [{ id: "availability", prompt: "¿Puedes asistir?", type: "choice", required: true, options: ["Sí", "No"], option_scores: { "Sí": 3, "No": -1 } }];
  const job = { application_questions: questions, required_education_level: "university", required_study_fields: ["Sistemas"] };
  const draft = offerDraft(job);
  draft.description = "Actualicé las responsabilidades";
  assert.deepEqual(offerPayload(draft).application_questions, questions);
  assert.equal(offerPayload(draft).required_education_level, "university");
  assert.deepEqual(offerPayload(draft).required_study_fields, ["Sistemas"]);
  draft.required_study_fields = " Sistemas, Informática, ";
  assert.deepEqual(offerPayload(draft).required_study_fields, ["Sistemas", "Informática"]);
  const empty = offerPayload(offerDraft());
  assert.equal(empty.required_education_level, null);
  assert.deepEqual(empty.application_questions, []);
});

test("guided payload automatically recalculates hours and preserves monthly requirements", () => {
  const draft = offerDraft({ quality_details: { experience_years: 2, weekly_hours: 40 } });
  assert.equal(offerPayload(draft).quality_details.experience_months, 24);
  draft.quality_details.experience_months = 6;
  draft.quality_details.work_schedule = { mode: "fixed", days: ["mon", "tue", "wed", "thu", "fri"], start: "05:30", end: "15:30", break_minutes: 60 };
  let details = offerPayload(draft).quality_details;
  assert.equal(details.weekly_hours, 45);
  assert.equal(details.experience_months, 6);
  assert.equal(details.experience_years, null);
  draft.quality_details.work_schedule.mode = "flexible";
  details = offerPayload(draft).quality_details;
  assert.equal(details.weekly_hours, null);
});

test("remote offers preserve multiple countries, continents and student acceptance", () => {
  const draft = offerDraft({ modality: "remote", location: "Medellín", department: "Antioquia", required_education_level: "technical" });
  const scope = { mode: "regions", countries: ["CO", "MX"], continents: ["EU"] };
  draft.quality_details.remote_scope = scope;
  draft.quality_details.education_accepts_in_progress = true;
  const payload = offerPayload(draft);
  assert.deepEqual(payload.quality_details.remote_scope, scope);
  assert.equal(payload.department, "");
  assert.match(payload.location, /Europa/);
  assert.match(payload.location, /Colombia/);
  assert.match(payload.location, /México/);
  assert.equal(payload.required_education_level, "technical");
  assert.equal(payload.quality_details.education_accepts_in_progress, true);
});

test("secondary offers remove career and ongoing-study restrictions and new guided offers keep privacy enabled", () => {
  const draft = offerDraft({ blind_hiring: false, required_education_level: "secondary", required_study_fields: ["Sistemas"] });
  draft.quality_details.education_accepts_in_progress = true;
  draft.quality_details.learnable_skills = [" SQL ", "sql", "Excel"];
  const payload = offerPayload(draft);
  assert.deepEqual(payload.required_study_fields, []);
  assert.deepEqual(payload.quality_details.learnable_skills, ["sql", "Excel"]);
  assert.equal(payload.quality_details.education_accepts_in_progress, false);
  assert.equal(payload.blind_hiring, true);
});

test("academic matching policy survives editing and student changes", () => {
  const draft = offerDraft({ quality_details: { education_field_policy: "exact" }, required_education_level: "university", required_study_fields: ["Contaduría"] });
  draft.quality_details.education_accepts_in_progress = true;
  assert.equal(offerPayload(draft).quality_details.education_field_policy, "exact");
  assert.equal(offerPayload(draft).quality_details.education_accepts_in_progress, true);
  assert.equal(offerDraft().quality_details.education_field_policy, "related");
});
