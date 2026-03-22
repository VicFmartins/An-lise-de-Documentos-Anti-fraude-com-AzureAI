from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    filename: str | None = None
    mime_type: str | None = None
    page_count: int | None = Field(default=None, ge=1)
    edited_after_scan: bool = False
    previous_submissions: int = Field(default=0, ge=0)


class AnalyzeDocumentRequest(BaseModel):
    document_type: str = Field(description="identity, invoice, proof_of_income ou other")
    extracted_text: str = ""
    fields: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class AnalyzeAzureResultRequest(BaseModel):
    document_type: str = Field(description="identity, invoice, proof_of_income ou other")
    azure_result: dict
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class FraudSignal(BaseModel):
    code: str
    severity: str
    score_impact: int
    message: str


class AnalyzeDocumentResponse(BaseModel):
    document_type: str
    risk_score: int
    risk_level: str
    recommendation: str
    extracted_summary: dict[str, str | int | float | bool | None]
    normalized_text_preview: str
    signals: list[FraudSignal]
