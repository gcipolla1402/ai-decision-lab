from app.schemas.analysis import DocumentAnalysis, DocumentType, Indicator


def sample_analysis(score: int = 75) -> DocumentAnalysis:
    return DocumentAnalysis(
        summary="Synthetic test document.",
        document_type=DocumentType.REPORT,
        attention_items=["Verify the date."],
        indicators=[Indicator(name="Date", value="not detected", observed=False, evidence="No date found.")],
        completeness_score=score,
    )

