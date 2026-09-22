import reviewer


def test_prompt_supports_needs_verification_classification():
    """
    O contrato do prompt deve permitir NEEDS VERIFICATION,
    além das classificações de severidade confirmadas.
    """

    prompt = reviewer.build_review_prompt(
        rules="Example review rules.",
        diff="Example Pull Request diff.",
    )

    assert (
        "- Classification: HIGH, MEDIUM, LOW or NEEDS VERIFICATION"
        in prompt
    )

    assert "- Severity: HIGH, MEDIUM or LOW" not in prompt