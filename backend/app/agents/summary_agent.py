from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.ollama_service import OllamaService


class BilingualSummary(BaseModel):
    english: str = Field(min_length=1, max_length=1200)
    gujarati: str = Field(min_length=1, max_length=1600)


def _fallback(case: dict, counts: dict) -> dict[str, str]:
    english = (f"{case['case_number']} contains {counts.get('documents', 0)} document(s) and {counts.get('pages', 0)} page(s). "
               f"The workspace has identified {counts.get('claims', 0)} candidate claim(s) and {counts.get('evidence', 0)} evidence reference(s). "
               "All machine-extracted findings remain decision-support material and should be checked against cited source pages.")
    gujarati = (f"કેસ {case['case_number']} માં {counts.get('documents', 0)} દસ્તાવેજ અને {counts.get('pages', 0)} પાનાં છે. "
                f"વર્કસ્પેસમાં {counts.get('claims', 0)} સંભવિત દાવા અને {counts.get('evidence', 0)} પુરાવા સંદર્ભો મળ્યા છે. "
                "મશીન દ્વારા કાઢવામાં આવેલા તમામ તારણો નિર્ણય-સહાયક છે અને સ્ત્રોત પાનાં સામે તપાસવા જોઈએ.")
    return {"english": english, "gujarati": gujarati}


def case_summary(case: dict, counts: dict, source_text: str = "") -> dict[str, str]:
    fallback = _fallback(case, counts)
    if not source_text.strip():
        return fallback
    prompt = f"""Create a cautious bilingual investigation workspace summary from the supplied case record.
Return JSON matching the schema: english and gujarati. Write 2-4 concise sentences in each language.
Only state allegations or extracted information as allegations/records; never state guilt or invent facts.
Mention important missing or unverified information when evident. Preserve case identifiers exactly.
English must be natural professional English. Gujarati must be natural Gujarati script.
CASE METRICS: {counts}
CASE RECORD EXCERPTS:\n{source_text[:12000]}"""
    try:
        result = OllamaService().structured(prompt, BilingualSummary, temperature=0.1)
        return result.model_dump()
    except Exception:
        return fallback

