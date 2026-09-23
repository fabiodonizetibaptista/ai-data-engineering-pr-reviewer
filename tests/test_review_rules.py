from pathlib import Path


RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "rules"
    / "data-engineering.md"
)


def load_rules() -> str:
    return RULES_PATH.read_text(
        encoding="utf-8",
    )


def test_rules_prohibit_unsupported_absence_claims():
    """
    O reviewer não deve inferir ausência de recursos
    apenas porque eles não aparecem no diff recebido.
    """

    rules = load_rules()

    assert "Absence-of-evidence rule" in rules
    assert "Never infer that something does not exist" in rules
    assert "There are no tests." in rules
    assert "NEEDS VERIFICATION" in rules


def test_rules_handle_partial_diff_safely():
    """
    Um diff truncado não pode ser tratado como representação
    completa do repositório ou do pull request.
    """

    rules = load_rules()

    assert "[DIFF TRUNCATED BY REVIEWER]" in rules
    assert "the review is explicitly partial" in rules
    assert "Do not claim complete repository coverage." in rules
    assert (
        "A smaller number of well-supported findings"
        in rules
    )