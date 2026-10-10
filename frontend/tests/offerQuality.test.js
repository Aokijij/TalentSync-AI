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
