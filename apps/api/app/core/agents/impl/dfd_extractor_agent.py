"""
DFD Extractor Agent

Modular agent that extracts DFD components from raw document text and outputs
validated JSON matching the DFDComponents schema. Mirrors the behavior of
core pipeline dfd_extraction_service but packaged as a reusable agent.
"""

from typing import Any, Optional, Tuple, Dict
from app.core.agents.base import BaseAgent, AgentMetadata, AgentCategory, AgentExecutionContext
from app.core.pipeline.dfd_extraction_service import extract_dfd_from_text
from app.models.dfd import DFDComponents


class DFDExtractorAgent(BaseAgent):
    """Agent that extracts DFD components from provided document text."""

    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="dfd_extractor",
            version="1.0.0",
            description="Extracts DFD components (entities, processes, assets, flows, boundaries) from document text",
            category=AgentCategory.ARCHITECTURE,
            priority=15,
            requires_document=True,
            requires_components=False,
            estimated_tokens=3000,
            enabled_by_default=True,
            legacy_equivalent=None,
        )

    async def extract(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None,
    ) -> Tuple[DFDComponents, Dict[str, Any]]:
        """
        Perform DFD extraction using the configured LLM provider.

        Returns a tuple of (DFDComponents model, token_usage/metadata dict).
        """
        if not context.document_text:
            # Return empty structure with note (defensive)
            empty = DFDComponents(
                project_name="No Document Provided",
                project_version="1.0",
                industry_context="",
                external_entities=[],
                assets=[],
                processes=[],
                trust_boundaries=[],
                data_flows=[],
            )
            return empty, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "total_cost_usd": 0.0}

        # Delegate to the existing extraction service for consistent behavior
        dfd_components, token_usage = await extract_dfd_from_text(
            llm_provider=llm_provider,
            document_text=context.document_text,
            use_instructor=True,
        )
        return dfd_components, token_usage



