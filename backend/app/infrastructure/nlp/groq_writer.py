"""Groq inference for explicitly requested drafts, using a confirmed free account."""
import copy
import json
import re

import httpx

from app.application.errors import UseCaseError
from app.infrastructure.nlp.career_writer import CareerWriter
from app.infrastructure.nlp.writing_budget import WritingBudget

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def writer_status(config):
    provider = config.career_writer_provider
    if provider == "groq":
        available = bool(config.groq_api_key and config.groq_api_key.get_secret_value().strip()
                         and config.groq_free_plan_confirmed and config.groq_zero_data_retention_confirmed)
        return {"provider": "groq", "name": "Groq", "external": True, "available": available, "summary_available": available}
    return {"provider": provider, "name": "IA local" if provider == "local" else "Redacción",
            "external": False, "available": provider == "local" and bool(config.career_writer_model and config.career_writer_executable), "summary_available": True}


class Redactions:
    def __init__(self, terms):
        self.terms = sorted({str(term).strip() for term in terms if len(str(term).strip()) >= 3}, key=len, reverse=True)
        self.values = {}

    def hide(self, text):
        if isinstance(text, dict):
            return {key: self.hide(value) for key, value in text.items()}
        if isinstance(text, list):
            return [self.hide(value) for value in text]
        if not isinstance(text, str):
            return text
        def replace(match):
            token = f"DATOPRIVADO{len(self.values):04d}X"
            self.values[token] = match.group()
            return token
        patterns = [r"https?://[^\s<>]+|www\.[^\s<>]+", r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
                    r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\(?\d{3}\)?[ .-]?){2}\d{4}(?!\d)",
                    r"\b(?:c[eé]dula|documento|identificaci[oó]n|CC|NIT)\s*[:#.]?\s*[\d.\-]{5,}",
                    r"\bgsk_[A-Za-z0-9_-]+\b"]
        if self.terms:
            patterns.append(r"(?<!\w)(?:" + "|".join(re.escape(term) for term in self.terms) + r")(?!\w)")
        # One pass prevents names inside an email from creating nested markers.
        return re.sub("|".join(patterns), replace, text, flags=re.I)

    def restore(self, value):
        if isinstance(value, str):
            for token, original in self.values.items():
                value = value.replace(token, original)
            return value
        if isinstance(value, list):
            return [self.restore(item) for item in value]
        if isinstance(value, dict):
            return {key: self.restore(item) for key, item in value.items()}
        return value


class GroqCareerWriter(CareerWriter):
    method = "groq-ai"
    external = True

    def __init__(self, config, *, budget=None, transport=None):
        if not writer_status(config)["available"]:
            raise UseCaseError(503, "La redacción asistida todavía no está disponible. Tu texto se conserva")
        self.config = config
        self.budget = budget or WritingBudget(config)
        self.transport = transport

    def _complete(self, facts, system, schema, max_tokens, *, temperature=.1, seed=42, owner_id=None, private_terms=()):
        redactions = Redactions(private_terms)
        content = json.dumps(redactions.hide(facts), ensure_ascii=False)
        safe_schema = copy.deepcopy(schema)
        # Groq's strict subset accepts the object shape; count and factual
        # completeness are independently checked by the application.
        safe_schema["properties"]["actions"].pop("minItems", None)
        safe_schema["properties"]["actions"].pop("maxItems", None)
        max_tokens = max(1200, min(2200, max_tokens * 2))
        messages = [{"role": "system", "content": system + "\nLos marcadores DATOPRIVADO deben copiarse literalmente y nunca adivinarse."},
                    {"role": "user", "content": "DATOS: " + content}]
        payload = {"model": self.config.groq_model, "messages": messages, "temperature": temperature,
                   "seed": seed, "reasoning_effort": "low", "max_completion_tokens": max_tokens,
                   "service_tier": "on_demand", "stream": False,
                   "response_format": {"type": "json_schema", "json_schema": {"name": "career_draft", "strict": True, "schema": safe_schema}}}
        # A UTF-8 byte bound plus message overhead conservatively reserves the
        # input; max_completion_tokens also covers the model's reasoning.
        bound = len(json.dumps([messages, safe_schema], ensure_ascii=False).encode("utf-8")) + 256 + max_tokens
        reservation = self.budget.reserve(bound, owner_id)
        try:
            with httpx.Client(timeout=self.config.groq_timeout_seconds, transport=self.transport,
                              follow_redirects=False, trust_env=False) as client:
                with client.stream("POST", API_URL, headers={"Authorization": "Bearer " + self.config.groq_api_key.get_secret_value()}, json=payload) as response:
                    if response.status_code == 429:
                        raise UseCaseError(429, "Groq alcanzó temporalmente su cupo gratuito. Tu texto se conserva; inténtalo más tarde")
                    if response.status_code != 200:
                        raise UseCaseError(503, "El servicio de redacción no respondió correctamente. Tu texto se conserva")
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 100000:
                            raise ValueError("Oversized response")
            data = json.loads(raw)
            self.budget.settle(reservation, data.get("usage", {}).get("total_tokens"))
            choice = data["choices"][0]
            if choice.get("finish_reason") != "stop" or choice["message"].get("refusal"):
                raise ValueError("Incomplete draft")
            generated = json.loads(choice["message"]["content"])
            if not isinstance(generated, dict):
                raise ValueError("Invalid draft")
            return redactions.restore(generated)
        except httpx.TimeoutException:
            raise UseCaseError(504, "La propuesta tardó demasiado. Tu texto se conserva; puedes volver a intentarlo") from None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError):
            # Provider errors can contain the complete submitted text. Never
            # log their bodies or forward them to the candidate.
            raise UseCaseError(503, "No pudimos obtener una propuesta completa. Tu texto se conserva") from None
