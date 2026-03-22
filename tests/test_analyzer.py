from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_clean_identity_document_returns_low_risk() -> None:
    payload = {
        "document_type": "identity",
        "extracted_text": "Documento oficial de identificacao do titular.",
        "fields": {
            "full_name": "Maria Souza",
            "document_number": "RG1234567",
            "birth_date": "1993-04-11",
            "cpf": "529.982.247-25",
        },
        "ocr_confidence": 0.96,
        "metadata": {
            "filename": "rg-frente.png",
            "page_count": 2,
            "edited_after_scan": False,
            "previous_submissions": 0,
        },
    }

    response = client.post("/api/documents/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "low"
    assert data["risk_score"] == 0


def test_suspicious_invoice_returns_high_or_critical_risk() -> None:
    payload = {
        "document_type": "invoice",
        "extracted_text": "FATURA SAMPLE photoshop rascunho para teste interno",
        "fields": {
            "issuer_name": "Empresa Ficticia",
            "invoice_number": "NF-2025-009",
            "issue_date": "2030-01-15",
            "total_amount": "1000,00",
            "subtotal": "800,00",
            "fees": "50,00",
            "discount": "0,00",
            "cnpj": "11.111.111/1111-11",
        },
        "ocr_confidence": 0.69,
        "metadata": {
            "edited_after_scan": True,
            "previous_submissions": 3,
            "page_count": 1,
        },
    }

    response = client.post("/api/documents/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in {"high", "critical"}
    assert data["risk_score"] >= 70
    assert any(signal["code"] == "amount_mismatch" for signal in data["signals"])


def test_azure_document_intelligence_payload_is_normalized() -> None:
    payload = {
        "document_type": "invoice",
        "metadata": {
            "filename": "invoice.pdf",
            "page_count": 1,
        },
        "azure_result": {
            "content": "Invoice sample generated for review",
            "documents": [
                {
                    "fields": {
                        "issuer_name": {"content": "ACME LTDA", "confidence": 0.98},
                        "invoice_number": {"content": "FAT-0099", "confidence": 0.97},
                        "issue_date": {"valueDate": "2025-03-01", "confidence": 0.96},
                        "total_amount": {"valueCurrency": {"amount": 1500.0}, "confidence": 0.95},
                        "cnpj": {"content": "45.723.174/0001-10", "confidence": 0.94},
                    }
                }
            ],
        },
    }

    response = client.post("/api/documents/analyze-azure-result", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "invoice"
    assert data["extracted_summary"]["issuer_name"] == "ACME LTDA"
    assert data["risk_level"] in {"low", "medium"}
