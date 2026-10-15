from state.agent_state import AgentState

def test_agent_state_initial_values():
    state = AgentState()

    assert state.last_recommendation is None
    assert state.last_tool_call is None
    assert state.action_history == []
    assert state.error_count == 0
    assert state.last_available_hours is None
    assert state.last_error is None

def test_agent_state_updates():
    state = AgentState()

    state.last_recommendation = "Web Development Assignment"
    state.last_tool_call = "lookup_assessments"
    state.action_history.append("looked up assessments")
    state.action_history.append("recommended Web Development Assignment")

    assert state.last_recommendation == "Web Development Assignment"
    assert state.last_tool_call == "lookup_assessments"
    assert state.action_history == [
        "looked up assessments",
        "recommended Web Development Assignment"
    ]
    assert state.error_count == 0

def test_agent_state_logs_transitions(caplog):
    state = AgentState()

    with caplog.at_level("INFO"):
        state.update_tool_call("lookup_assessments")
        state.update_recommendation("Web Development Assignment")
        state.add_action("Recommended Web Development Assignment")
        state.update_available_hours(5)

    assert "State transition: last_tool_call = lookup_assessments" in caplog.text
    assert "State transition: last_recommendation = Web Development Assignment" in caplog.text
    assert "State transition: action_history updated" in caplog.text
    assert "State transition: last_available_hours = 5" in caplog.text

def test_agent_state_tracks_available_hours():
    state = AgentState()
    state.update_available_hours(5)

    assert state.last_available_hours == 5

def test_agent_state_tracks_errors():
    state = AgentState()
    state.update_error("Test error")

    assert state.last_error == "Test error"