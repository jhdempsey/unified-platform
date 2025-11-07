"""
RAG Query Tool
Query the RAG service for supply chain documentation
"""

import logging
import os
from typing import Any, Dict

import httpx
from base_tool import BaseTool, ToolParameter

logger = logging.getLogger(__name__)


class RAGQueryTool(BaseTool):
    """Query the RAG service for supply chain documentation"""

    name = "query_documentation"
    description = (
        "Search supply chain policies, procedures, compliance documentation, "
        "and best practices. Returns relevant information with source citations."
    )
    parameters = [
        ToolParameter(
            name="question",
            type="string",
            description=(
                "Natural language question about supply chain policies, "
                "procedures, compliance, or operational guidelines"
            ),
            required=True,
        ),
        ToolParameter(
            name="max_results",
            type="number",
            description="Maximum number of relevant documents to return (default: 3)",
            required=False,
        ),
    ]
    version = "1.0.0"

    def __init__(self):
        self.rag_url = os.getenv(
            "RAG_SERVICE_URL", "https://rag-service-dakmfhg3aa-uc.a.run.app"
        )
        logger.info(f"RAG Query Tool initialized with URL: {self.rag_url}")

    async def execute(
        self, arguments: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute RAG query"""

        # Validate arguments
        self.validate_arguments(arguments)

        question = arguments.get("question")
        max_results = arguments.get("max_results", 3)

        logger.info(f"Querying RAG service: {question}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rag_url}/query",
                    json={"question": question, "max_results": max_results},
                    timeout=120.0,
                )
                response.raise_for_status()
                rag_result = response.json()

            logger.info(
                f"RAG query successful, got {len(rag_result.get('sources', []))} sources"  # noqa: E501
            )

            # Format for agent consumption
            return {
                "answer": rag_result.get("answer", "No answer found"),
                "sources": [
                    {
                        "filename": src.get("filename", "Unknown"),
                        "relevance_score": round(src.get("score", 0), 3),
                        "excerpt": src.get("text", "")[:300],  # First 300 chars
                        "page": src.get("page"),
                    }
                    for src in rag_result.get("sources", [])[:max_results]
                ],
                "confidence": self._calculate_confidence(rag_result),
                "query": question,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"RAG service HTTP error: {e}")
            raise Exception(
                f"RAG service returned error: {e.response.status_code}"
            ) from e

        except httpx.RequestError as e:
            logger.error(f"RAG service connection error: {e}")
            raise Exception(f"Could not connect to RAG service: {str(e)}") from e

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            raise

    def _calculate_confidence(self, result: Dict[str, Any]) -> str:
        """Calculate confidence level based on source scores"""
        sources = result.get("sources", [])

        if not sources:
            return "low"

        avg_score = sum(s.get("score", 0) for s in sources) / len(sources)

        if avg_score > 0.8:
            return "high"
        elif avg_score > 0.6:
            return "medium"
        else:
            return "low"
