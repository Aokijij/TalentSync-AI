import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.domain.entities.nlp import NLPResult

COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "html",
    "html5",
    "css",
    "css3",
    "php",
    "react",
    "angular",
    "vue",
    "nodejs",
    "node.js",
    "fastapi",
    "django",
    "flask",
    "spring boot",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "git",
    "github",
    "gitlab",
    "linux",
    "bash",
    "postman",
    "swagger",
    "api rest",
    "rest",
    "wordpress",
    "bootstrap",
    "tailwind",
    "figma",
    "power bi",
    "excel",
    "pandas",
    "numpy",
    "scikit-learn",
    "machine learning",
    "nlp",
    "qa",
    "testing",
    "selenium",
    "scrum",
    "kanban",
    "agile",
    "liderazgo",
    "trabajo en equipo",
    "comunicación",
    "gestión de proyectos",
    "análisis de requerimientos",
    "aseguramiento de calidad",
    "autocad",
    "revit",
    "ms project",
    "topografía",
    "costos y presupuestos",
    "supervisión técnica",
    "control de calidad",
    ".net",
    "c#",
    "desarrollo de software",
    "analítica de datos",
    "inteligencia artificial",
    "docencia",
    "pedagogía",
    "matemáticas",
    "gestión administrativa",
    "administración",
    "ventas",
    "negociación",
    "prospección de clientes",
    "servicio al cliente",
    "atención al cliente",
    "logística",
    "gestión de inventarios",
    "despachos",
    "contabilidad",
    "facturación",
    "conciliaciones bancarias",
    "enfermería",
    "atención al paciente",
    "manejo de caja",
    "recursos humanos",
    "reclutamiento",
    "selección de personal",
    "crm",
    "sap",
    "gestión documental",
    "presupuestos",
    "interventoría",
    "marketing digital",
    "redes sociales",
    "google analytics",
    "meta ads",
    "google ads",
    "canva",
    "capcut",
    "photoshop",
    # Ambiente, construcción, SST y gestión. La lista funciona como taxonomía
    # extensible y no depende de que el CV tenga una sección llamada "Skills".
    "gestión ambiental",
    "gestión socioambiental",
    "saneamiento ambiental",
    "seguridad y salud en el trabajo",
    "sst",
    "hseq",
    "manejo de residuos",
    "gestión de residuos",
    "normatividad ambiental",
    "legislación ambiental",
    "impacto ambiental",
    "evaluación de impacto ambiental",
    "auditoría ambiental",
    "seguimiento ambiental",
    "monitoreo ambiental",
    "licenciamiento ambiental",
    "planes de manejo ambiental",
    "pasao",
    "informes técnicos",
    "trabajo de campo",
    "inducción de personal",
    "capacitación",
    "docencia",
    "diseño curricular",
    "análisis de agua",
    "análisis de alimentos",
    "química",
    "biología",
    "manejo de sustancias químicas",
    "calidad del agua",
    "iso 14001",
    "iso 45001",
    "sistemas integrados de gestión",
    "contratación pública",
    "obra pública",
    "cicloinfraestructura",
    "electromecánica",
    "control de obra",
    "residencia de obra",
    "elaboración de informes",
    "gestión de permisos",
    "cumplimiento normativo",
}

SKILL_ALIAS_PATTERNS = {
    ".net": (r"(?<!\w)\.net(?!\w)", r"\bdotnet\b"),
    "desarrollo de software": (
        r"\bdesarroll(?:o|ador(?:a)?)\s+de\s+software\b",
        r"\bfull[\s-]?stack\b",
        r"\bfront[\s-]?end\b",
        r"\bback[\s-]?end\b",
    ),
    "analítica de datos": (
        r"\banalitica\s+de\s+datos\b",
        r"\banalisis\s+de\s+datos\b",
        r"\bdata\s+analytics\b",
    ),
    "inteligencia artificial": (r"\binteligencia\s+artificial\b", r"\bia\b"),
    "docencia": (
        r"\bdocent(?:e|es)\b",
        r"\bprofesor(?:a|es|as)?\b",
        r"\bensenanza\b",
    ),
    "pedagogía": (r"\bpedagog(?:ia|ico|ica|icos|icas)\b",),
    "matemáticas": (r"\bmatematic(?:a|as|o|os)\b",),
    "gestión administrativa": (
        r"\b(?:auxiliar|asistente)\s+administrativ(?:o|a)\b",
        r"\bgestion\s+administrativa\b",
    ),
    "ventas": (
        r"\bventas?\b",
        r"\bvendedor(?:a|es|as)?\b",
        r"\b(?:asesor|ejecutivo)\s+comercial\b",
    ),
    "servicio al cliente": (
        r"\bservicio\s+al\s+cliente\b",
        r"\batencion\s+al\s+cliente\b",
        r"\bcustomer\s+service\b",
    ),
    "logística": (
        r"\blogistic(?:a|o)\b",
        r"\b(?:auxiliar|operario)\s+de\s+bodega\b",
    ),
    "gestión de inventarios": (r"\binventarios?\b",),
    "contabilidad": (
        r"\bcontabilidad\b",
        r"\bcontable\b",
        r"\bcontador(?:a|es)?\b",
    ),
    "facturación": (r"\bfactur(?:acion|ar|as?)\b",),
    "enfermería": (r"\benfermer(?:ia|o|a|os|as)\b",),
    "atención al paciente": (r"\batencion\s+(?:a|al)\s+pacientes?\b",),
    "manejo de caja": (r"\bmanejo\s+de\s+caja\b", r"\bcajer(?:o|a|os|as)\b"),
    "recursos humanos": (r"\brecursos\s+humanos\b", r"\btalento\s+humano\b"),
    "reclutamiento": (r"\breclutamiento\b", r"\breclutador(?:a|es|as)?\b"),
}


class TextProcessor:
    def __init__(self) -> None:
        self._vectorizer = HashingVectorizer(
            n_features=384, alternate_sign=False, norm="l2"
        )

    def repair_spaced_letters(self, text: str) -> str:
        def collapse(match: re.Match[str]) -> str:
            return re.sub(r"\s+", "", match.group(0))

        latin = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9"
        text = re.sub(rf"(?<!\w)(?:[{latin}] ){{2,}}[{latin}](?!\w)", collapse, text)
        text = re.sub(r"\b((?:19|20)\d)\s+(\d)\b", r"\1\2", text)
        text = re.sub(r"\b((?:19|20)\d)\s+(\d)(?=[A-Za-zÁÉÍÓÚÑ])", r"\1\2\n", text)
        text = re.sub(r"\b[Dd]\s+[Ee]\b", "de", text)
        text = re.sub(r"\b[Ee]\s+[Nn]\b", "en", text)
        text = re.sub(r"\b[Aa]\s+[Ll]\b", "al", text)
        text = re.sub(r"\b[Ee]\s+[Ll]\b", "el", text)
        text = re.sub(r"\b[Ll]\s+[Aa]\b", "la", text)
        text = re.sub(r"\b[Ll]\s+[Oo]\b", "lo", text)
        text = re.sub(r"\b[Qq]\s+[Aa]\b", "QA", text)
        text = re.sub(r"\b[Ss]\s+[Aa]\b", "SA", text)
        text = re.sub(r"\b([A-ZÁÉÍÓÚÑ])\s+([a-záéíóúñ]{2,})\b", r"\1\2", text)
        return text

    @staticmethod
    def repair_pdf_glyphs(text: str) -> str:
        """Repair the most common missing accent glyphs emitted by PDF fonts."""
        regex_replacements = {
            r"ingenier\s*�\s*a": "ingeniería",
            r"an\s*�\s*lisis": "análisis",
            r"dise\s*�\s*o": "diseño",
            r"comunicaci\s*�\s*n": "comunicación",
            r"educaci\s*�\s*n": "educación",
            r"gesti\s*�\s*n": "gestión",
            r"tecnolog\s*�\s*a": "tecnología",
            r"metodolog\s*�\s*as": "metodologías",
            r"\s*�\s*giles": " ágiles",
            r"cat\s*�\s*lica": "católica",
            r"amig\s*�": "amigó",
            r"inform\s*�\s*tica": "informática",
            r"pr\s*�\s*cticas": "prácticas",
        }
        for broken, repaired in regex_replacements.items():
            text = re.sub(broken, repaired, text, flags=re.I)
        replacements = {
            "CI�N": "CIÓN",
            "ci�n": "ción",
            "GI�N": "GIÓN",
            "gi�n": "gión",
            "TECNOLOG�A": "TECNOLOGÍA",
            "tecnolog�a": "tecnología",
            "INGENIER�A": "INGENIERÍA",
            "ingenier�a": "ingeniería",
            "MEDELL�N": "MEDELLÍN",
            "Medell�n": "Medellín",
            "medell�n": "medellín",
            "QU�MICA": "QUÍMICA",
            "qu�mica": "química",
            "BIOLOG�A": "BIOLOGÍA",
            "AN�LISIS": "ANÁLISIS",
            "an�lisis": "análisis",
            "�REA": "ÁREA",
            "P�BLICA": "PÚBLICA",
            "p�blica": "pública",
            "T�CNIC": "TÉCNIC",
            "t�cnic": "técnic",
            "GU�A": "GUÍA",
            "gu�a": "guía",
            "INTERVENTOR�A": "INTERVENTORÍA",
            "interventor�a": "interventoría",
            "EL�CTRIC": "ELÉCTRIC",
            "el�ctric": "eléctric",
        }
        for broken, repaired in replacements.items():
            text = text.replace(broken, repaired)
        return text.replace("�", "")

    def fold_text(self, text: str) -> str:
        value = self.repair_pdf_glyphs(self.repair_spaced_letters(text)).lower()
        value = unicodedata.normalize("NFKD", value)
        value = "".join(
            character for character in value if not unicodedata.combining(character)
        )
        value = re.sub(r"[^a-z0-9+#.\s-]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def clean_text(self, text: str) -> str:
        text = self.repair_pdf_glyphs(self.repair_spaced_letters(text)).lower()
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"[^a-záéíóúüñ0-9+#.\s-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def extract_skills(self, text: str) -> list[str]:
        clean = self.fold_text(text)
        tokens = clean.split()
        found = []
        for skill in sorted(COMMON_SKILLS):
            folded_skill = self.fold_text(skill)
            if re.search(
                rf"(?<![\w+#.]){re.escape(folded_skill)}(?![\w+#.])", clean, re.I
            ):
                found.append(skill)
                continue
            # Font maps sometimes lose a single accented vowel (gesti�n -> gestin).
            # A conservative fuzzy pass recovers long domain terms without turning
            # arbitrary CV prose into skills.
            skill_tokens = folded_skill.split()
            if len(folded_skill) < 7:
                continue
            windows = (
                " ".join(tokens[index : index + len(skill_tokens)])
                for index in range(len(tokens) - len(skill_tokens) + 1)
            )
            if any(
                SequenceMatcher(None, folded_skill, window).ratio() >= 0.92
                for window in windows
            ):
                found.append(skill)
        for skill, patterns in SKILL_ALIAS_PATTERNS.items():
            if any(re.search(pattern, clean, re.I) for pattern in patterns):
                found.append(skill)
        return sorted(set(found))

    def extract_location(self, text: str) -> str | None:
        domicile = re.search(r"domicilio\s*:\s*([^\n]+)", text, re.I)
        if domicile:
            return domicile.group(1).strip(" .")
        for city in (
            "bogota",
            "medellin",
            "cali",
            "barranquilla",
            "cartagena",
            "bucaramanga",
            "manizales",
            "pereira",
            "guarne",
            "rionegro",
            "envigado",
            "itagui",
        ):
            if re.search(rf"\b{city}\b", self.clean_text(text)):
                return city.title()
        return None

    def extract_phone(self, text: str) -> str | None:
        # Colombian mobile numbers only; avoids contract/NIT numbers in CV bodies.
        match = re.search(r"(?:\+?57[\s.-]?)?3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}", text)
        return match.group(0).strip() if match else None

    def extract_profession(self, text: str) -> str | None:
        repaired = self.repair_pdf_glyphs(self.repair_spaced_letters(text))
        for line in repaired.splitlines()[:35]:
            candidate = re.sub(r"\s+", " ", line).strip(" .:-")
            if (
                re.match(
                    r"^(?:practicante\s+de\s+ingenier[íi]a|ingenier[oa]|administrador(?:a)?|arquitect[oa]|abogad[oa]|contador(?:a)?|psic[oó]log[oa]|tecn[oó]log[oa]|desarrollador(?:a)?|analista)\b",
                    candidate,
                    re.I,
                )
                and len(candidate) <= 140
            ):
                return candidate.split("|")[0].strip().title()
        profile_match = re.search(
            r"perfil\s+profesional\s*\n?\s*([^\n.]{8,140})", repaired, re.I
        )
        if profile_match:
            lead = profile_match.group(1).strip()
            professional = re.search(
                r"(profesional\s+en\s+.+?)(?=\s+con\b|[,.;]|$)", lead, re.I
            )
            if professional:
                return professional.group(1).title()
        clean = self.clean_text(text)
        for title in (
            "analista de proyectos",
            "residente administrativo",
            "ingeniero de sistemas",
            "desarrollador frontend",
            "desarrollador front-end",
            "analista de datos",
            "analista de requerimientos",
            "residente de obra",
            "analista de software",
            "desarrollador full stack",
            "desarrollador backend",
        ):
            if title in clean:
                return title.title()
        return None

    @staticmethod
    def _line(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" .•-")

    @staticmethod
    def _month_period_pattern() -> re.Pattern[str]:
        month = r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
        return re.compile(
            rf"(?P<start_month>{month})\s*(?P<start_year>(?:19|20)\d{{2}})\s*[-–—a]+\s*(?P<end_month>{month})?\s*(?P<end_year>(?:19|20)\d{{2}}|presente|actualidad)",
            re.I,
        )

    def _extract_period_entries(self, block: str, kind: str) -> list[dict]:
        periods = list(self._month_period_pattern().finditer(block))
        entries: list[dict] = []
        previous_end = 0
        role_pattern = re.compile(
            r"^(?:residente|instructor|auxiliar|analista|ingenier|coordinador|director|jefe|supervisor|consultor|profesional|docente|practicante|asistente|gerente)",
            re.I,
        )
        degree_pattern = re.compile(
            r"(?:posgrado|postgrado|pregrado|especializaci[oó]n|ingenier[íi]a|tecnolog[íi]a|tecn[oó]log|t[eé]cnic|profesional|maestr[íi]a|doctorado|bachiller)",
            re.I,
        )
        institution_pattern = re.compile(
            r"(?:universidad|sena|instituto|instituci[oó]n|polit[eé]cnico|college|academy)",
            re.I,
        )
        for period in periods:
            segment = block[previous_end : period.start()]
            previous_end = period.end()
            lines = [
                self._line(line) for line in segment.splitlines() if self._line(line)
            ]
            if kind == "experience":
                index = next(
                    (i for i, line in enumerate(lines) if role_pattern.match(line)),
                    None,
                )
                if index is None or index + 1 >= len(lines):
                    continue
                role = lines[index]
                company = lines[index + 1]
                body = " ".join(lines[index + 2 :])
                functions = re.search(r"funciones?\s*:\s*(.*)", body, re.I)
                description = (functions.group(1) if functions else body).strip()
                entries.append(
                    {
                        "company": company[:140],
                        "role": role[:160],
                        "start_year": period.group("start_year"),
                        "end_year": "Presente"
                        if period.group("end_year").lower()
                        in {"presente", "actualidad"}
                        else period.group("end_year"),
                        "description": description[:900],
                    }
                )
            else:
                located = next(
                    (
                        (i, degree_pattern.search(line))
                        for i, line in enumerate(lines)
                        if degree_pattern.search(line)
                    ),
                    None,
                )
                index = located[0] if located else None
                if index is None:
                    continue
                degree = lines[index][located[1].start() :]
                institution = "No especificada"
                for line in lines[index + 1 : index + 4]:
                    institution_match = institution_pattern.search(line)
                    if institution_match:
                        institution = line[institution_match.start() :]
                        break
                entries.append(
                    {
                        "degree": degree[:200],
                        "institution": institution[:160],
                        "start_year": period.group("start_year"),
                        "end_year": "Presente"
                        if period.group("end_year").lower()
                        in {"presente", "actualidad"}
                        else period.group("end_year"),
                    }
                )
        return entries

    @staticmethod
    def _period_year(value: str) -> str:
        match = re.search(r"(19\d{2}|20\d{2})", value)
        return match.group(1) if match else ""

    def _dedupe(self, items: list[dict], key: str) -> list[dict]:
        result = []
        seen = set()
        for item in items:
            value = self.fold_text(str(item.get(key, "")))
            # Extraction engines can disagree only on punctuation or a broken
            # font glyph. Those are the same semantic record, not two records.
            value = re.sub(r"[^a-z0-9]+", " ", value).strip()
            if value and value not in seen:
                seen.add(value)
                result.append(item)
        return result

    def _extract_section(self, text: str, start: str, stops: tuple[str, ...]) -> str:
        start_match = re.search(start, text, re.I | re.M)
        if not start_match:
            return ""
        tail = text[start_match.end() :]
        if not stops:
            return tail
        stop_pattern = "|".join(stops)
        stop_match = re.search(stop_pattern, tail, re.I | re.M)
        return tail[: stop_match.start()] if stop_match else tail

    @staticmethod
    def _semantic_line(value: str) -> str:
        """Remove presentation markup while keeping the text's meaning."""
        value = re.sub(r"^\s*#{1,6}\s*", "", value)
        value = re.sub(r"^\s*(?:[-*+]\s+|[•]\s*)", "", value)
        return re.sub(r"\s+", " ", value).strip(" .")

    @staticmethod
    def _resume_period(value: str) -> tuple[str, str, tuple[int, int]] | None:
        """Read common CV periods without depending on one visual template."""
        month = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
        end_word = r"presente|actualidad|actual|en\s+curso|vigente"
        patterns = (
            re.compile(
                rf"(?:{month}\s+)?(?P<start>(?:19|20)\d{{2}})\s*(?:[-–—]|a|hasta)\s*(?:{month}\s+)?(?P<end>(?:19|20)\d{{2}}|{end_word})",
                re.I,
            ),
            re.compile(
                rf"(?P<start>(?:19|20)\d{{2}})\s*(?:[-–—]|a|hasta)\s*(?P<end>(?:19|20)\d{{2}}|{end_word})",
                re.I,
            ),
        )
        for pattern in patterns:
            match = pattern.search(value)
            if match:
                end = match.group("end")
                if not re.fullmatch(r"(?:19|20)\d{2}", end):
                    end = "Presente"
                return match.group("start"), end, match.span()
        return None

    def _extract_semantic_experiences(self, text: str) -> list[dict]:
        """Interpret Docling headings and field labels as employment records.

        Docling already solves reading order and layout. This stage deliberately
        reasons from generic concepts (period, employer, role and duties), not
        from coordinates or employer names from a sample CV.
        """
        block = self._extract_section(
            self.repair_pdf_glyphs(text),
            r"(?:^|\n)\s*#{0,6}\s*(?:experiencia|trayectoria)\s+(?:laboral|profesional)(?:\s+y\s+laboral)?\s*$",
            (
                r"(?:^|\n)\s*#{1,6}\s*(?:herramientas|habilidades|competencias|tecnolog[ií]as|referencias|idiomas|certificaciones)\b",
                r"\n\s*PYPDF FALLBACK\s*\n",
            ),
        )
        if not block:
            return []

        lines = block.splitlines()
        entries: list[tuple[int, str, str, str]] = []
        rejected_prefixes = (
            "cargo",
            "puesto",
            "rol",
            "posicion",
            "posición",
            "funciones",
            "responsabilidades",
            "jefe",
            "supervisor",
            "contacto",
            "telefono",
            "teléfono",
        )
        for index, raw_line in enumerate(lines):
            line = self._semantic_line(raw_line)
            period = self._resume_period(line)
            if not line or not period:
                continue
            start_year, end_year, span = period
            employer = line[: span[0]].strip(" ([-–—:")
            if not employer:
                employer = line[span[1] :].strip(" )]-–—:")
            normalized = self.fold_text(employer)
            if (
                len(employer) < 2
                or normalized.startswith(rejected_prefixes)
                or re.fullmatch(r"(?:19|20)\d{2}", employer)
            ):
                continue
            entries.append((index, employer[:140], start_year, end_year))

        experiences: list[dict] = []
        metadata = re.compile(
            r"^(?:jef(?:e|a)(?:s)?\s+inmediat|supervisor|referencia|contacto|tel[eé]fono|celular|correo|nit)\b",
            re.I,
        )
        role_label = re.compile(
            r"^(?:cargo|puesto|rol|posici[oó]n|ocupaci[oó]n)\s*:\s*(.*)$", re.I
        )
        duties_heading = re.compile(
            r"^(?:funciones|responsabilidades|actividades|tareas|logros|principales\s+funciones)\s*:?$",
            re.I,
        )
        for entry_index, (line_index, employer, start_year, end_year) in enumerate(
            entries
        ):
            next_index = (
                entries[entry_index + 1][0]
                if entry_index + 1 < len(entries)
                else len(lines)
            )
            record_lines = lines[line_index + 1 : next_index]
            role = ""
            duties_started = False
            description_lines: list[str] = []
            unlabeled_lines: list[str] = []
            for raw_line in record_lines:
                line = self._semantic_line(raw_line)
                if not line or line == "<!-- image -->":
                    continue
                role_match = role_label.match(line)
                if role_match:
                    role = role_match.group(1).strip(" .:")
                    continue
                if duties_heading.match(line):
                    duties_started = True
                    continue
                if metadata.match(line):
                    continue
                if duties_started:
                    description_lines.append(line)
                elif not line.startswith("#"):
                    unlabeled_lines.append(line)

            if not role:
                role = next(
                    (
                        line
                        for line in unlabeled_lines
                        if len(line) <= 160
                        and re.search(
                            r"\b(?:analista|auxiliar|asistente|coordinador|director|gerente|jefe|ingenier|inspector|residente|consultor|profesional|docente|practicante|desarrollador|supervisor|administrador|arquitect)\b",
                            line,
                            re.I,
                        )
                    ),
                    "",
                )
            if not description_lines:
                description_lines = [line for line in unlabeled_lines if line != role]
            if not role:
                role = "Cargo no identificado"
            experiences.append(
                {
                    "company": employer,
                    "role": role[:160],
                    "start_year": start_year,
                    "end_year": end_year,
                    "description": " ".join(description_lines)[:900],
                }
            )
        return experiences

    def _extract_semantic_educations(self, text: str) -> list[dict]:
        """Parse labelled and free-form education items from Docling Markdown."""
        block = self._extract_section(
            self.repair_pdf_glyphs(text),
            r"(?:^|\n)\s*#{0,6}\s*(?:(?:formaci[oó]n|educaci[oó]n)\s+acad[eé]mica|estudios)\s*$",
            (
                r"(?:^|\n)\s*#{0,6}\s*(?:experiencia|trayectoria)\s+(?:laboral|profesional)",
                r"\n\s*PYPDF FALLBACK\s*\n",
            ),
        )
        if not block:
            return []

        lines = block.splitlines()
        degree_label = re.compile(
            r"^(?P<label>pregrado|posgrado|postgrado|especializaci[oó]n|maestr[ií]a|doctorado|tecn[oó]log[oa]|tecnolog[ií]a|t[eé]cnic[oa]|profesional|bachiller)\s*:\s*(?P<content>.*)$",
            re.I,
        )
        institution_pattern = re.compile(
            r"\b(?:universidad|university|instituto|instituci[oó]n|colegio|escuela|polit[eé]cnico|sena|i\.?\s*e\.?)\b",
            re.I,
        )
        stop_line = re.compile(
            r"^(?:cursos?|diplomados?|certificaciones?|seminarios?|talleres?)\b", re.I
        )
        items: list[dict] = []
        index = 0
        while index < len(lines):
            line = self._semantic_line(lines[index])
            match = degree_label.match(line)
            if not match:
                index += 1
                continue
            label = match.group("label").strip().title()
            content = match.group("content").strip()
            cursor = index + 1
            if not content:
                while cursor < len(lines):
                    candidate = self._semantic_line(lines[cursor])
                    if candidate and candidate != "<!-- image -->":
                        content = candidate
                        cursor += 1
                        break
                    cursor += 1

            status_match = re.search(
                r"\s*(?:[-–—|,]\s*)?(?P<status>(?:19|20)\d{2}|en\s+curso|presente|actualidad|finalizado|culminado)\s*$",
                content,
                re.I,
            )
            end_year = ""
            if status_match:
                status = status_match.group("status")
                end_year = (
                    status
                    if re.fullmatch(r"(?:19|20)\d{2}", status)
                    else (
                        "Presente"
                        if status.lower() in {"en curso", "presente", "actualidad"}
                        else ""
                    )
                )
                content = content[: status_match.start()].strip(" -–—|,()")
            elif re.search(r"\ben\s+curso\b", content, re.I):
                end_year = "Presente"

            institution = "No especificada"
            degree = content
            institution_match = institution_pattern.search(content)
            if institution_match:
                if (
                    label.lower().startswith("bachiller")
                    or institution_match.start() == 0
                ):
                    institution = content[institution_match.start() :].strip(" -–—|,")
                    degree = (
                        "Bachiller" if label.lower().startswith("bachiller") else label
                    )
                else:
                    degree = content[: institution_match.start()].strip(" -–—|,")
                    institution = content[institution_match.start() :].strip(" -–—|,")
            else:
                for nearby_index in range(cursor, min(cursor + 3, len(lines))):
                    candidate = self._semantic_line(lines[nearby_index])
                    if degree_label.match(candidate) or stop_line.match(candidate):
                        break
                    if institution_pattern.search(candidate):
                        institution = candidate
                        break

            if not degree:
                degree = label
            items.append(
                {
                    "degree": degree[:200],
                    "institution": institution[:160],
                    "start_year": "",
                    "end_year": end_year,
                }
            )
            index = max(index + 1, cursor)
        return items

    def _extract_structured_experiences(self, text: str) -> list[dict]:
        repaired = self.repair_pdf_glyphs(text)
        block = self._extract_section(
            repaired,
            r"experiencia\s+(?:laboral|profesional|profesional y laboral)",
            (r"herramientas", r"habilidades", r"referencias"),
        )
        period_entries = self._extract_period_entries(block, "experience")
        if period_entries:
            return self._dedupe(period_entries, "company")
        month = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
        pattern = re.compile(
            rf"(?P<company>^[^\n()]{{2,140}}?)\s*\(\s*(?P<start>{month}\s+\d{{4}})\s*(?:-|–|—|�|a)\s*(?P<end>{month}\s+\d{{4}})\s*\)\s*(?P<body>.*?)(?=^[^\n()]+?\s*\(\s*{month}\s+\d{{4}}\s*(?:-|–|—|�|a)|\Z)",
            re.I | re.M | re.S,
        )
        experiences = []
        for match in pattern.finditer(block):
            body = match.group("body")
            role_match = re.search(r"cargo\s*:\s*([^\n.]+)", body, re.I)
            functions_match = re.search(r"funciones\s*:\s*(.*)", body, re.I | re.S)
            description = functions_match.group(1).strip() if functions_match else ""
            description = re.sub(r"[•]\s*", "", description)
            experiences.append(
                {
                    "company": re.sub(r"\s+", " ", match.group("company")).strip(" ."),
                    "role": role_match.group(1).strip(" .")
                    if role_match
                    else "Cargo no identificado",
                    "start_year": self._period_year(match.group("start")),
                    "end_year": self._period_year(match.group("end")),
                    "description": description[:900],
                }
            )
        return experiences

    def _extract_education_and_courses(
        self, text: str
    ) -> tuple[list[dict], list[dict]]:
        repaired = self.repair_pdf_glyphs(text)
        block = self._extract_section(
            repaired,
            r"(?:formaci.n|educaci.n)\s+acad.mica|mis\s+estudios",
            (r"experiencia\s+(?:laboral|profesional)",),
        )
        period_educations = self._extract_period_entries(block, "education")
        educations = []
        for line in block.splitlines():
            cleaned = re.sub(r"^[•\-]\s*", "", line).strip()
            match = re.match(
                r"(?:pregrado|tecn.loga|t.cnica|bachiller|profesional|especializaci.n|maestr.a)\s*:\s*(.+)",
                cleaned,
                re.I,
            )
            if not match:
                continue
            content = match.group(1).strip()
            year_match = re.search(
                r"(?:-|–|—)\s*(\d{4}|en\s+curso|presente)\s*$", content, re.I
            )
            end = year_match.group(1).title() if year_match else ""
            degree = (
                content[: year_match.start()].strip(" -") if year_match else content
            )
            educations.append(
                {
                    "degree": degree,
                    "institution": "No especificada",
                    "start_year": "",
                    "end_year": end,
                }
            )

        courses = []
        course_block = self._extract_section(
            block, r"(?:cursos?\s+y\s+diplomados?|certificaciones?)\s*:", ()
        )
        for line in course_block.splitlines():
            name = re.sub(r"^[•\-]\s*", "", line).strip(" .")
            if len(name) >= 3 and not re.search(r"experiencia\s+laboral", name, re.I):
                courses.append({"name": name, "issuer": "No especificado", "year": ""})
        return self._dedupe(period_educations + educations, "degree"), self._dedupe(
            courses, "name"
        )

    def _extract_certifications(self, text: str) -> list[dict]:
        repaired = self.repair_pdf_glyphs(text)
        certifications: list[dict] = []
        patterns = (
            r"(?:el\s+t[ií]tulo\s+de|le\s+confiere\s+el\s+t[ií]tulo\s+de)\s*:?[\s\n]+([^\n]{5,180})",
            r"certificaci[oó]n\s+(?:en|de)\s+([^\n]{5,160})",
        )
        for pattern in patterns:
            for match in re.finditer(pattern, repaired, re.I):
                name = self._line(match.group(1))
                if name.lower().rstrip(":").endswith((" en", " de", "especialista en")):
                    following = [
                        self._line(line)
                        for line in repaired[
                            match.end() : match.end() + 350
                        ].splitlines()
                        if self._line(line)
                    ]
                    if following:
                        name = f"{name.rstrip(':')} {following[0]}"
                        if (
                            following[0].lower().endswith((" en", " de"))
                            and len(following) > 1
                        ):
                            name = f"{name} {following[1]}"
                if name:
                    year = self._period_year(repaired[match.end() : match.end() + 400])
                    certifications.append(
                        {
                            "name": name[:180],
                            "issuer": "Documento adjunto",
                            "year": year,
                        }
                    )
        return self._dedupe(certifications, "name")

    def _extract_visual_timeline(self, text: str) -> tuple[list[dict], list[dict]]:
        """Read CVs whose PDF text layer spaces every letter instead of preserving columns."""
        visual = self.repair_pdf_glyphs(self.repair_spaced_letters(text))
        visual = re.sub(r"((?:19|20)\d{2})\s*([A-Za-zÁÉÍÓÚÑáéíóúñ])", r"\1\n\2", visual)
        section_heading = re.compile(
            r"^\s*#{0,6}\s*(?:perfil\s+profesional|educaci[oó]n|formaci[oó]n|habilidades|tecnolog[ií]as|proyectos|certificaciones|idiomas|referencias)\s*$",
            re.I | re.M,
        )
        experience_blocks = []
        for experience_match in re.finditer(
            r"experiencia\s+(?:laboral|profesional)", visual, re.I
        ):
            tail = visual[experience_match.end() :]
            stop = section_heading.search(tail)
            block = tail[: stop.start()] if stop else tail
            period_count = len(
                re.findall(
                    r"(?:19|20)\d{2}\s*[-–—]\s*(?:(?:19|20)\d{2}|presente|actualidad)",
                    block,
                    re.I,
                )
            )
            experience_blocks.append((period_count, len(block), block))
        experience_block = max(experience_blocks, default=(0, 0, ""))[2]
        periods = list(
            re.finditer(
                r"(?P<start>(?:19|20)\d{2})\s*[-–—]\s*(?P<end>(?:19|20)\d{2}|presente|actualidad)",
                experience_block,
                re.I,
            )
        )
        role_pattern = re.compile(
            r"^(?P<role>(?:desarrollador|analista|ingeniero|coordinador|director|residente|auxiliar|profesional|practicante|diseñador|asistente|supervisor)[^\n]{0,100})$",
            re.I | re.M,
        )
        ignored = {
            "habilidades",
            "tecnologias",
            "tecnologías",
            "proyectos",
            "contacto",
            "medellin colombia",
        }
        experiences = []
        for index, period in enumerate(periods):
            end = (
                periods[index + 1].start()
                if index + 1 < len(periods)
                else len(experience_block)
            )
            segment = experience_block[period.end() : end]
            role_match = role_pattern.search(segment)
            if not role_match:
                continue
            preceding_lines = [
                line.strip(" .")
                for line in segment[: role_match.start()].splitlines()
                if line.strip()
            ]
            company = ""
            for line in reversed(preceding_lines):
                normalized = self.clean_text(line)
                if (
                    normalized in ignored
                    or normalized.startswith(("http", "www"))
                    or "," in line
                ):
                    continue
                if re.search(
                    r"\b(?:s\.?a\.?s?\.?|ltda\.?|inc\.?|llc|corp\.?|group|solutions)\b",
                    line,
                    re.I,
                ) or re.fullmatch(r"[A-Za-zÁÉÍÓÚÑáéíóúñ0-9 .&-]{2,80}", line):
                    company = re.sub(r"\s+", " ", line)
                    break
            if not company:
                prior_lines = [
                    self._line(line)
                    for line in experience_block[
                        max(0, period.start() - 240) : period.start()
                    ].splitlines()
                    if self._line(line)
                ]
                company = next(
                    (
                        line
                        for line in reversed(prior_lines)
                        if not role_pattern.match(line)
                    ),
                    "Empresa no identificada",
                )
            company = re.sub(
                r"\bS\s*\.\s*A\s*\.\s*S\s*\.?", "S.A.S.", company, flags=re.I
            )
            company = re.sub(r"\bS\s*\.\s*A\s*\.?", "S.A.", company, flags=re.I)
            description_lines = [
                self._line(line)
                for line in segment[role_match.end() :].splitlines()
                if self._line(line)
                and not re.search(
                    r"^(?:https?://|www\.|(?:19|20)\d{2}\s*[-–—])",
                    self._line(line),
                    re.I,
                )
            ]
            experiences.append(
                {
                    "company": company,
                    "role": re.sub(r"\s+", " ", role_match.group("role")).strip(" ."),
                    "start_year": period.group("start"),
                    "end_year": "Presente"
                    if period.group("end").lower() in {"presente", "actualidad"}
                    else period.group("end"),
                    "description": " ".join(description_lines)[:900],
                }
            )

        degree_pattern = re.compile(
            r"^(?:ingenier[íi]a|tecn[oó]logo|tecnolog[íi]a|t[eé]cnico|profesional|especializaci[oó]n|maestr[íi]a|doctorado|bachiller)[^\n]{2,120}$",
            re.I,
        )
        institution_pattern = re.compile(
            r"\b(?:universidad|instituto|instituci[oó]n|politecnico|polit[eé]cnico|sena|academy|college)\b",
            re.I,
        )
        period_pattern = re.compile(
            r"((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2}|presente|actualidad)", re.I
        )
        lines = [
            re.sub(r"\s+", " ", line).strip(" .")
            for line in visual.splitlines()
            if line.strip()
        ]
        educations = []
        for index, line in enumerate(lines):
            if not degree_pattern.match(line):
                continue
            if re.search(r"\b(?:cuento|experiencia|estudiante\s+de)\b", line, re.I):
                continue
            degree = line
            if (
                index + 1 < len(lines)
                and not lines[index + 1].startswith("#")
                and not period_pattern.search(lines[index + 1])
                and not institution_pattern.search(lines[index + 1])
                and not re.search(
                    r"\b(?:cuento\s+con|experiencia)\b", lines[index + 1], re.I
                )
                and len(lines[index + 1]) < 100
            ):
                degree = f"{degree} {lines[index + 1]}"
            before = lines[max(0, index - 5) : index]
            after = lines[index + 1 : index + 6]
            institution = next(
                (item for item in reversed(before) if institution_pattern.search(item)),
                "No especificada",
            )
            institution = re.sub(r"^#+\s*", "", institution)
            if institution != "No especificada":
                institution_index = next(
                    (
                        offset
                        for offset, item in enumerate(before)
                        if item == institution
                    ),
                    None,
                )
                if institution_index is not None:
                    following_index = (
                        max(0, index - len(before)) + institution_index + 1
                    )
                    if (
                        following_index < index
                        and not period_pattern.search(lines[following_index])
                        and not degree_pattern.match(lines[following_index])
                    ):
                        institution = f"{institution} {lines[following_index]}"
            nearby_periods = []
            for offset, item in enumerate(after):
                # A date immediately followed by another institution starts the
                # next education entry; it does not close the current one.
                if offset + 1 < len(after) and institution_pattern.search(
                    after[offset + 1]
                ):
                    continue
                nearby_periods.extend(
                    (match, "after") for match in period_pattern.finditer(item)
                )
            if not nearby_periods:
                nearby_periods = [
                    (match, "before")
                    for item in reversed(before)
                    for match in period_pattern.finditer(item)
                ]
            start_year, end_year = "", ""
            if nearby_periods:
                period, _ = nearby_periods[0]
                start_year = period.group(1)
                end_year = (
                    "Presente"
                    if period.group(2).lower() in {"presente", "actualidad"}
                    else period.group(2)
                )
            educations.append(
                {
                    "degree": degree,
                    "institution": institution,
                    "start_year": start_year,
                    "end_year": end_year,
                }
            )
        return self._dedupe(experiences, "company"), self._dedupe(educations, "degree")

    def extract_resume_items(
        self, text: str
    ) -> tuple[list[dict], list[dict], list[dict]]:
        sources = [
            source.strip()
            for source in re.split(r"\n\s*PYPDF FALLBACK\s*\n", text)
            if source.strip()
        ]
        semantic_experiences: list[dict] = []
        semantic_educations: list[dict] = []
        experiences: list[dict] = []
        educations: list[dict] = []
        certifications: list[dict] = []
        visual_experiences: list[dict] = []
        visual_educations: list[dict] = []
        for source in sources:
            semantic_experiences.extend(self._extract_semantic_experiences(source))
            semantic_educations.extend(self._extract_semantic_educations(source))
            experiences.extend(self._extract_structured_experiences(source))
            source_educations, source_certifications = (
                self._extract_education_and_courses(source)
            )
            educations.extend(source_educations)
            certifications.extend(source_certifications)
            source_visual_experiences, source_visual_educations = (
                self._extract_visual_timeline(source)
            )
            visual_experiences.extend(source_visual_experiences)
            visual_educations.extend(source_visual_educations)

        invalid_prefixes = (
            "funciones",
            "responsabilidades",
            "jefe inmediato",
            "supervisor",
            "cargo",
        )
        merged_experiences = [
            item
            for item in [*semantic_experiences, *experiences, *visual_experiences]
            if self.fold_text(str(item.get("company", "")))
            and not self.fold_text(str(item.get("company", ""))).startswith(
                invalid_prefixes
            )
            and not self.fold_text(str(item.get("role", ""))).startswith(
                ("jefe inmediato", "funciones")
            )
        ]
        return (
            self._dedupe(merged_experiences, "company"),
            self._dedupe(
                [*semantic_educations, *visual_educations, *educations], "degree"
            ),
            self._dedupe(certifications + self._extract_certifications(text), "name"),
        )

    def embed(self, text: str) -> list[float]:
        return (
            self._vectorizer.transform([self.clean_text(text)])
            .toarray()[0]
            .astype(float)
            .tolist()
        )

    def analyze_cv(self, text: str) -> NLPResult:
        clean = self.clean_text(text)
        experiences, educations, certifications = self.extract_resume_items(text)
        return NLPResult(
            clean_text=clean,
            profession=self.extract_profession(text),
            skills=self.extract_skills(text),
            experience="\n".join(
                f"{item['role']} - {item['company']}" for item in experiences
            )
            or None,
            education="\n".join(
                f"{item['degree']} - {item['institution']}" for item in educations
            )
            or None,
            location=self.extract_location(text),
            phone=self.extract_phone(text),
            experiences=experiences,
            educations=educations,
            certifications=certifications,
            embedding=self.embed(clean),
        )

    def analyze(self, text: str) -> NLPResult:
        """Backward-compatible generic analysis used by lightweight checks."""
        return self.analyze_cv(text)

    def analyze_job(self, text: str) -> NLPResult:
        clean = self.clean_text(text)
        return NLPResult(
            clean,
            None,
            self.extract_skills(text),
            None,
            None,
            None,
            None,
            [],
            [],
            [],
            self.embed(clean),
        )

    def similarity_percentage(
        self, left: list[float] | None, right: list[float] | None
    ) -> float:
        if not left or not right:
            return 0.0
        score = cosine_similarity(
            np.array(left).reshape(1, -1), np.array(right).reshape(1, -1)
        )[0][0]
        return round(max(0.0, min(1.0, float(score))) * 100, 2)


text_processor = TextProcessor()
