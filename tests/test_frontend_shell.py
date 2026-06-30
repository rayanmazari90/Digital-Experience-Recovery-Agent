from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_frontend_shell_contains_interactive_incident_command_regions():
    html = (FRONTEND / "index.html").read_text()
    required = [
        "Active incident",
        "Start investigation",
        "primaryCtaReason",
        "stageTracker",
        "activeWorkstream",
        "agentDrawer",
        "Hermes command",
        "Expand chat",
        "Sub-agent operations",
        "Evidence canvas",
        "Recovery dossier",
        "Approve local synthetic recovery",
        "Ask Hermes to revise dossier",
        "Voice Operator Mode",
        "Voice lives inside Hermes chat",
        "voiceBubble",
        "Mute",
        "Stop conversation",
        "Uses browser microphone permission only. No calls are placed.",
        "Raw evidence",
        "Advanced raw streams",
    ]
    for text in required:
        assert text in html


def test_frontend_uses_incident_api_contract_and_state_machine():
    js = (FRONTEND / "app.js").read_text()
    for state in [
        "disconnected",
        "ready_with_incident",
        "investigating.customer_signal",
        "investigating.observability",
        "investigating.change_correlation",
        "investigating.recovery_planning",
        "dossier_ready",
        "revising_dossier",
        "approval_required",
        "approved_local",
        "rejected_local",
        "error",
    ]:
        assert state in js
    for endpoint in [
        "/api/incidents",
        "/investigate",
        "/ask",
        "/dossier/revise",
        "/approval",
    ]:
        assert endpoint in js


def test_accessibility_and_operational_language_contracts():
    html = (FRONTEND / "index.html").read_text()
    css = (FRONTEND / "styles.css").read_text()
    assert "aria-live" in html
    assert "aria-label" in html
    assert "landing" not in html.lower()
    assert "slide" not in html.lower()
    assert "console-grid" in css
    assert "@media(max-width:1100px)" in css
    assert "[hidden]" in css


def test_voice_operator_demo_features_are_labeled_and_bounded():
    html = (FRONTEND / "index.html").read_text()
    js = (FRONTEND / "app.js").read_text()
    assert "Voice lives inside Hermes chat" in html
    assert "voiceBubble" in html
    assert "Stop conversation" in html
    assert "Kokoro-82M" in html
    assert "Simulate caller question" in html
    assert "SpeechRecognition" in js
    assert "speechSynthesis" in js
    assert "startVoiceConversation" in js
    assert "stopVoiceConversation" in js
    assert "toggleVoiceMute" in js
    assert "handleVoiceDelta" in js
    assert "flushVoiceBuffer" in js
    assert "Hermes will speak while writing streamed answers" in js
    assert "addHermesWritingMessage" in js
    assert "hermes-progress" in js
    assert "streamPhase" in js
    assert "streamHermesMessage" in js
    assert "/ask/stream" in js
    assert "response.body.getReader" in js
    assert "typeHermesMessage" in js
    assert "toggleChatExpanded" in js
    assert "openAgentDrawer" in js
    assert "AGENT_WORK_SCRIPTS" in js
    assert "Visible reasoning summary" in js
    assert "I cannot receive my MFA code. Is my card still working?" in js
    assert "no telephony connected" in js.lower()
