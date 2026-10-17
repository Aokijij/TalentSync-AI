"""Infer only explicitly stated hiring priorities and skill levels."""

import re

from app.domain.services.skill_context import VARIANTS, fold
from app.domain.services.skills import skill_key

LEVELS = [
    ("expert", r"expert[oa]?s?|expertise"),
    ("advanced", r"avanzad[oa]s?|advanced"),
    ("intermediate", r"intermedi[oa]s?|intermediate"),
    ("basic", r"basic[oa]s?|basics?|principiante|fundamentos"),
]
OPTIONAL = r"\b(?:deseables?|opcional(?:es)?|preferibles?|valorables?|se valora|aprendible|puede aprender|no (?:es |se )?(?:obligatori[oa]|necesari[oa]|indispensable|exige|requiere))\b"
REQUIRED = r"\b(?:esencial(?:es)?|obligatori[oa]s?|indispensables?|imprescindibles?|necesari[oa]s?|requerid[oa]s?|se requiere|se exige|debe dominar)\b"


def _priority(text):
    return (
        False
        if re.search(OPTIONAL, text)
        else True
        if re.search(REQUIRED, text)
        else None
    )


def _level(text):
    return next(
        (level for level, pattern in LEVELS if re.search(rf"\b(?:{pattern})\b", text)),
        None,
    )


def infer_offer_skills(text, detected):
    aliases = {}
    for name in detected:
        key = skill_key(name)
        base = re.sub(
            r"\s+(?:nivel\s+)?(?:basico|intermedio|avanzado|experto|basic|intermediate|advanced|expert)$",
            "",
            key,
        ).strip()
        aliases.setdefault(base, set()).update(
            [fold(name), base, *VARIANTS.get(base, [])]
        )
    rows = {
        key: {
            "skill": key,
            "essential": False,
            "level": "basic",
            "weight": 1,
            "context_detected": False,
        }
        for key in aliases
    }
    heading = heading_level = None
    for line in fold(text).splitlines():
        if (
            len(line.strip()) < 70
            and ":" not in line.rstrip(": ")
            and (_priority(line) is not None or _level(line))
            and not any(
                re.search(rf"(?<!\w){re.escape(name)}(?!\w)", line)
                for names in aliases.values()
                for name in names
            )
        ):
            heading = _priority(line)
            heading_level = _level(line)
            continue
        for clause in re.split(r"[;!?•]|\.(?=\s|$)", line):
            mentions = []
            for key, names in aliases.items():
                # Prefer the base name so a following level remains in its local context.
                terms = sorted({fold(name) for name in names}, key=len)
                pattern = (
                    r"(?<![\w+#])(?:"
                    + "|".join(re.escape(name) for name in terms)
                    + r")(?![\w+#])"
                )
                mentions += [
                    (match.start(), match.end(), key)
                    for match in re.finditer(pattern, clause)
                ]
            mentions.sort()
            common = clause[: mentions[0][0]] if mentions else ""
            for index, (start, end, key) in enumerate(mentions):
                before = clause[mentions[index - 1][1] if index else 0 : start]
                after = clause[
                    end : mentions[index + 1][0]
                    if index + 1 < len(mentions)
                    else len(clause)
                ]
                local = (
                    re.split(r",|\by\b", before)[-1]
                    + " "
                    + re.split(r",|\by\b", after)[0]
                )
                priority, level = _priority(local), _level(local)
                if priority is None:
                    priority = (
                        _priority(common) if _priority(common) is not None else heading
                    )
                level = level or _level(common) or heading_level
                row = rows[key]
                if priority is not None:
                    row["essential"] = priority
                if level:
                    row["level"] = level
                row["context_detected"] |= priority is not None or level is not None
    return list(rows.values())
