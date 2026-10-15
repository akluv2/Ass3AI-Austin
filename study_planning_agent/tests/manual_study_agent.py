from agents.study_agent import run_study_agent

def test_study_agent():
    response = run_study_agent(2)
    print(response)

def test_study_agent_state_updates_across_runs():
    from agents import study_agent

    study_agent.run_study_agent(5)
    first_recommendation = study_agent.agent_state.last_recommendation

    study_agent.run_study_agent(2)
    second_recommendation = study_agent.agent_state.last_recommendation

    assert first_recommendation is not None
    assert second_recommendation is not None
    assert len(study_agent.agent_state.action_history) >= 2
    assert study_agent.agent_state.last_tool_call == "lookup_assessments"