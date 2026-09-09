from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any, Literal

import httpx

NarrativeMode = Literal["openai", "deterministic"]


def _number(value: Decimal | str | None) -> str:
    return "not applicable" if value is None else format(Decimal(value), "f")


class RiskNarrator:
    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._api_key = api_key.strip() if api_key else None
        self._model = model
        self._timeout_seconds = timeout_seconds

    async def report_summary(self, facts: dict[str, Any]) -> tuple[str, NarrativeMode]:
        fallback = self._deterministic_summary(facts)
        return await self._generate(facts, "overview", fallback)

    async def explain(self, facts: dict[str, Any], intent: str) -> tuple[str, NarrativeMode]:
        fallback = self._deterministic_explanation(facts, intent)
        return await self._generate(facts, intent, fallback)

    async def _generate(
        self, facts: dict[str, Any], intent: str, fallback: str
    ) -> tuple[str, NarrativeMode]:
        if not self._api_key:
            return fallback, "deterministic"

        instructions = (
            "You are Wallet Vitals, a cautious Aave risk explainer. Use only the supplied "
            "structured facts. Never calculate or alter a number. Mention the evidence block. "
            "Do not predict prices, give financial advice, or suggest a transaction. Write one "
            "short paragraph in plain English without Markdown formatting. Mention the block "
            "number but do not reproduce deployment hashes or long position identifiers; "
            "refer readers to the Evidence Receipt. Describe the health factor as an indexed "
            "estimate. If a fact is unavailable, say so."
        )
        request_facts = {"intent": intent, "facts": facts}
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "instructions": instructions,
                        "input": json.dumps(request_facts, separators=(",", ":")),
                        "max_output_tokens": 350,
                        "store": False,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return fallback, "deterministic"

        output_text = self._extract_output_text(payload)
        if not output_text or not self._is_grounded_output(output_text, facts):
            return fallback, "deterministic"
        return output_text.strip()[:1800], "openai"

    @staticmethod
    def _extract_output_text(payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        chunks: list[str] = []
        output = payload.get("output")
        if not isinstance(output, list):
            return None
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        return "\n".join(chunks) or None

    @staticmethod
    def _is_grounded_output(output: str, facts: dict[str, Any]) -> bool:
        """Reject model-added numeric claims and narratives that omit the source block."""
        if str(facts["block_number"]) not in output.replace(",", ""):
            return False
        fact_text = json.dumps(facts, separators=(",", ":"))
        for identifier in re.findall(r"\b(?:Qm[A-Za-z0-9]+|0x[a-fA-F0-9]+)\b", output):
            if identifier not in fact_text:
                return False
        pattern = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?")

        def numbers(value: str) -> set[Decimal]:
            parsed: set[Decimal] = set()
            for token in pattern.findall(value):
                try:
                    parsed.add(Decimal(token.replace(",", "")))
                except ValueError:
                    return set()
            return parsed

        allowed = numbers(fact_text)
        allowed.update({abs(value) for value in allowed})
        return numbers(output).issubset(allowed)

    @staticmethod
    def _deterministic_summary(facts: dict[str, Any]) -> str:
        debt = Decimal(str(facts["total_debt_usd"]))
        block = facts["block_number"]
        if debt == 0:
            return (
                f"No Aave debt was found in the indexed position at block {block}. "
                "Stress health factors are therefore not applicable."
            )
        return (
            f"At evidence block {block}, the position has a health factor of "
            f"{facts['health_factor']} and is classified as {facts['severity']}. "
            f"The uniform-collateral liquidation buffer is {facts['liquidation_buffer_pct']}%. "
            f"The result is grounded in {len(facts['evidence_refs'])} position evidence "
            "references. This is a sensitivity calculation, not a price forecast."
        )

    @staticmethod
    def _deterministic_explanation(facts: dict[str, Any], intent: str) -> str:
        block = facts["block_number"]
        if intent == "what_changed":
            delta = facts["risk_delta"]
            if delta["status"] == "no_baseline":
                return (
                    f"Block {block} is the first stored comparable snapshot, so no change can "
                    "be calculated yet. Run the same address again after a later indexed block."
                )
            if delta["status"] != "comparable":
                return "The stored snapshot used different evidence rules or deployment metadata."
            return (
                f"From block {delta['previous_block_number']} to {block}, collateral changed by "
                f"${delta['collateral_usd_change']}, debt by ${delta['debt_usd_change']}, and "
                f"health factor by {_number(delta['health_factor_change'])}."
            )
        if intent == "what_breaks_first":
            ladder = facts["stress_ladder"]
            if facts["health_factor"] is None:
                return (
                    f"No debt was found at block {block}, so the stress ladder is not applicable."
                )
            first = next((item for item in ladder if item["severity"] == "liquidatable"), None)
            if first:
                return (
                    f"In this fixed-assumption ladder, the first tested liquidatable scenario is "
                    f"a {abs(first['collateral_shock_pct'])}% uniform collateral decline."
                )
            return (
                "None of the tested 5%, 10%, or 20% uniform collateral declines makes the "
                f"position liquidatable at evidence block {block}."
            )
        references = facts["evidence_refs"]
        reference_text = references[0] if references else "no active position reference"
        return (
            f"Verify this report against Aave V3 subgraph block {block}, deployment "
            f"{facts['deployment']}, and its receipt. The first evidence reference is "
            f"{reference_text}."
        )
