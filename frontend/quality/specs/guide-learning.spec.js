import { test, expect } from "@playwright/test";

const course = { id: "course-review", version: 1, title: "Curso de hojas de cálculo", provider: "Proveedor de revisión", category: "administration", kind: "course", hours: 2, cost: "free", active: true, url: "https://example.com/course", skills: ["excel"], instructions: "Organiza tablas y revisa los datos del temario con ejercicios del proveedor.", journey: null, practice: { mode: "none" }, details: { certificate_cost: "free", level: "beginner", languages: ["Español"], syllabus: [], access_notes: "Consulta las condiciones del proveedor", certificate_notes: "Documento emitido por el proveedor", prerequisites: "", duration_notes: "" } };
const organization = { id: 41, name: "Empresa de revisión", active: true, role: "owner", verification_status: "verified", verification_required: true };
async function setup(page, { width = 1280, theme = "light", role = "candidate", path = "/aprendizaje", memberRole = "owner" } = {}) {
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  const errors = [], calls = [], state = { plans: [], courseDone: false, adminCourse: { ...course }, failAdd: false };
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", async (route) => {
    const request = route.request(), url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    const endpoint = url.pathname.replace("/api/v1", ""), method = request.method(), body = request.postDataJSON();
    calls.push({ endpoint, method, body });
    if (endpoint === "/notifications/unread-count") return route.fulfill({ json: { count: 0 } });
    if (["/organization/me", "/organization/access"].includes(endpoint)) return route.fulfill({ json: { ...organization, role: memberRole } });
    if (endpoint === "/learning/catalog") return route.fulfill({ json: { resources: [course], areas: [{ id: "administration", label: "Administración" }], assessments: [] } });
    if (endpoint === "/learning/plans") return route.fulfill({ json: state.plans });
    if (endpoint === `/learning/plans/${course.id}` && method === "PUT") {
      if (state.failAdd) return route.fulfill({ status: 503, json: { detail: "No se pudo añadir el curso de revisión." } });
      state.plans = [{ id: 1, resource: course, version: 1, status: "in_progress", progress: { course_tracking: true, course_completed: false } }];
      return route.fulfill({ json: state.plans });
    }
    if (endpoint === `/learning/plans/${course.id}/course`) {
      state.courseDone = body.completed;
      state.plans = state.plans.map((row) => ({ ...row, version: row.version + 1, status: body.completed ? "completed" : "in_progress", progress: { ...row.progress, course_completed: body.completed } }));
      return route.fulfill({ json: state.plans });
    }
    if (endpoint === "/learning/passport") return route.fulfill({ json: {
      learning_results: Array.from({ length: 13 }, (_, index) => ({ id: `result-${index}`, resource_id: "previous-course", title: `Práctica de revisión ${index + 1}`, provider: "YouTube", score: index ? 60 : 0, passed: false, attempt_number: index + 1, feedback: [{ question_id: "question", prompt: "Actividad del intento anterior", correct: false, message: "Revisa las condiciones del caso antes de reintentar." }], completed_at: "2026-10-23T14:00:00" })),
      certificates: [{ id: "certificate", name: "Excel básico", issuer: "Proveedor de revisión", year: "2026", url: "https://example.com/credential" }],
      course_results: state.courseDone ? [{ resource_id: course.id, title: course.title, provider: course.provider, completed_at: "2026-10-23T14:00:00" }] : [],
      assessments: [{ id: "assessment", assessment_id: "microservices", skill: "microservicios", title: "Decisiones básicas de microservicios", status: "completed", score: 60, passed: false, valid: false, feedback: [], started_at: "2026-10-23T14:00:00" }], practice_evidence: [], notice: "Los documentos y los intentos se conservan con su alcance." } });
    if (endpoint === "/learning/opportunities") return route.fulfill({ json: { items: [] } });
    if (endpoint === "/learning/opportunity-sources") return route.fulfill({ json: { sources: [] } });
    if (endpoint === "/admin/learning/demand") return route.fulfill({ json: { skills: [], vacancy_sample: 0 } });
    if (endpoint === "/admin/learning/practice-templates") return route.fulfill({ json: [{ id: "excel", title: "Comprueba una hoja de cálculo" }] });
    if (endpoint === "/admin/learning/practice-templates/excel") return route.fulfill({ json: { activities: [{ id: "calculation", type: "number", prompt: "De diez entregas se devuelven dos. ¿Cuántas quedan?", answer: 8, feedback: "Se restan las dos devoluciones a diez." }] } });
    if (endpoint === "/admin/learning/resources") {
      if (method === "POST") state.adminCourse = { ...course, ...body };
      return route.fulfill({ status: method === "POST" ? 201 : 200, json: method === "GET" ? [] : [state.adminCourse] });
    }
    return route.fulfill({ status: 404, json: { detail: "Ruta no prevista en esta revisión" } });
  });
  const params = new URLSearchParams({ entry: "1", theme, path, ...(role ? { signed: role } : {}) });
  await page.goto(`/quality/?${params}`);
  return { state, calls, errors };
}
async function noOverflow(page) {
  const result = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, elements: [...document.querySelectorAll("body *")].filter((node) => node.getBoundingClientRect().right > innerWidth + 1).slice(0, 10).map((node) => ({ tag: node.tagName, class: String(node.className), width: Math.round(node.getBoundingClientRect().width) })) }));
  expect(result.overflow, JSON.stringify(result.elements)).toBeLessThanOrEqual(1);
}

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Course tracking and separate results · ${width} · ${theme}`, async ({ page }) => {
  const context = await setup(page, { width, theme });
  await page.getByRole("button", { name: "Añadir a mi plan", exact: true }).click();
  await expect(page.locator(".feedback-toast")).toHaveCount(1);
  await expect(page.locator(".feedback-toast")).toContainText("Añadido a Mi plan");
  await expect(page.locator(".learning-published")).toHaveCount(0);
  await page.getByRole("button", { name: "Abrir Mi plan", exact: true }).click();
  await expect(page.getByRole("heading", { name: "1. Estudia el curso", exact: true })).toBeVisible();
  await expect(page.getByText("No hay una práctica asociada a este curso.", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Aportar certificado", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ya terminé el curso", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Confirmar finalización", exact: true }).click();
  await expect(page.getByRole("button", { name: "Retomar curso", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Mis resultados", exact: true }).click();
  await expect(page.locator(".result-record")).toHaveCount(8);
  await expect(page.locator(".result-record-score").first()).toHaveText("0%");
  await page.getByRole("textbox", { name: "Buscar en mis resultados", exact: true }).fill("Práctica de revisión 12");
  await expect(page.locator(".result-record")).toHaveCount(1);
  await page.getByRole("textbox", { name: "Buscar en mis resultados", exact: true }).fill("");
  await page.getByRole("tab", { name: "Cursos (1)", exact: true }).click();
  await expect(page.locator(".result-record")).toContainText("Finalizado por ti");
  await expect(page.locator(".result-record-score")).toHaveCount(0);
  await page.getByRole("tab", { name: "Certificados (1)", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Excel básico", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Fundamentos (1)", exact: true }).click();
  await expect(page.locator(".result-record-score")).toHaveText("60%");
  await noOverflow(page);
  await page.screenshot({ path: `../.local/learning-guide-review/results-${theme}-${width}.png`, fullPage: true });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; }); await noOverflow(page);
  expect(context.calls.filter((row) => row.endpoint.endsWith("/journey"))).toEqual([]);
  expect(context.errors).toEqual([]);
});

test("Landing explains roles and guide limits interviewer actions", async ({ page }) => {
  await setup(page, { role: null, path: "/", width: 360, theme: "dark" });
  await page.getByRole("tab", { name: "Empresas", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Revisar muchas candidaturas", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Administración", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Publicar formación y prácticas", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Lo que distingue tu recorrido en TalentSync.", exact: true })).toBeVisible();
  await setup(page, { role: "company", memberRole: "interviewer", path: "/guia", width: 360 });
  await expect(page.getByRole("button", { name: /Preparar y evaluar entrevistas/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Preparar una oferta clara/ })).toHaveCount(0);
  await page.getByRole("button", { name: "Abrir menú", exact: true }).click();
  await expect(page.getByRole("link", { name: "Guía de uso", exact: true })).toHaveCount(1);
  await page.getByRole("dialog", { name: "Navegación principal", exact: true }).getByRole("button", { name: "Cerrar menú", exact: true }).click();
  await noOverflow(page);
});

test("Candidate guide opens topics without changing preferences", async ({ page }) => {
  const context = await setup(page, { role: "candidate", path: "/guia", width: 1280 });
  const topics = page.getByRole("navigation", { name: "Temas de la guía", exact: true });
  await expect(topics.getByRole("button")).toHaveCount(8);
  await topics.getByRole("button", { name: /Cursos, prácticas y Mi plan/ }).click();
  await expect(page.getByRole("heading", { name: "Cursos, prácticas y Mi plan", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir Cursos y prácticas", exact: true })).toHaveAttribute("href", "/aprendizaje#cursos");
  await expect(page.getByText(/Añadir a Mi plan no te inscribe/)).toBeVisible();
  await page.screenshot({ path: "../.local/learning-guide-review/candidate-guide.png", fullPage: true });
  expect(context.calls.filter((row) => row.method !== "GET")).toEqual([]);
});

test("Admin can author a practice with separate solutions through the resource form", async ({ page }) => {
  const context = await setup(page, { role: "admin", path: "/admin/aprendizaje", width: 1280 });
  await page.getByRole("button", { name: "Añadir formación +", exact: true }).click();
  const form = page.locator("#catalog-editor");
  await form.getByLabel("Nombre del curso o taller", { exact: true }).fill(course.title);
  await form.getByLabel("Quién lo ofrece", { exact: true }).fill(course.provider);
  await form.getByLabel("Enlace público del recurso (HTTPS)", { exact: true }).fill(course.url);
  await form.getByRole("button", { name: "Continuar", exact: true }).click();
  await form.getByLabel(/^Habilidades que podrá reforzar/).fill("excel");
  await form.locator('[name="instructions"]').fill(course.instructions);
  await form.getByLabel(/^Horas estimadas/).fill("2");
  await form.getByLabel(/^Relación con la práctica/).selectOption("template");
  await form.getByLabel(/^Práctica que has revisado/).selectOption("excel");
  await form.getByText("Revisar actividades y soluciones de la plantilla", { exact: true }).click();
  await expect(form.getByText("Respuesta: 8", { exact: true })).toBeVisible();
  await form.getByLabel(/^Relación con la práctica/).selectOption("custom");
  await form.getByLabel(/^Cómo se relaciona con el temario/).fill("El caso permite repasar las operaciones del temario de este curso.");
  await form.getByLabel("Título de la práctica", { exact: true }).fill("Revisa las entregas del almacén");
  await form.getByLabel("Caso y datos para resolverlo", { exact: true }).fill("Se registran diez entregas ficticias y dos devoluciones. Comprueba las cantidades del almacén.");
  await form.getByLabel(/^Pasos en el orden correcto/).fill("Revisar las entregas\nContar las devoluciones\nRegistrar el resultado");
  await form.getByLabel("Pregunta del cálculo", { exact: true }).fill("De diez entregas se devuelven dos. ¿Cuántas quedan?");
  await form.getByLabel("Respuesta numérica correcta", { exact: true }).fill("8");
  await form.getByLabel("Explicación de la solución", { exact: true }).fill("Se restan las dos devoluciones a diez: el resultado es ocho.");
  await form.getByLabel("Conceptos, uno por línea", { exact: true }).fill("Entrega\nDevolución\nRegistro");
  await form.getByLabel("Definiciones correspondientes", { exact: true }).fill("Pedido recibido\nPedido retornado\nAnotación del resultado");
  await page.screenshot({ path: "../.local/learning-guide-review/practice-authoring.png", fullPage: true });
  await form.getByRole("button", { name: "Continuar", exact: true }).click();
  await form.getByRole("button", { name: "Publicar recurso", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Guardar recurso", exact: true }).click();
  await expect(page.locator(".feedback-toast")).toHaveCount(1);
  const write = context.calls.find((row) => row.method === "POST" && row.endpoint === "/admin/learning/resources");
  expect(write.body.practice.mode).toBe("custom");
  expect(write.body.practice.draft.calculation_answer).toBe(8);
  expect(write.body.practice.draft.steps).toHaveLength(3);
  expect(context.errors).toEqual([]);
});

test("Failed addition keeps the course available and emits no success notification", async ({ page }) => {
  const context = await setup(page, { width: 360 });
  context.state.failAdd = true;
  const add = page.getByRole("button", { name: "Añadir a mi plan", exact: true });
  await add.click();
  await expect(page.getByRole("alert")).toContainText("No se pudo añadir el curso");
  await expect(page.locator(".feedback-toast")).toHaveCount(0);
  await expect(add).toBeEnabled();
  context.state.failAdd = false;
  await add.click();
  await expect(page.locator(".feedback-toast")).toHaveCount(1);
});
