"""AI Gateway Integration for Answer Generation."""

import os
from typing import Dict, List

import requests


class AIGatewayGenerator:
    """Generate answers using AI Gateway."""

    def __init__(self, gateway_url: str = None):
        """Initialize AI Gateway client."""
        self.gateway_url = gateway_url or os.getenv(
            "AI_GATEWAY_URL", "https://ai-gateway-dakmfhg3aa-uc.a.run.app"
        )
        self.completion_endpoint = f"{self.gateway_url}/v1/completions"
        print(f"✅ AI Gateway initialized: {self.gateway_url}")

    def generate_answer(
        self,
        question: str,
        context: str,
        sources: List[Dict],
        team_id: str = "rag-service",
    ) -> str:
        """Generate answer using retrieved context."""

        # Build prompt with context and citations
        prompt = self._build_prompt(question, context, sources)

        # Call AI Gateway with correct schema
        payload = {
            "prompt": prompt,
            "team_id": team_id,
            "max_tokens": 1000,
            "temperature": 0.3,
            "routing_strategy": "quality_optimized",
            "use_cache": True,
        }

        try:
            response = requests.post(
                self.completion_endpoint, json=payload, timeout=120
            )
            response.raise_for_status()

            result = response.json()
            answer = result.get("text", "")

            # Log usage
            provider = result.get("provider", "unknown")
            cost = result.get("cost", 0)
            print(f"✅ Generated with {provider} (cost: ${cost:.4f})")

            return answer

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text if e.response else 'No response'}")
            return f"Error generating answer: {str(e)}"
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            return f"Error generating answer: {str(e)}"

    def _build_prompt(self, question: str, context: str, sources: List[Dict]) -> str:
        """Build RAG prompt with context and source attribution."""

        # List sources for citation
        source_list = "\n".join(
            [f"- {s['filename']} (relevance: {s['score']:.2f})" for s in sources]
        )

        # Build prompt with proper line breaks
        prompt = (
            "You are a supply chain expert assistant. "
            "Answer the question based ONLY on the provided context "
            "from our internal documents.\n\n"
            f"**Question:** {question}\n\n"
            f"**Context from our documents:**\n{context}\n\n"
            f"**Sources:**\n{source_list}\n\n"
            "**Instructions:**\n"
            "1. Answer the question directly and concisely\n"
            "2. Use ONLY information from the provided context\n"
            "3. If the context doesn't contain the answer, "
            'say "I don\'t have that information in our documents"\n'
            "4. Reference which documents you used "
            '(e.g., "According to our Vendor Policy...")\n'
            "5. Be specific with numbers, requirements, "
            "and procedures when mentioned\n"
            "6. Keep your answer focused and actionable\n\n"
            "**Answer:**"
        )

        return prompt


if __name__ == "__main__":
    # Test the generator
    generator = AIGatewayGenerator()

    test_question = "What are the cold chain requirements for seafood?"
    test_context = """
    [Source 1]: Temperature Control: -10°F for frozen, 32-38°F for fresh seafood.
    Traceability: Full chain of custody from catch to delivery required.
    Testing: Weekly microbiological testing required.
    """
    test_sources = [
        {
            "filename": "compliance_procedures.md",
            "score": 0.85,
            "document_id": "compliance",
        }
    ]

    answer = generator.generate_answer(test_question, test_context, test_sources)
    print(f"\n💬 Generated Answer:\n{answer}\n")
