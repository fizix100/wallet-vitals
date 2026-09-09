from wallet_vitals.ai.narrator import RiskNarrator


def test_negative_stress_values_can_be_explained_as_declines() -> None:
    assert RiskNarrator._is_grounded_output(
        "At block 123, test a 20% collateral decline.",
        {"block_number": 123, "collateral_shock_pct": -20},
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
