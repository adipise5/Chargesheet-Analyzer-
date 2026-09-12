from __future__ import annotations


LABELS = {
    "fir": ("first information report", "fir", "પ્રથમ માહિતી"),
    "witness_statement": ("witness statement", "statement of witness", "સાક્ષી"),
    "panchnama": ("panchnama", "પંચનામું", "પંચનામા"),
    "seizure_memo": ("seizure", "જપ્તી"),
    "medical_report": ("medical report", "postmortem", "મેડિકલ"),
    "fsl_report": ("forensic science", "fsl"),
    "cdr": ("call detail record", "cdr"),
    "cctv_record": ("cctv", "camera export", "video recording"),
    "case_diary": ("case diary", "investigation diary", "કેસ ડાયરી"),
    "chargesheet": ("charge sheet", "chargesheet", "આરોપનામું"),
}


def classify_document(text: str) -> tuple[str, float]:
    haystack = text.casefold()
    scores = {label: sum(token in haystack for token in tokens) for label, tokens in LABELS.items()}
    best = max(scores, key=scores.get, default="unknown")
    return (best, min(0.95, 0.55 + scores[best] * 0.15)) if scores.get(best, 0) else ("unknown", 0.35)

