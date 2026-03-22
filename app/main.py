from fastapi import FastAPI

from app.analyzer import analyze_document
from app.azure_normalizer import normalize_azure_document_intelligence_result
from app.models import (
    AnalyzeAzureResultRequest,
    AnalyzeDocumentRequest,
    AnalyzeDocumentResponse,
)


app = FastAPI(
    title="Azure AI Anti-Fraud Document Analyzer",
    version="1.0.0",
    description="API de triagem anti-fraude para documentos, com ingestao direta ou normalizacao de saida do Azure AI Document Intelligence.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "azureai-antifraude"}


@app.post("/api/documents/analyze", response_model=AnalyzeDocumentResponse)
def analyze_document_endpoint(payload: AnalyzeDocumentRequest) -> AnalyzeDocumentResponse:
    return analyze_document(payload)


@app.post("/api/documents/analyze-azure-result", response_model=AnalyzeDocumentResponse)
def analyze_azure_result_endpoint(payload: AnalyzeAzureResultRequest) -> AnalyzeDocumentResponse:
    extracted_text, fields, ocr_confidence = normalize_azure_document_intelligence_result(payload.azure_result)
    normalized_payload = AnalyzeDocumentRequest(
        document_type=payload.document_type,
        extracted_text=extracted_text,
        fields=fields,
        ocr_confidence=ocr_confidence,
        metadata=payload.metadata,
    )
    return analyze_document(normalized_payload)
