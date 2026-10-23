import { test, expect } from "@playwright/test";

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Recruitment inbox and active process · ${width} · ${theme}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  const errors = [], calls = []; let failUpdate = true;
  page.on("pageerror", (error) => errors.push(error.message));
  const stages = [{ id: "submitted", title: "Recibidas" }, { id: "reviewing", title: "En revisión" }, { id: "interview", title: "Entrevista" }, { id: "hired", title: "Contratados" }, { id: "rejected", title: "No seleccionados" }];
  const rows = Array.from({ length: 400 }, (_, i) => ({ id: i + 1, user_id: i + 1001, job_id: 101, candidate_name: `Persona ${String(i).padStart(3, "0")}`, profession: "Analista de operaciones", created_at: "2026-10-20T14:00:00", reviewed_at: null, version: 1, base_match_percentage: i % 5 ? 75 : null, adjusted_match_percentage: i % 5 ? 75 : null, screening_adjustment: 0, recruiter_notes: "Solo para el equipo", screening_answers: i === 398 ? [{ question_id: "example", question: "Describe un resultado", answer: "Organicé inventarios y verifiqué las diferencias.", type: "open", reviewer_adjustment: 1 }] : [], interview_at: i === 396 ? "2030-10-30T14:00:00" : null, interview_details: i === 396 ? { mode: "virtual", minutes: 60, location: "https://meet.google.com/example" } : {}, status: i < 396 ? "submitted" : i < 398 ? "reviewing" : i === 398 ? "hired" : "rejected", pipeline_stage: i < 396 ? "submitted" : i < 398 ? "reviewing" : i === 398 ? "hired" : "rejected" }));
  const group = (row) => ["hired", "accepted", "rejected"].includes(row.status) ? "closed" : ["submitted", "seen"].includes(row.status) ? "inbox" : "active";
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname.replace("/api/v1", ""); calls.push({ method: request.method(), path, params: url.searchParams, body: request.method() === "POST" || request.method() === "PUT" ? request.postDataJSON() : null });
    const json = (data, status = 200) => route.fulfill({ status, json: data });
    if (path === "/jobs/mine/board") return json([{ id: 101, title: "Analista de operaciones y coordinación de inventarios", status: "active", applications_count: 400, pipeline_stages: stages }]);
    if (path === "/applications/jobs/101/workspace") {
      const counts = { inbox: 0, active: 0, closed: 0, interviews: 1 }, stageCounts = {}, allStageCounts = {};
      for (const row of rows) { counts[group(row)]++; allStageCounts[row.pipeline_stage] = (allStageCounts[row.pipeline_stage] || 0) + 1; if (group(row) === "active") stageCounts[row.pipeline_stage] = (stageCounts[row.pipeline_stage] || 0) + 1; }
      const bucket = url.searchParams.get("bucket"), search = url.searchParams.get("search") || "", score = url.searchParams.get("score_filter");
      const filtered = rows.filter((row) => (bucket === "interviews" ? row.interview_at && group(row) !== "closed" : group(row) === bucket) && (bucket !== "interviews" || !url.searchParams.get("interview_state") || url.searchParams.get("interview_state") === "all" || (url.searchParams.get("interview_state") === "awaiting_response" ? !!row.interview_completed_at : url.searchParams.get("interview_state") === "scheduled" ? new Date(row.interview_at) > new Date() && !row.interview_completed_at : new Date(row.interview_at) < new Date() && !row.interview_completed_at)) && (!url.searchParams.get("stage") || row.pipeline_stage === url.searchParams.get("stage")) && `${row.candidate_name} ${row.profession}`.toLowerCase().includes(search.toLowerCase()) && (score === "missing" ? row.adjusted_match_percentage == null : score === "unreviewed" ? !row.reviewed_at : true));
      const size = Number(url.searchParams.get("page_size") || 25), current = Number(url.searchParams.get("page") || 1);
      return json({ items: filtered.slice((current - 1) * size, current * size), total: filtered.length, page: current, page_size: size, counts, interview_counts: { scheduled: rows.filter((r) => r.interview_at && new Date(r.interview_at) > new Date() && group(r) !== "closed").length, unconfirmed: rows.filter((r) => r.interview_at && new Date(r.interview_at) < new Date() && !r.interview_completed_at && group(r) !== "closed").length, awaiting_response: rows.filter((r) => r.interview_completed_at && group(r) !== "closed").length }, stage_counts: stageCounts, all_stage_counts: allStageCounts, hired_count: 1, unreviewed: rows.filter((row) => group(row) === "inbox" && !row.reviewed_at).length });
    }
    const detail = path.match(/^\/applications\/(\d+)\/review$/), reviewed = path.match(/^\/applications\/(\d+)\/reviewed$/), update = path.match(/^\/applications\/(\d+)\/status$/);
    if (detail) { const row = rows.find((item) => item.id === Number(detail[1])); return json({ application: row, profile: { profession: row.profession, experience: "Coordino inventarios y documento los resultados con el equipo.", skills: ["excel", "python", "sql"], experiences: [{ role: "Analista de inventario", company: "Empresa de ejemplo", description: "Organicé registros y revisé las diferencias." }], educations: [] } }); }
    if (reviewed) { const row = rows.find((item) => item.id === Number(reviewed[1])); row.reviewed_at = "2026-10-23T16:00:00"; row.version++; return json({ reviewed_at: row.reviewed_at, version: row.version, first_review: true }); }
    if (update) {
      if (failUpdate) { failUpdate = false; return json({ detail: "No se pudo guardar el avance. Vuelve a intentarlo." }, 503); }
      const row = rows.find((item) => item.id === Number(update[1])), payload = request.postDataJSON();
      if (payload.expected_version !== row.version) return json({ detail: "La versión cambió" }, 409);
      Object.assign(row, payload); row.version++;
      if (payload.pipeline_stage) row.status = payload.pipeline_stage === "interview" ? "technical_interview" : "reviewing";
      if (payload.interview_action === "complete") row.interview_completed_at = new Date().toISOString();
      return json(row);
    }
    if (path.endsWith("/explanation")) return json({ base_match_percentage: 75, match_percentage: 75 });
    return json({ detail: `Ruta inesperada: ${path}` }, 404);
  });
  await page.goto(`/quality/?recruitment=1&role=company&theme=${theme}`);
  await expect(page.getByRole("tab", { name: "Por revisar (396)", exact: true })).toBeVisible();
  await expect(page.locator(".applicant-list-row")).toHaveCount(25);
  expect(calls.some((item) => item.path.endsWith("/mark-seen") || item.path === "/applications/jobs/101")).toBe(false);
  expect(calls.some((item) => item.path.endsWith("/explanation"))).toBe(false);
  await page.locator(".applicant-list-row").first().click();
  const detail = page.getByRole("complementary", { name: "Detalle de candidatura", exact: true });
  await expect(detail.getByRole("heading", { name: "Persona 000", exact: true })).toBeVisible();
  await expect(detail.getByRole("button", { name: "Cambiar etapa", exact: true })).toBeEnabled();
  expect(calls.filter((item) => item.path.endsWith("/reviewed"))).toHaveLength(1);
  if (width > 760) {
    await page.locator(".applicant-list-row").first().focus();
    await page.keyboard.press("ArrowDown");
    await expect(detail.getByRole("heading", { name: "Persona 001", exact: true })).toBeVisible();
    await expect(detail.getByRole("button", { name: "Cambiar etapa", exact: true })).toBeEnabled();
    await page.locator('.applicant-list-row[data-application-id="2"]').focus();
    await page.keyboard.press("ArrowUp");
    await expect(detail.getByRole("heading", { name: "Persona 000", exact: true })).toBeVisible();
    await page.keyboard.press("r");
    const decision = page.getByRole("dialog", { name: "Finalizar candidatura con feedback", exact: true });
    await expect(decision).toBeVisible();
    await decision.getByRole("button", { name: "Volver a revisar", exact: true }).click();
    expect(calls.filter((item) => item.method === "PUT")).toHaveLength(0);
  }
  await page.screenshot({ path: `../.local/recruitment-review/inbox-${theme}-${width}.png`, fullPage: true });
  await detail.getByRole("button", { name: "Cambiar etapa", exact: true }).click();
  await page.getByRole("alertdialog", { name: "Confirmar cambio de etapa", exact: true }).getByRole("button", { name: "Cancelar", exact: true }).click();
  expect(calls.filter((item) => item.method === "PUT")).toHaveLength(0);
  await detail.getByRole("button", { name: "Cambiar etapa", exact: true }).click();
  await page.getByRole("button", { name: "Cambiar y notificar", exact: true }).click();
  await expect(detail.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(detail.getByRole("heading", { name: "Persona 000", exact: true })).toBeVisible();
  await detail.getByRole("button", { name: "Cambiar etapa", exact: true }).click();
  await page.getByRole("button", { name: "Cambiar y notificar", exact: true }).click();
  await expect(detail.getByRole("heading", { name: "Persona 001", exact: true })).toBeVisible();
  await expect(detail.getByRole("button", { name: "Cambiar etapa", exact: true })).toBeEnabled();
  await detail.getByRole("button", { name: "Finalizar con feedback", exact: true }).click();
  const rejection = page.getByRole("dialog", { name: "Finalizar candidatura con feedback", exact: true });
  const before = calls.filter((item) => item.method === "PUT").length;
  await expect(rejection).toBeVisible();
  expect(calls.filter((item) => item.method === "PUT")).toHaveLength(before);
  await rejection.getByLabel("Mensaje para el candidato").fill("Gracias por participar. Para este cargo necesitamos más experiencia en inventarios.");
  await rejection.getByRole("button", { name: "Finalizar y notificar", exact: true }).click();
  await expect(rejection).toHaveCount(0);
  expect(calls.filter((item) => item.method === "PUT").at(-1).body.candidate_feedback.message).toContain("inventarios");
  await page.getByRole("tab", { name: /^Proceso activo/ }).click();
  await expect(page.getByRole("region", { name: "Tablero del proceso activo" })).toBeVisible();
  await expect(page.locator(".pipeline-applicant")).toHaveCount(3);
  if (width > 760) {
    const from = page.getByRole("region", { name: "En revisión", exact: true });
    const to = page.getByRole("region", { name: "Entrevista", exact: true });
    await from.locator(".pipeline-applicant").filter({ hasText: "Persona 396" }).click();
    await expect(detail.getByRole("heading", { name: "Persona 396", exact: true })).toBeVisible();
    await expect(detail.getByRole("button", { name: "Cambiar etapa", exact: true })).toBeEnabled();
    await detail.getByRole("button", { name: "Cerrar detalle", exact: true }).click();
    await from.locator(".pipeline-applicant").filter({ hasText: "Persona 396" }).dragTo(to);
    await page.getByRole("button", { name: "Cambiar y notificar", exact: true }).click();
    await expect(to.locator(".pipeline-applicant")).toHaveCount(1);
    await expect(from.locator(".pipeline-applicant")).toHaveCount(2);
  }
  await page.screenshot({ path: `../.local/recruitment-review/active-${theme}-${width}.png`, fullPage: true });
  await page.getByLabel("Opciones de la vacante", { exact: true }).click();
  await page.getByRole("button", { name: "Editar etapas", exact: true }).click();
  const stageEditor = page.getByRole("dialog", { name: "Editar etapas", exact: true });
  await expect(stageEditor.getByRole("button", { name: "Eliminar Recibidas", exact: true })).toBeDisabled();
  await expect(stageEditor.getByRole("button", { name: "Bajar etapa", exact: true }).first()).toBeDisabled();
  await stageEditor.getByRole("button", { name: "Agregar etapa", exact: true }).click();
  await expect(stageEditor.getByRole("textbox", { name: "Nombre de etapa 4", exact: true })).toHaveValue("Nueva etapa");
  await stageEditor.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.getByRole("button", { name: "Lista", exact: true }).click();
  await expect(page.locator(".applicant-list-row")).toHaveCount(3);
  await page.getByRole("combobox", { name: "Filtrar por estado del proceso" }).selectOption("interview");
  await expect(page.locator(".applicant-list-row")).toHaveCount(width > 760 ? 1 : 0);
  await page.getByRole("combobox", { name: "Filtrar por estado del proceso" }).selectOption("");
  await expect(page.locator(".applicant-list-row")).toHaveCount(3);
  rows[396].status = "technical_interview"; rows[396].pipeline_stage = "interview"; rows[396].interview_at = "2000-01-01T14:00:00";
  await page.getByRole("tab", { name: /^Entrevistas/ }).click();
  await page.getByRole("button", { name: /^Por registrar/ }).click();
  await page.locator(".applicant-list-row").first().click();
  await detail.getByRole("button", { name: "Registrar entrevista realizada", exact: true }).click();
  const completion = page.getByRole("alertdialog", { name: "Registrar entrevista realizada", exact: true });
  await completion.getByRole("button", { name: "Registrar y notificar", exact: true }).click();
  await expect(detail.getByText("El candidato espera tu respuesta")).toBeVisible();
  await page.getByRole("button", { name: /^Pendientes de respuesta/ }).click();
  await expect(page.locator(".applicant-list-row")).toHaveCount(1);
  await page.getByRole("tab", { name: /^Finalizados/ }).click();
  await page.locator('.applicant-list-row[data-application-id="399"]').click();
  await expect(detail.getByRole("button", { name: "Gestionar entrevista", exact: true })).toHaveCount(0);
  await detail.getByRole("button", { name: /^Ver respuestas/ }).click();
  const closedAnswers = page.getByRole("dialog", { name: "Respuestas de postulación", exact: true });
  await expect(closedAnswers.getByRole("combobox")).toBeDisabled();
  await expect(closedAnswers.getByRole("button", { name: /Guardar valoración/ })).toHaveCount(0);
  await closedAnswers.getByRole("button", { name: "Cerrar", exact: true }).click();
  await page.getByRole("tab", { name: /^Por revisar/ }).click();
  await page.getByRole("textbox", { name: "Buscar candidatura", exact: true }).fill("Persona 200");
  await expect(page.locator(".applicant-list-row")).toHaveCount(1);
  const writes = calls.filter((item) => item.method === "PUT").length;
  await page.getByRole("textbox", { name: "Buscar candidatura", exact: true }).press("a");
  expect(calls.filter((item) => item.method === "PUT")).toHaveLength(writes);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});

test("Recruitment can recover a failed vacancy load without claiming an empty inbox", async ({ page }) => {
  let attempts = 0, available = false;
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/jobs/mine/board")) {
      attempts++;
      return !available ? route.fulfill({ status: 503, json: { detail: "No pudimos consultar tus vacantes" } }) : route.fulfill({ json: [{ id: 101, title: "Vacante de ejemplo", status: "active", pipeline_stages: [] }] });
    }
    if (path.endsWith("/workspace")) return route.fulfill({ json: { items: [], total: 0, page: 1, page_size: 25, counts: { inbox: 0, active: 0, interviews: 0, closed: 0 }, stage_counts: {}, all_stage_counts: {}, unreviewed: 0 } });
    return route.fulfill({ status: 404, json: { detail: "Ruta inesperada" } });
  });
  await page.goto("/quality/?recruitment=1&role=company&theme=light");
  await expect(page.getByRole("alert")).toContainText("No pudimos consultar tus vacantes");
  await expect(page.getByText("Tu bandeja está al día", { exact: true })).toHaveCount(0);
  available = true;
  await page.getByRole("button", { name: "Volver a intentar", exact: true }).click();
  await expect(page.getByText("Tu bandeja está al día", { exact: true })).toBeVisible();
  expect(attempts).toBe(3);
});
