from __future__ import annotations

import asyncio
import enum
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.models.context_element import ContextElement, ContextElementRole
from app.services.context_analyzer import ContextAnalyzer, get_context_analyzer
from app.services.gemini_service import GeminiService, get_gemini_service
from app.utils.token_counter import TokenCounter


class OptimizationType(str, enum.Enum):
    TOKEN_REDUCTION = "token_reduction"
    CLARITY_IMPROVEMENT = "clarity_improvement"
    RELEVANCE_ENHANCEMENT = "relevance_enhancement"
    REDUNDANCY_REMOVAL = "redundancy_removal"
    STRUCTURE_OPTIMIZATION = "structure_optimization"


@dataclass
class OptimizationResult:
    original_elements: list[ContextElement]
    optimized_elements: list[ContextElement]
    strategy_used: OptimizationType
    token_savings: int
    quality_improvement: float


class OptimizationStrategy(ABC):
    _WORD_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b")
    _SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
    _ACK_PATTERN = re.compile(
        r"^(ok|okay|sure|noted|done|thanks|thank you|understood|will do|sounds good)[.!]?$",
        re.IGNORECASE,
    )
    _STOP_WORDS = {
        "about",
        "and",
        "after",
        "again",
        "also",
        "are",
        "because",
        "been",
        "before",
        "between",
        "build",
        "change",
        "context",
        "does",
        "from",
        "have",
        "into",
        "just",
        "more",
        "need",
        "only",
        "project",
        "should",
        "some",
        "such",
        "the",
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
        "will",
        "with",
        "would",
        "your",
    }
    _ROLE_ORDER = {
        ContextElementRole.SYSTEM: 0,
        ContextElementRole.USER: 1,
        ContextElementRole.ASSISTANT: 2,
        ContextElementRole.TOOL: 3,
    }

    def __init__(
        self,
        *,
        token_counter: TokenCounter | None = None,
        gemini_service: GeminiService | None = None,
    ) -> None:
        self.token_counter = token_counter or TokenCounter()
        self.gemini = gemini_service

    @abstractmethod
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        pass

    def _estimate_tokens(self, element: ContextElement) -> int:
        if element.token_count > 0:
            return element.token_count
        return self.token_counter.count(element.content)

    def _update_tokens(self, element: ContextElement) -> ContextElement:
        element.token_count = self.token_counter.count(element.content)
        return element

    def _clone_element(
        self,
        element: ContextElement,
        *,
        content: str | None = None,
        role: ContextElementRole | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextElement:
        clone = ContextElement(
            window_id=element.window_id,
            role=role or element.role,
            content=(content if content is not None else element.content).strip(),
            token_count=0,
            metadata_=dict(element.metadata_ if metadata is None else metadata),
        )
        return self._update_tokens(clone)

    @staticmethod
    def _normalize_text(content: str) -> str:
        return " ".join(content.lower().split())

    def _extract_keywords(self, content: str) -> set[str]:
        normalized = self._normalize_text(content)
        return {
            word
            for word in self._WORD_PATTERN.findall(normalized)
            if word not in self._STOP_WORDS
        }

    def _split_sentences(self, content: str) -> list[str]:
        chunks = [chunk.strip(" -\t") for chunk in self._SENTENCE_PATTERN.split(content.strip())]
        return [chunk for chunk in chunks if chunk]

    @staticmethod
    def _jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 1.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _content_similarity(self, left: str, right: str) -> float:
        left_normalized = self._normalize_text(left)
        right_normalized = self._normalize_text(right)
        if not left_normalized and not right_normalized:
            return 1.0
        if (
            left_normalized == right_normalized
            or left_normalized in right_normalized
            or right_normalized in left_normalized
        ):
            return 1.0

        left_keywords = self._extract_keywords(left_normalized)
        right_keywords = self._extract_keywords(right_normalized)
        keyword_score = self._jaccard_similarity(left_keywords, right_keywords)

        left_sentences = {self._normalize_text(sentence) for sentence in self._split_sentences(left)}
        right_sentences = {self._normalize_text(sentence) for sentence in self._split_sentences(right)}
        sentence_score = self._jaccard_similarity(left_sentences, right_sentences)
        return max(keyword_score, sentence_score * 0.9)

    def _priority_score(
        self,
        element: ContextElement,
        *,
        index: int,
        total_elements: int,
        anchor_keywords: set[str] | None = None,
    ) -> float:
        base = {
            ContextElementRole.SYSTEM: 3.5,
            ContextElementRole.USER: 3.0,
            ContextElementRole.ASSISTANT: 2.2,
            ContextElementRole.TOOL: 1.1,
        }[element.role]
        keywords = self._extract_keywords(element.content)
        overlap = 0.0
        if anchor_keywords:
            overlap = self._jaccard_similarity(keywords, anchor_keywords) * 2.5
        density = min(len(keywords) / max(self._estimate_tokens(element), 1), 0.25) * 4.0
        recency = (index + 1) / max(total_elements, 1)
        explicit_priority = self._parse_priority(element.metadata_.get("priority"))
        acknowledgement_penalty = 1.5 if self._ACK_PATTERN.match(element.content.strip()) else 0.0
        return base + overlap + density + explicit_priority + recency - acknowledgement_penalty

    @staticmethod
    def _parse_priority(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "high":
                return 1.5
            if normalized == "medium":
                return 0.75
            if normalized == "low":
                return 0.0
        return 0.0

    def _choose_anchor_keywords(self, elements: list[ContextElement]) -> set[str]:
        prioritized = [
            element
            for element in elements
            if element.role in {ContextElementRole.SYSTEM, ContextElementRole.USER}
        ]
        source = prioritized or elements
        counter = Counter(keyword for element in source for keyword in self._extract_keywords(element.content))
        repeated_keywords = {word for word, count in counter.items() if count >= 2}
        if repeated_keywords:
            return repeated_keywords
        if source:
            return self._extract_keywords(source[0].content)
        return {word for word, _ in counter.most_common(12)}

    def _deduplicate_elements(
        self,
        elements: list[ContextElement],
        *,
        threshold: float,
        merge: bool,
    ) -> list[ContextElement]:
        groups: list[tuple[int, list[ContextElement]]] = []

        for element in elements:
            placed = False
            for _, group in groups:
                representative = group[0]
                if representative.role != element.role:
                    continue
                if self._content_similarity(representative.content, element.content) >= threshold:
                    group.append(element)
                    placed = True
                    break
            if not placed:
                groups.append((len(groups), [element]))

        optimized: list[ContextElement] = []
        for _, group in groups:
            if len(group) == 1:
                optimized.append(self._clone_element(group[0]))
                continue

            if merge:
                optimized.append(self._merge_group(group))
            else:
                optimized.append(self._clone_element(group[-1]))
        return optimized

    def _merge_group(self, group: list[ContextElement]) -> ContextElement:
        sentences: list[str] = []
        seen_sentences: set[str] = set()
        for element in group:
            for sentence in self._split_sentences(element.content):
                normalized = self._normalize_text(sentence)
                if not normalized or normalized in seen_sentences:
                    continue
                seen_sentences.add(normalized)
                sentences.append(sentence.strip())

        representative = max(
            group,
            key=lambda element: (
                self._priority_score(element, index=0, total_elements=len(group)),
                self._estimate_tokens(element),
            ),
        )
        if not sentences:
            content = representative.content
        elif len(sentences) == 1:
            content = sentences[0]
        else:
            content = "\n".join(f"- {sentence}" for sentence in sentences[:6])

        metadata = dict(representative.metadata_)
        metadata["merged_from"] = len(group)
        return self._clone_element(representative, content=content, metadata=metadata)

    def _compact_text_locally(
        self,
        content: str,
        *,
        max_sentences: int,
        max_tokens: int | None = None,
        anchor_keywords: set[str] | None = None,
    ) -> str:
        sentences = self._split_sentences(content)
        if not sentences:
            return content.strip()

        unique_sentences: list[str] = []
        seen: set[str] = set()
        for sentence in sentences:
            normalized = self._normalize_text(sentence)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_sentences.append(sentence.strip())

        scored = []
        for index, sentence in enumerate(unique_sentences):
            keywords = self._extract_keywords(sentence)
            score = len(keywords)
            if anchor_keywords:
                score += self._jaccard_similarity(keywords, anchor_keywords) * 8.0
            if re.search(r"\d", sentence):
                score += 1.0
            if ":" in sentence:
                score += 0.5
            scored.append((score, index, sentence))

        selected = [
            sentence
            for _, _, sentence in sorted(scored, key=lambda item: (-item[0], item[1]))[:max_sentences]
        ]
        ordered = [sentence for sentence in unique_sentences if sentence in set(selected)]

        if len(ordered) == 1:
            compacted = ordered[0]
        else:
            compacted = "\n".join(f"- {sentence}" for sentence in ordered)

        if max_tokens is None or self.token_counter.count(compacted) <= max_tokens:
            return compacted

        trimmed = ordered[:]
        while len(trimmed) > 1:
            trimmed.pop()
            candidate = "\n".join(f"- {sentence}" for sentence in trimmed)
            if self.token_counter.count(candidate) <= max_tokens:
                return candidate

        return self.token_counter.truncate(trimmed[0], max_tokens)

    async def _compress_element(
        self,
        element: ContextElement,
        *,
        max_tokens: int,
        anchor_keywords: set[str] | None = None,
    ) -> ContextElement:
        if max_tokens <= 0:
            return self._clone_element(element, content="")

        if self._estimate_tokens(element) <= max_tokens:
            return self._clone_element(element)

        content = await self._compress_text(
            element.content,
            max_tokens=max_tokens,
            anchor_keywords=anchor_keywords,
        )
        return self._clone_element(element, content=content)

    async def _compress_text(
        self,
        content: str,
        *,
        max_tokens: int,
        anchor_keywords: set[str] | None = None,
    ) -> str:
        if self.gemini is not None:
            prompt = (
                "Compress the following context while preserving user intent, constraints, "
                "decisions, identifiers, and critical facts.\n"
                f"Target max tokens: {max_tokens}\n"
                "Return plain text only.\n\n"
                f"{content}"
            )
            try:
                compressed = await asyncio.to_thread(
                    self.gemini.generate,
                    prompt,
                    0.2,
                    max(64, max_tokens * 2),
                )
                normalized = compressed.strip()
                if normalized and self.token_counter.count(normalized) <= max_tokens:
                    return normalized
            except Exception:
                pass

        return self._compact_text_locally(
            content,
            max_sentences=3,
            max_tokens=max_tokens,
            anchor_keywords=anchor_keywords,
        )


class TokenReductionStrategy(OptimizationStrategy):
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        working = [self._clone_element(element) for element in elements if element.content.strip()]
        if not working:
            return []

        anchor_keywords = self._choose_anchor_keywords(working)
        working = self._deduplicate_elements(working, threshold=0.86, merge=True)

        original_tokens = sum(self._estimate_tokens(element) for element in working)
        target_ratio = max(0.0, min(float(params.get("target_reduction_ratio", 0.2)), 0.8))
        token_limit = params.get("token_limit")
        target_tokens = int(original_tokens * (1.0 - target_ratio))
        if isinstance(token_limit, int) and token_limit > 0:
            target_tokens = min(target_tokens, token_limit)
        target_tokens = max(target_tokens, 1)

        scored_elements = list(
            enumerate(
                sorted(
                    working,
                    key=lambda element: self._priority_score(
                        element,
                        index=working.index(element),
                        total_elements=len(working),
                        anchor_keywords=anchor_keywords,
                    ),
                )
            )
        )

        retained = working[:]
        current_tokens = sum(self._estimate_tokens(element) for element in retained)
        for _, candidate in scored_elements:
            if current_tokens <= target_tokens or len(retained) <= 1:
                break
            if candidate.role is ContextElementRole.SYSTEM:
                continue
            if candidate not in retained:
                continue

            candidate_score = self._priority_score(
                candidate,
                index=retained.index(candidate),
                total_elements=len(retained),
                anchor_keywords=anchor_keywords,
            )
            if candidate.role is ContextElementRole.TOOL or candidate_score < 3.2:
                retained.remove(candidate)
                current_tokens -= self._estimate_tokens(candidate)

        optimized: list[ContextElement] = []
        current_tokens = sum(self._estimate_tokens(element) for element in retained)
        for index, element in enumerate(retained):
            if current_tokens <= target_tokens:
                optimized.append(self._clone_element(element))
                continue

            element_tokens = self._estimate_tokens(element)
            surplus = current_tokens - target_tokens
            max_reduction = max(int(element_tokens * 0.45), 0)
            requested_reduction = min(surplus, max_reduction)
            if requested_reduction <= 0 or element.role is ContextElementRole.SYSTEM:
                optimized.append(self._clone_element(element))
                continue

            compressed = await self._compress_element(
                element,
                max_tokens=max(element_tokens - requested_reduction, 12),
                anchor_keywords=anchor_keywords,
            )
            optimized.append(compressed)
            current_tokens -= max(0, element_tokens - self._estimate_tokens(compressed))

        return [element for element in optimized if element.content.strip()]


class ClarityImprovementStrategy(OptimizationStrategy):
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        working = [self._clone_element(element) for element in elements if element.content.strip()]
        if not working:
            return []

        anchor_keywords = self._choose_anchor_keywords(working)
        optimized: list[ContextElement] = []
        for element in working:
            structured = self._compact_text_locally(
                element.content,
                max_sentences=int(params.get("max_sentences", 4)),
                anchor_keywords=anchor_keywords,
            )
            if "\n" not in structured and len(self._split_sentences(element.content)) >= 3:
                sentences = self._split_sentences(structured)
                if len(sentences) > 1:
                    structured = "\n".join(f"- {sentence}" for sentence in sentences)
            optimized.append(self._clone_element(element, content=structured))
        return optimized


class RelevanceEnhancementStrategy(OptimizationStrategy):
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        working = [self._clone_element(element) for element in elements if element.content.strip()]
        if not working:
            return []

        anchor_keywords = self._choose_anchor_keywords(working)
        threshold = max(0.05, min(float(params.get("relevance_threshold", 0.22)), 0.95))

        optimized: list[ContextElement] = []
        for index, element in enumerate(working):
            keywords = self._extract_keywords(element.content)
            overlap = self._jaccard_similarity(keywords, anchor_keywords)
            role_bonus = 0.18 if element.role is ContextElementRole.USER else 0.08
            recency_bonus = (index + 1) / len(working) * 0.05
            score = min(overlap * 0.8 + role_bonus + recency_bonus, 1.0)

            if element.role is not ContextElementRole.SYSTEM and score < threshold:
                continue

            metadata = dict(element.metadata_)
            metadata["relevance_score"] = round(score, 3)
            content = element.content
            if score < 0.5 and self._estimate_tokens(element) > 24:
                content = self._compact_text_locally(
                    content,
                    max_sentences=2,
                    anchor_keywords=anchor_keywords,
                )
            optimized_element = self._clone_element(element, content=content, metadata=metadata)
            optimized_element.metadata_["relevance_score"] = round(score, 3)
            optimized.append(optimized_element)

        return optimized


class RedundancyRemovalStrategy(OptimizationStrategy):
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        working = [self._clone_element(element) for element in elements if element.content.strip()]
        if not working:
            return []

        threshold = max(0.5, min(float(params.get("similarity_threshold", 0.6)), 0.98))
        return self._deduplicate_elements(working, threshold=threshold, merge=True)


class StructureOptimizationStrategy(OptimizationStrategy):
    async def optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any],
    ) -> list[ContextElement]:
        working = [self._clone_element(element) for element in elements if element.content.strip()]
        if not working:
            return []

        anchor_keywords = self._choose_anchor_keywords(working)
        indexed = list(enumerate(working))
        indexed.sort(
            key=lambda item: (
                self._ROLE_ORDER[item[1].role],
                -self._priority_score(
                    item[1],
                    index=item[0],
                    total_elements=len(working),
                    anchor_keywords=anchor_keywords,
                ),
                item[0],
            )
        )
        return [self._clone_element(element) for _, element in indexed]


class ContextOptimizer:
    """Apply context optimization heuristics and select strategies automatically."""

    def __init__(
        self,
        *,
        analyzer: ContextAnalyzer | None = None,
        gemini_service: GeminiService | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.token_counter = token_counter or TokenCounter()
        self.analyzer = analyzer or ContextAnalyzer(token_counter=self.token_counter)
        self.gemini = gemini_service
        self.strategies: dict[OptimizationType, OptimizationStrategy] = {
            OptimizationType.TOKEN_REDUCTION: TokenReductionStrategy(
                token_counter=self.token_counter,
                gemini_service=self.gemini,
            ),
            OptimizationType.CLARITY_IMPROVEMENT: ClarityImprovementStrategy(
                token_counter=self.token_counter,
                gemini_service=self.gemini,
            ),
            OptimizationType.RELEVANCE_ENHANCEMENT: RelevanceEnhancementStrategy(
                token_counter=self.token_counter,
                gemini_service=self.gemini,
            ),
            OptimizationType.REDUNDANCY_REMOVAL: RedundancyRemovalStrategy(
                token_counter=self.token_counter,
                gemini_service=self.gemini,
            ),
            OptimizationType.STRUCTURE_OPTIMIZATION: StructureOptimizationStrategy(
                token_counter=self.token_counter,
                gemini_service=self.gemini,
            ),
        }

    async def optimize(
        self,
        elements: list[ContextElement],
        optimization_type: OptimizationType | str,
        params: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        strategy_type = (
            optimization_type
            if isinstance(optimization_type, OptimizationType)
            else OptimizationType(optimization_type)
        )
        strategy = self.strategies[strategy_type]
        request_params = params or {}
        original_elements = [strategy._clone_element(element) for element in elements if element.content.strip()]
        optimized_elements = await strategy.optimize(original_elements, request_params)

        original_analysis, optimized_analysis = await asyncio.gather(
            self.analyzer.analyze(original_elements),
            self.analyzer.analyze(optimized_elements),
        )
        original_tokens = sum(strategy._estimate_tokens(element) for element in original_elements)
        optimized_tokens = sum(strategy._estimate_tokens(element) for element in optimized_elements)

        return OptimizationResult(
            original_elements=original_elements,
            optimized_elements=optimized_elements,
            strategy_used=strategy_type,
            token_savings=max(0, original_tokens - optimized_tokens),
            quality_improvement=round(
                optimized_analysis.quality_score - original_analysis.quality_score,
                2,
            ),
        )

    async def auto_optimize(
        self,
        elements: list[ContextElement],
        params: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        request_params = params or {}
        strategy_type = await self._select_strategy(elements, request_params)
        return await self.optimize(elements, strategy_type, request_params)

    async def _select_strategy(
        self,
        elements: list[ContextElement],
        params: dict[str, Any] | None = None,
    ) -> OptimizationType:
        request_params = params or {}
        analysis = await self.analyzer.analyze(elements)
        total_tokens = sum(
            element.token_count if element.token_count > 0 else self.token_counter.count(element.content)
            for element in elements
        )
        token_limit = request_params.get("token_limit")

        if isinstance(token_limit, int) and token_limit > 0 and total_tokens > token_limit:
            return OptimizationType.TOKEN_REDUCTION
        if analysis.information_redundancy >= 0.45:
            if isinstance(token_limit, int) and token_limit > 0 and total_tokens > token_limit:
                return OptimizationType.TOKEN_REDUCTION
            return OptimizationType.REDUNDANCY_REMOVAL
        if analysis.topic_consistency < 0.65:
            return OptimizationType.RELEVANCE_ENHANCEMENT
        if analysis.logical_flow < 0.72:
            return OptimizationType.STRUCTURE_OPTIMIZATION
        if analysis.token_efficiency < 0.7:
            return OptimizationType.CLARITY_IMPROVEMENT
        return OptimizationType.CLARITY_IMPROVEMENT


def get_context_optimizer(settings: Settings | None = None) -> ContextOptimizer:
    """Create a context optimizer with optional Gemini and analyzer dependencies."""
    app_settings = settings or get_settings()
    gemini_service = None
    if app_settings.gemini_api_key:
        gemini_service = get_gemini_service(app_settings)
    analyzer = get_context_analyzer(app_settings)
    return ContextOptimizer(
        analyzer=analyzer,
        gemini_service=gemini_service,
    )


__all__ = [
    "ClarityImprovementStrategy",
    "ContextOptimizer",
    "OptimizationResult",
    "OptimizationStrategy",
    "OptimizationType",
    "RedundancyRemovalStrategy",
    "RelevanceEnhancementStrategy",
    "StructureOptimizationStrategy",
    "TokenReductionStrategy",
    "get_context_optimizer",
]
