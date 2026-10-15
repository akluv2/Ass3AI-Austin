from tools.assessment_tools import lookup_assessments

def test_lookup_assessments_returns_stored_data():
    result = lookup_assessments.invoke({})

    assert "AI Application" in result
    assert "Database Project" in result
    assert "Web Development Assignment" in result

def test_lookup_assessments_handles_service_failure(monkeypatch):
    from tools import assessment_tools

    def fake_get_assessments():
        raise Exception("Assessment service unavailable")

    monkeypatch.setattr(
        assessment_tools,
        "get_assessments",
        fake_get_assessments
    )

    try:
        assessment_tools.lookup_assessments.invoke({})
        assert False, "Expected the tool to raise an exception"
    except Exception as error:
        assert str(error) == "Assessment service unavailable"