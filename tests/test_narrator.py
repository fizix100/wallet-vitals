from unittest.mock import AsyncMock

import pytest

from wallet_vitals.ai.narrator import RiskNarrator


def test_negative_stress_values_can_be_explained_as_declines() -> None:
    assert RiskNarrator._is_grounded_output(
        "At block 123, test a 20% collateral decline.",
        {"block_number": 123, "collateral_shock_pct": -20},
    )


def test_invented_deployment_is_rejected() -> None:
    assert not RiskNarrator._is_grounded_output(
        "At block 123, deployment QmWrongSource.",
        {"block_number": 123, "deployment": "QmCorrectSource"},
    )


def test_fallback_formats_serialized_delta() -> None:
    answer = RiskNarrator._deterministic_explanation(
        {
            "block_number": 124,
            "risk_delta": {
                "status": "comparable",
                "previous_block_number": 123,
                "collateral_usd_change": "0.00",
                "debt_usd_change": "1.00",
                "health_factor_change": "-0.0010",
            },
        },
        "what_changed",
    )
    assert "-0.0010" in answer


def test_responses_output_text_extraction() -> None:
    payload = {
        "output": [
            {"type": "reasoning", "content": []},
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "Grounded answer."}],
            },
        ]
    }

    assert RiskNarrator._extract_output_text(payload) == "Grounded answer."


def test_grounding_guard_rejects_new_numbers() -> None:
    facts = {
        "block_number": 123,
        "health_factor": "1.2500",
        "total_debt_usd": "1000.00",
    }

    assert RiskNarrator._is_grounded_output("At block 123 the health factor is 1.25.", facts)
    assert not RiskNarrator._is_grounded_output(
        "At block 123 the health factor will reach 9.99.", facts
    )
    assert not RiskNarrator._is_grounded_output("The position is currently healthy.", facts)


@pytest.mark.asyncio
async def test_liquidation_breakpoint_does_not_depend_on_ai_wording() -> None:
    narrator = RiskNarrator("test-key", "unused")
    narrator._generate = AsyncMock(side_effect=AssertionError("Must not ask AI for this boundary"))
    answer, mode = await narrator.explain(
        {
            "block_number": 123,
            "health_factor": "1.1407",
            "stress_ladder": [
                {"collateral_shock_pct": -5, "severity": "danger", "health_factor": "1.0836"},
                {"collateral_shock_pct": -10, "severity": "danger", "health_factor": "1.0266"},
                {
                    "collateral_shock_pct": -20,
                    "severity": "liquidatable",
                    "health_factor": "0.9125",
                },
            ],
        },
        "what_breaks_first",
    )
    assert mode == "deterministic"
    assert "first tested liquidatable scenario is a 20%" in answer
    assert "block 123" in answer
    narrator._generate.assert_not_awaited()


def test_summary_does_not_treat_rounded_dust_debt_as_no_debt() -> None:
    answer = RiskNarrator._deterministic_summary(
        {
            "block_number": 123,
            "health_factor": "0.9500",
            "total_debt_usd": "0.00",
            "severity": "liquidatable",
            "liquidation_buffer_pct": None,
            "evidence_refs": ["reference"],
        }
    )
    assert "No Aave debt" not in answer
    assert "None%" not in answer
    assert "no positive" in answer
