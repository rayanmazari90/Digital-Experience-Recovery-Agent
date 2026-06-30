from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.orchestration_guidance import (
    PARENT_ORCHESTRATION_GUIDANCE,
    ROLE_GUIDANCE,
    SUPERVISOR_PROMPT,
    build_child_prompt,
    build_delegate_task_spec,
    list_role_names,
)


EXPECTED_ROLES = {
    "fault_diagnostician",
    "journey_analyst",
    "recovery_strategist",
    "evidence_synthesizer",
}

FORBIDDEN_CHILD_TOOLSETS = {
    "memory",
    "messaging",
    "cronjob",
    "browser",
    "web",
    "terminal",
    "delegation",
    "session_search",
    "send_message",
}


def test_role_guidance_defines_required_contracts():
    assert set(list_role_names()) == EXPECTED_ROLES
    for role, guidance in ROLE_GUIDANCE.items():
        assert guidance["context_receives"]
        assert guidance["delegate_when"]
        assert guidance["approval_triggers"]
        assert guidance["allowed_toolsets"] == ["file"]
        assert not (set(guidance["allowed_toolsets"]) & FORBIDDEN_CHILD_TOOLSETS)
        assert guidance["output_schema"]["role"] == role
        assert "replay" in str(guidance["output_schema"]).lower()
        assert "Do not write memory" in guidance["prompt"]
        assert "Do not delegate" in guidance["prompt"]


def test_delegate_task_specs_are_bounded_leaf_specs():
    incident_context = {"run_id": "run_test", "evidence_ids": ["evd_test"], "synthetic": True}
    for role in EXPECTED_ROLES:
        spec = build_delegate_task_spec(role, incident_context)
        assert spec["role"] == "leaf"
        assert spec["toolsets"] == ["file"]
        assert spec["context"]["role"] == role
        assert spec["context"]["synthetic_only"] is True
        assert spec["context"]["incident_context"] == incident_context
        assert spec["context"]["output_schema"]["role"] == role


def test_prompts_encode_delegate_task_and_approval_constraints():
    assert "delegate_task" in SUPERVISOR_PROMPT
    assert "role='leaf'" in SUPERVISOR_PROMPT
    assert "memory" in SUPERVISOR_PROMPT
    assert "Operator approval policy" in SUPERVISOR_PROMPT
    assert "Final synthesis policy" in SUPERVISOR_PROMPT

    parent_text = str(PARENT_ORCHESTRATION_GUIDANCE)
    assert "nested" in parent_text.lower()
    assert "final" in parent_text.lower()
    assert "approval" in parent_text.lower()

    child_prompt = build_child_prompt("fault_diagnostician")
    assert "Shared constraints" in child_prompt
    assert "Expected output schema" in child_prompt
    assert "Do not write memory" in child_prompt
    assert "role='leaf'" in child_prompt


def test_orchestration_guidance_api_contract(tmp_path):
    settings = Settings(
        database_path=tmp_path / "test.sqlite3",
        storage_root=tmp_path / "storage",
        hermes_enabled=False,
        hermes_api_key="test-key",
    )
    client = TestClient(create_app(settings))
    response = client.get("/orchestration/guidance")
    assert response.status_code == 200
    body = response.json()
    assert set(body["roles"]) == EXPECTED_ROLES
    assert "supervisor_prompt" in body
    assert "parent_guidance" in body
    assert body["roles"]["recovery_strategist"]["output_schema"]["operator_approval_request"]["required"] == "boolean"
