from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.models.context_element import ContextElement
from app.services.gemini_service import GeminiService, get_gemini_service
from app.utils.token_counter import TokenCounter


@dataclass
class AnalysisResult:
    quality_score: float
    topic_consistency: float
    logical_flow: float
    information_redundancy: float
    token_efficiency: float
    issues: list[str]
    recommendations: list[str]


class ContextAnalyzer:
    """Analyze context quality using local heuristics and optional Gemini feedback."""

    _WORD_PATTERN = re.compile(r"\b[a-zA-Z]{3,}\b")
    _STOP_WORDS = {
        "about",
        "after",
        "again",
        "also",
        "because",
        "been",
        "before",
        "between",
        "could",
        "context",
        "does",
        "from",
        "have",
        "into",
        "just",
        "more",
        "need",
        "only",
        "should",
        "some",
        "such",
        "than",
        "that",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "very",
        "what",
        "when",
        "where",
        "which",
        "with",
        "would",
        "your",
    }
    _FLOW_SCORES = {
        ("system", "user"): 1.0,
        ("system", "assistant"): 0.9,
        ("user", "assistant"): 1.0,
        ("assistant", "user"): 0.9,
        ("assistant", "tool"): 0.75,
        ("tool", "assistant"): 1.0,
        ("user", "tool"): 0.5,
        ("assistant", "assistant"): 0.55,
        ("user", "user"): 0.45,
        ("tool", "tool"): 0.4,
    }

    def __init__(
        self,
        gemini_service: GeminiService | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.gemini = gemini_service
        self.token_counter = token_counter or TokenCounter()

    async def analyze(self, elements: list[ContextElement]) -> AnalysisResult:
        ordered_elements = [element for element in elements if element.content.strip()]
        if not ordered_elements:
            return AnalysisResult(
                quality_score=0.0,
                topic_consistency=0.0,
                logical_flow=0.0,
                information_redundancy=0.0,
                token_efficiency=0.0,
                issues=["No context elements were provided for analysis."],
                recommendations=[
                    "Add the key user requirements, constraints, and recent decisions to the window."
                ],
            )

        topic_consistency = self._calculate_topic_consistency(ordered_elements)
        logical_flow = self._calculate_logical_flow(ordered_elements)
        information_redundancy = self._calculate_information_redundancy(ordered_elements)
        token_efficiency = self._calculate_token_efficiency(
            ordered_elements,
            information_redundancy,
        )
        quality_score = self._calculate_quality_score(
            topic_consistency=topic_consistency,
            logical_flow=logical_flow,
            information_redundancy=information_redundancy,
            token_efficiency=token_efficiency,
        )

        issues = self._collect_local_issues(
            topic_consistency=topic_consistency,
            logical_flow=logical_flow,
            information_redundancy=information_redundancy,
            token_efficiency=token_efficiency,
        )
        recommendations = self._collect_local_recommendations(
            topic_consistency=topic_consistency,
            logical_flow=logical_flow,
            information_redundancy=information_redundancy,
            token_efficiency=token_efficiency,
            elements=ordered_elements,
        )

        ai_feedback = await self._request_ai_feedback(
            elements=ordered_elements,
            metrics={
                "quality_score": quality_score,
                "topic_consistency": topic_consistency,
                "logical_flow": logical_flow,
                "information_redundancy": information_redundancy,
                "token_efficiency": token_efficiency,
            },
            issues=issues,
            recommendations=recommendations,
        )

        return AnalysisResult(
            quality_score=round(quality_score, 2),
            topic_consistency=round(topic_consistency, 3),
            logical_flow=round(logical_flow, 3),
            information_redundancy=round(information_redundancy, 3),
            token_efficiency=round(token_efficiency, 3),
            issues=self._deduplicate_strings(issues + ai_feedback.get("issues", [])),
            recommendations=self._deduplicate_strings(
                recommendations + ai_feedback.get("recommendations", [])
            ),
        )

    def _build_analysis_prompt(
        self,
        elements: list[ContextElement],
        metrics: dict[str, float],
        issues: list[str],
        recommendations: list[str],
    ) -> str:
        serialized_elements = "\n".join(
            f"- role={element.role.value} tokens={self._estimate_tokens(element)} "
            f"content={self._truncate(element.content.strip(), 400)}"
            for element in elements
        )
        serialized_issues = "\n".join(f"- {issue}" for issue in issues) or "- None"
        serialized_recommendations = (
            "\n".join(f"- {recommendation}" for recommendation in recommendations) or "- None"
        )

        return f"""
You are analyzing the quality of an AI context window.
Review the context and provide concise, actionable findings.

Metrics already computed locally:
- quality_score: {metrics["quality_score"]:.2f} / 100
- topic_consistency: {metrics["topic_consistency"]:.3f}
- logical_flow: {metrics["logical_flow"]:.3f}
- information_redundancy: {metrics["information_redundancy"]:.3f}
- token_efficiency: {metrics["token_efficiency"]:.3f}

Current locally detected issues:
{serialized_issues}

Current locally detected recommendations:
{serialized_recommendations}

Context elements:
{serialized_elements}

Return a JSON object with:
- issues: array of up to 5 short strings
- recommendations: array of up to 5 short strings

Focus on missing requirements, weak transitions, redundant content, and ways to improve context quality.
Do not repeat the exact same sentence if a local suggestion already covers it.
""".strip()

    def _calculate_topic_consistency(self, elements: list[ContextElement]) -> float:
        keyword_sets = [self._extract_keywords(element.content) for element in elements]
        non_empty_sets = [keywords for keywords in keyword_sets if keywords]
        if not non_empty_sets:
            return 0.0
        if len(non_empty_sets) == 1:
            return 1.0

        adjacent_scores: list[float] = []
        for current, following in zip(non_empty_sets, non_empty_sets[1:]):
            adjacent_scores.append(self._jaccard_similarity(current, following))

        counter = Counter(word for keywords in non_empty_sets for word in keywords)
        anchor_terms = {word for word, count in counter.items() if count >= 2}
        if anchor_terms:
            anchor_coverage = sum(
                len(keywords & anchor_terms) / len(anchor_terms) for keywords in non_empty_sets
            ) / len(non_empty_sets)
        else:
            anchor_coverage = 0.45

        return self._clamp((sum(adjacent_scores) / len(adjacent_scores)) * 0.55 + anchor_coverage * 0.45)

    def _calculate_logical_flow(self, elements: list[ContextElement]) -> float:
        if len(elements) == 1:
            first_role = elements[0].role.value
            return 1.0 if first_role in {"system", "user"} else 0.7

        start_score = 1.0 if elements[0].role.value in {"system", "user"} else 0.65
        transition_scores = [
            self._FLOW_SCORES.get((current.role.value, following.role.value), 0.35)
            for current, following in zip(elements, elements[1:])
        ]
        return self._clamp(start_score * 0.25 + (sum(transition_scores) / len(transition_scores)) * 0.75)

    def _calculate_information_redundancy(self, elements: list[ContextElement]) -> float:
        normalized_contents = [self._normalize_text(element.content) for element in elements]
        comparable_pairs = 0
        duplicate_signal = 0.0

        for index, content in enumerate(normalized_contents):
            if not content:
                continue

            words = set(content.split())
            for following in normalized_contents[index + 1 :]:
                if not following:
                    continue

                comparable_pairs += 1
                following_words = set(following.split())
                if content == following or content in following or following in content:
                    duplicate_signal += 1.0
                    continue

                duplicate_signal += self._jaccard_similarity(words, following_words)

        if comparable_pairs == 0:
            return 0.0

        return self._clamp(duplicate_signal / comparable_pairs)

    def _calculate_token_efficiency(
        self,
        elements: list[ContextElement],
        information_redundancy: float,
    ) -> float:
        total_tokens = sum(self._estimate_tokens(element) for element in elements)
        if total_tokens == 0:
            return 0.0

        meaningful_words = [
            word
            for element in elements
            for word in self._extract_keywords(element.content)
        ]
        density = len(set(meaningful_words)) / total_tokens
        normalized_density = self._clamp(density * 4.0)

        return self._clamp(normalized_density * 0.6 + (1.0 - information_redundancy) * 0.4)

    def _calculate_quality_score(
        self,
        *,
        topic_consistency: float,
        logical_flow: float,
        information_redundancy: float,
        token_efficiency: float,
    ) -> float:
        weighted_score = (
            topic_consistency * 0.35
            + logical_flow * 0.25
            + (1.0 - information_redundancy) * 0.2
            + token_efficiency * 0.2
        )
        return self._clamp(weighted_score) * 100.0

    def _collect_local_issues(
        self,
        *,
        topic_consistency: float,
        logical_flow: float,
        information_redundancy: float,
        token_efficiency: float,
    ) -> list[str]:
        issues: list[str] = []
        if topic_consistency < 0.8:
            issues.append("The context drifts across multiple topics without a stable anchor.")
        if logical_flow < 0.7:
            issues.append("The message sequence has weak transitions that may confuse downstream models.")
        if information_redundancy > 0.3:
            issues.append("Repeated information is consuming context budget without adding much value.")
        if token_efficiency < 0.7:
            issues.append("The current token usage is not carrying enough unique signal.")
        return issues

    def _collect_local_recommendations(
        self,
        *,
        topic_consistency: float,
        logical_flow: float,
        information_redundancy: float,
        token_efficiency: float,
        elements: list[ContextElement],
    ) -> list[str]:
        recommendations: list[str] = []
        if topic_consistency < 0.8:
            recommendations.append("Add a brief summary of the primary task and keep later messages aligned to it.")
        if logical_flow < 0.7:
            recommendations.append("Reorder the context so user intent, constraints, and latest assistant state appear in sequence.")
        if information_redundancy > 0.3:
            recommendations.append("Merge duplicate statements and keep only the most recent authoritative version.")
        if token_efficiency < 0.7:
            recommendations.append("Replace verbose passages with short factual bullets that preserve decisions and constraints.")
        if not any(element.role.value == "system" for element in elements):
            recommendations.append("Include a concise system instruction so the model sees stable operating rules first.")
        return recommendations

    async def _request_ai_feedback(
        self,
        *,
        elements: list[ContextElement],
        metrics: dict[str, float],
        issues: list[str],
        recommendations: list[str],
    ) -> dict[str, list[str]]:
        if self.gemini is None:
            return {"issues": [], "recommendations": []}

        prompt = self._build_analysis_prompt(elements, metrics, issues, recommendations)
        try:
            response = self.gemini.generate_json(prompt)
        except Exception:
            return {"issues": [], "recommendations": []}

        return {
            "issues": self._normalize_string_list(response.get("issues")),
            "recommendations": self._normalize_string_list(response.get("recommendations")),
        }

    def _estimate_tokens(self, element: ContextElement) -> int:
        if element.token_count > 0:
            return element.token_count
        return self.token_counter.count(element.content)

    def _extract_keywords(self, content: str) -> set[str]:
        normalized = self._normalize_text(content)
        return {
            word
            for word in self._WORD_PATTERN.findall(normalized)
            if word not in self._STOP_WORDS
        }

    @staticmethod
    def _normalize_text(content: str) -> str:
        return " ".join(content.lower().split())

    @staticmethod
    def _jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 1.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    @staticmethod
    def _normalize_string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    @staticmethod
    def _deduplicate_strings(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduplicated: list[str] = []
        for value in values:
            key = value.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduplicated.append(value.strip())
        return deduplicated

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return f"{value[: max_length - 3].rstrip()}..."

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))


def get_context_analyzer(settings: Settings | None = None) -> ContextAnalyzer:
    """Create a context analyzer with an optional Gemini dependency."""
    app_settings = settings or get_settings()
    gemini_service = None
    if app_settings.gemini_api_key:
        gemini_service = get_gemini_service(app_settings)
    return ContextAnalyzer(gemini_service=gemini_service)


__all__ = ["AnalysisResult", "ContextAnalyzer", "get_context_analyzer"]
