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
        "DERA command",
        "Expand chat",
        "Sub-agent operations",
        "Evidence canvas",
        "Recovery dossier",
        "Approve local recovery",
        "Ask DERA to revise dossier",
        "Voice Operator Mode",
        "Voice lives inside the DERA command rail",
        "voiceBubble",
        "Mic off",
        "Mute DERA",
        "Stop conversation",
        "Uses browser microphone permission only. No calls are placed.",
        "Raw evidence",
        "Advanced raw streams",
        "chatHint",
        "Type a question, or click one of the suggested prompt chips above.",
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
    assert "cockpit-grid" in css
    assert "@media (max-width: 1200px)" in css
    assert "[hidden]" in css


def test_voice_operator_demo_features_are_labeled_and_bounded():
    html = (FRONTEND / "index.html").read_text()
    js = (FRONTEND / "app.js").read_text()
    assert "Voice lives inside the DERA command rail" in html
    assert "voiceBubble" in html
    assert "Mic off" in html
    assert "Mute DERA" in html
    assert "Stop conversation" in html
    assert "Kokoro-82M" in html
    assert "Simulate caller question" in html
    assert "SpeechRecognition" in js
    assert "speechSynthesis" in js
    assert "startVoiceConversation" in js
    assert "stopVoiceConversation" in js
    assert "toggleMicMute" in js
    assert "toggleVoiceMute" in js
    assert "speakWithKokoro" in js
    assert "primeAudioPlayback" in js
    assert "audio.play().then" in js
    assert "utterance.rate = 1.12" in js
    assert "/api/voice/tts" in js
    assert "voice_mode: state.voiceMode" in js
    assert "handleVoiceDelta" in js
    assert "flushVoiceBuffer" in js
    assert "DERA will answer briefly and Kokoro will speak streamed chunks" in js
    assert "addHermesWritingMessage" in js
    assert "hermes-progress" in js
    assert "streamPhase" in js
    assert "streamHermesMessage" in js
    assert "/ask/stream" in js
    assert "response.body.getReader" in js
    assert "typeHermesMessage" in js
    assert "toggleChatExpanded" in js
    assert "chatQuestionFromInput" in js
    assert "askHermes(chatQuestionFromInput())" in js
    assert "showChatInputHint" in js
    assert "routeDashboardCommand" in js
    assert "technical timeline|why|what|how|explain|summarize|list|compare" in js
    assert "dashboardContextForChat" in js
    assert "dashboard_context" in js
    assert "applyQuestionPlacement" in js
    assert "renderAgentFlowGraph" in js
    assert "return $('chatInput').value.trim()" in js
    assert "if (!cleanQuestion)" in js
    assert "openAgentDrawer" in js
    assert "AGENT_WORK_SCRIPTS" in js
    assert "Visible reasoning summary" in js
    assert "I cannot receive my MFA code. Is my card still working?" in js
    assert "no telephony connected" in js.lower()
    assert "synthetic" not in html.lower()
