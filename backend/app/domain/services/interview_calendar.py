"""Private, manual calendar export (RFC 5545); never sends invitations."""

from datetime import datetime, timezone
from hashlib import sha256


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _date(value: datetime) -> str:
    return utc(value).strftime("%Y%m%dT%H%M%SZ")


def _text(value: str) -> str:
    # TEXT values must not be able to inject properties/components.
    value = "".join(char for char in value if char in "\r\n\t" or ord(char) >= 32)
    return value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def _fold(line: str) -> str:
    # Fold at 75 octets, preserving UTF-8 code points. Continuation space counts.
    lines, part, size = [], "", 0
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > 75:
            lines.append(part)
            part, size = " ", 1
        part += char
        size += width
    lines.append(part)
    return "\r\n".join(lines)


def interview_calendar(*, application_id: int, created_at: datetime, interview_at: datetime,
                       job_title: str, company_name: str, process_url: str, version: int,
                       now: datetime | None = None) -> bytes:
    uid = sha256(f"{application_id}:{_date(created_at)}:{process_url}".encode()).hexdigest()
    description = ("Consulta el proceso para confirmar duración, modalidad y acceso a la entrevista. "
                   "Esta copia no se sincroniza: si la cita cambia o se cancela, actualiza tu calendario.\n"
                   f"Proceso: {process_url}")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//TalentSync//Agenda de entrevistas//ES",
             "CALSCALE:GREGORIAN", "BEGIN:VEVENT", f"UID:{uid}@talentsync",
             f"DTSTAMP:{_date(now or datetime.now(timezone.utc))}", f"SEQUENCE:{version}",
             f"DTSTART:{_date(interview_at)}", f"SUMMARY:{_text(f'Entrevista · {job_title} · {company_name}')}",
             f"DESCRIPTION:{_text(description)}", "CLASS:PRIVATE", "STATUS:CONFIRMED",
             # End time/location are intentionally omitted: they are not scheduled facts.
             "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-PT30M", "DESCRIPTION:Entrevista en 30 minutos",
             "END:VALARM", "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(_fold(line) for line in lines) + "\r\n").encode("utf-8")
