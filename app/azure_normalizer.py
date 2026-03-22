from __future__ import annotations


def _flatten_field_value(field: dict) -> str | int | float | bool | None:
    for key in ("content", "valueString", "valueDate", "valueTime", "valuePhoneNumber", "valueCurrency"):
        value = field.get(key)
        if value is not None:
            if isinstance(value, dict) and "amount" in value:
                return value["amount"]
            return value
    if "valueNumber" in field and field["valueNumber"] is not None:
        return field["valueNumber"]
    if "valueBoolean" in field and field["valueBoolean"] is not None:
        return field["valueBoolean"]
    if "valueInteger" in field and field["valueInteger"] is not None:
        return field["valueInteger"]
    return field.get("content")


def normalize_azure_document_intelligence_result(payload: dict) -> tuple[str, dict[str, str | int | float | bool | None], float | None]:
    content = payload.get("content", "") or ""
    documents = payload.get("documents", []) or []
    fields: dict[str, str | int | float | bool | None] = {}
    confidences: list[float] = []

    if documents:
        first_document = documents[0]
        for key, value in (first_document.get("fields") or {}).items():
            if isinstance(value, dict):
                fields[key] = _flatten_field_value(value)
                confidence = value.get("confidence")
                if isinstance(confidence, (int, float)):
                    confidences.append(float(confidence))

    if not content:
        paragraphs = payload.get("paragraphs") or []
        content = " ".join(item.get("content", "") for item in paragraphs if isinstance(item, dict))

    average_confidence = None
    if confidences:
        average_confidence = round(sum(confidences) / len(confidences), 4)

    return content.strip(), fields, average_confidence
