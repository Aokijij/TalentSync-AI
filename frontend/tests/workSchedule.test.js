import assert from "node:assert/strict";
import test from "node:test";
import { EMPTY_WORK_SCHEDULE, scheduleHours, scheduleSummary } from "../src/utils/workSchedule.js";
import { qualityStepProgress } from "../src/utils/offerQuality.js";

test("fixed and overnight schedules count selected days once and subtract breaks", () => {
  const value = { ...EMPTY_WORK_SCHEDULE, days: ["mon", "tue", "wed", "thu", "fri"], start: "08:00", end: "17:00", break_minutes: 60 };
  assert.equal(scheduleHours(value), 40);
  assert.equal(scheduleHours({ ...value, break_minutes: 45 }), 41.25);
  assert.match(scheduleSummary(value), /Lunes a viernes · 08:00 a 17:00 · 60 minutos de descanso/);
  const overnight = { ...value, days: ["mon", "mon"], start: "22:00", end: "06:00", break_minutes: 30 };
  assert.equal(scheduleHours(overnight), 7.5);
  assert.match(scheduleSummary(overnight), /finaliza al día siguiente/);
});

test("missing times, zero duration, invalid times and flexible schedules do not invent hours", () => {
  assert.equal(scheduleHours(EMPTY_WORK_SCHEDULE), null);
  for (const [start, end] of [["08:00", "08:00"], ["25:00", "17:00"], ["", "17:00"]]) assert.equal(scheduleHours({ ...EMPTY_WORK_SCHEDULE, days: ["mon"], start, end }), null);
  const flexible = { ...EMPTY_WORK_SCHEDULE, mode: "flexible", days: ["sat", "sun"], notes: "Entrada a convenir" };
  assert.equal(scheduleHours(flexible), null);
  assert.equal(scheduleSummary(flexible), "Horario flexible · Sábados y domingos · Entrada a convenir");
});

test("quality steps retain responsibility points when missions are absent", () => {
  const quality = { checks: [{ step: 1, key: "description", points: 20, weight: 20, passed: true }, { step: 1, key: "missions", points: 0, weight: 3, passed: false }] };
  assert.deepEqual(qualityStepProgress(quality, 1), { points: 20, total: 23, complete: false });
});
