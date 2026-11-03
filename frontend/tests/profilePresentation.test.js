import assert from "node:assert/strict";
import { test } from "node:test";
import { calendarDays, shiftDate, shiftMonth } from "../src/utils/calendar.js";
import { continueBullet } from "../src/utils/bulletEditing.js";
import { exportSections, savedResumeSections } from "../src/utils/resumeExport.js";

test("calendar covers leap February and navigates month and year boundaries", () => {
  const days = calendarDays("2024-02");
  assert.equal(days.length, 42);
  assert.ok(days.includes("2024-02-29"));
  assert.equal(new Date(`${days[0]}T12:00:00Z`).getUTCDay(), 1);
  assert.equal(shiftDate("2024-02-29", 1), "2024-03-01");
  assert.equal(shiftMonth("2026-12", 1), "2027-01");
  assert.equal(shiftMonth("2026-01", -1), "2025-12");
});

test("Enter continues bullets, replaces selected text and leaves an empty list", () => {
  assert.deepEqual(continueBullet("• Primera acción", 16), { value: "• Primera acción\n• ", caret: 19 });
  assert.deepEqual(continueBullet("• Uno resto", 5, 11), { value: "• Uno\n• ", caret: 8 });
  assert.deepEqual(continueBullet("• Uno\n• ", 8), { value: "• Uno\n", caret: 6 });
  assert.equal(continueBullet("Texto libre", 5), null);
});

test("resume documents have independent switches while retaining older export choices", () => {
  assert.equal(exportSections.length, 11);
  assert.deepEqual(savedResumeSections({ resume_export_options: { sections: ["certifications"] } }), ["certifications", "driving_licenses", "professional_cards"]);
  assert.deepEqual(savedResumeSections({ resume_export_options: { sections: ["certifications"], version: 2 } }), ["certifications"]);
});
