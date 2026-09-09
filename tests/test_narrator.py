from wallet_vitals.ai.narrator import RiskNarrator


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
