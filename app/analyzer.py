from __future__ import annotations

from datetime import date

from app.models import AnalyzeDocumentResponse, AnalyzeDocumentRequest, FraudSignal
from app.validators import validate_cnpj, validate_cpf


SUSPICIOUS_KEYWORDS = {
    "photoshop": ("critical", 30, "Texto do documento contem indicio de edicao manual."),
    "amostra": ("medium", 12, "Documento marcado como amostra, o que exige revisao."),
    "sample": ("medium", 12, "Documento marcado como sample, o que exige revisao."),
    "teste": ("medium", 10, "Documento contem indicio de conteudo nao produtivo."),
    "rascunho": ("medium", 10, "Documento contem marcacao de rascunho."),
    "ficticio": ("high", 20, "Documento contem indicio de dado ficticio."),
}

REQUIRED_FIELDS = {
    "identity": ["full_name", "document_number", "birth_date"],
    "invoice": ["issuer_name", "invoice_number", "issue_date", "total_amount"],
    "proof_of_income": ["full_name", "issue_date", "gross_amount"],
}


def _parse_float(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    normalized = str(value).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _add_signal(signals: list[FraudSignal], code: str, severity: str, score_impact: int, message: str) -> None:
    signals.append(
        FraudSignal(
            code=code,
            severity=severity,
            score_impact=score_impact,
            message=message,
        )
    )


def analyze_document(request: AnalyzeDocumentRequest) -> AnalyzeDocumentResponse:
    signals: list[FraudSignal] = []
    fields = {key: value for key, value in request.fields.items()}
    text = request.extracted_text.strip()
    lowered_text = text.lower()

    for required in REQUIRED_FIELDS.get(request.document_type, []):
        if fields.get(required) in (None, "", False):
            _add_signal(
                signals,
                code=f"missing_{required}",
                severity="medium",
                score_impact=10,
                message=f"Campo obrigatorio ausente: {required}.",
            )

    if request.ocr_confidence is not None:
        if request.ocr_confidence < 0.75:
            _add_signal(signals, "low_ocr_confidence", "high", 18, "Confianca OCR baixa; documento pode estar ilegivel ou manipulado.")
        elif request.ocr_confidence < 0.88:
            _add_signal(signals, "medium_ocr_confidence", "low", 6, "Confianca OCR moderada; recomenda-se revisao humana.")

    if request.metadata.edited_after_scan:
        _add_signal(signals, "edited_after_scan", "critical", 25, "Metadado indica edicao apos a digitalizacao.")

    if request.metadata.previous_submissions >= 2:
        _add_signal(signals, "reused_document", "high", 20, "Mesmo documento foi submetido repetidas vezes.")

    if request.metadata.page_count and request.document_type == "identity" and request.metadata.page_count > 2:
        _add_signal(signals, "unexpected_page_count", "medium", 8, "Documento de identidade com quantidade de paginas incomum.")

    for keyword, (severity, impact, message) in SUSPICIOUS_KEYWORDS.items():
        if keyword in lowered_text:
            _add_signal(signals, f"keyword_{keyword}", severity, impact, message)

    cpf = fields.get("cpf")
    if isinstance(cpf, str) and cpf and not validate_cpf(cpf):
        _add_signal(signals, "invalid_cpf", "high", 22, "CPF extraido nao passou na validacao.")

    cnpj = fields.get("cnpj")
    if isinstance(cnpj, str) and cnpj and not validate_cnpj(cnpj):
        _add_signal(signals, "invalid_cnpj", "high", 22, "CNPJ extraido nao passou na validacao.")

    for date_field in ("issue_date", "birth_date", "expiration_date"):
        raw_date = fields.get(date_field)
        if isinstance(raw_date, str) and raw_date:
            try:
                parsed = date.fromisoformat(raw_date)
                if date_field in {"issue_date", "birth_date"} and parsed > date.today():
                    _add_signal(signals, f"future_{date_field}", "high", 18, f"Campo {date_field} contem data futura.")
                if date_field == "expiration_date" and parsed < date.today():
                    _add_signal(signals, "expired_document", "medium", 12, "Documento aparenta estar expirado.")
            except ValueError:
                _add_signal(signals, f"invalid_{date_field}", "medium", 10, f"Campo {date_field} nao esta em formato ISO valido.")

    total_amount = _parse_float(fields.get("total_amount"))
    subtotal = _parse_float(fields.get("subtotal"))
    fees = _parse_float(fields.get("fees")) or 0.0
    discount = _parse_float(fields.get("discount")) or 0.0
    if total_amount is not None and subtotal is not None:
        expected_total = round(subtotal + fees - discount, 2)
        if abs(expected_total - total_amount) > 0.01:
            _add_signal(signals, "amount_mismatch", "high", 20, "Total do documento nao fecha com subtotal, taxas e desconto.")

    score = min(sum(signal.score_impact for signal in signals), 100)
    if score >= 70:
        risk_level = "critical"
        recommendation = "Bloquear automacao e encaminhar para revisao antifraude."
    elif score >= 40:
        risk_level = "high"
        recommendation = "Exigir revisao humana antes de aprovar o documento."
    elif score >= 15:
        risk_level = "medium"
        recommendation = "Aprovar apenas com verificacao complementar."
    else:
        risk_level = "low"
        recommendation = "Documento com baixo risco aparente; seguir fluxo padrao."

    return AnalyzeDocumentResponse(
        document_type=request.document_type,
        risk_score=score,
        risk_level=risk_level,
        recommendation=recommendation,
        extracted_summary=fields,
        normalized_text_preview=text[:300],
        signals=signals,
    )
