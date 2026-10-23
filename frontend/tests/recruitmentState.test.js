import test from "node:test";
import assert from "node:assert/strict";
import { interviewState, recruitmentStage } from "../src/utils/recruitmentState.js";

const now = new Date("2026-10-23T15:00:00Z");

test("a past appointment requires attendance confirmation and does not imply completion", () => {
  const row = { status: "technical_interview", interview_at: "2026-10-23T14:00:00" };
  assert.equal(interviewState(row, now), "unconfirmed");
  assert.equal(interviewState({ ...row, interview_completed_at: "2026-10-23T14:50:00" }, now), "awaiting_response");
  assert.equal(interviewState({ ...row, interview_at: "2026-10-24T14:00:00" }, now), "scheduled");
});

test("finished processes never have an active interview even with stale stage data", () => {
  for (const status of ["hired", "accepted", "rejected"]) {
    const row = { status, pipeline_stage: "interview", interview_at: "2026-10-24T14:00:00" };
    assert.equal(interviewState(row, now), null);
    assert.equal(recruitmentStage(row), status === "rejected" ? "No seleccionado" : "Contratado");
  }
});

test("advancing after a completed interview ends the pending response substate", () => {
  assert.equal(interviewState({ status: "reviewing", interview_at: "2026-10-22T14:00:00", interview_completed_at: "2026-10-22T15:00:00" }, now), null);
  assert.equal(recruitmentStage({ status: "reviewing", pipeline_stage: "portfolio" }, [{ id: "portfolio", title: "Revisión de portafolio" }]), "Revisión de portafolio");
});
