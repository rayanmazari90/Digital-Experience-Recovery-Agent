const apiBase = 'http://127.0.0.1:8080';
const state = {
  connected: false,
  hermesConnected: false,
  incident: null,
  investigating: false,
  selectedEvidence: null,
  recognition: null,
  activeTab: 'timeline',
  chatExpanded: false,
  streamPhase: 'idle',
  activeAgentId: null,
  activeAgentStage: null,
  agentWorkLog: [],
  agentWorkTimer: null,
  voiceMode: false,
  voiceMuted: false,
  micMuted: false,
  voiceSpeaking: false,
  voiceStreamBuffer: '',
  voiceAudioQueue: Promise.resolve(),
  audioContext: null,
  audioUnlocked: false,
  kokoroAvailable: null,
};

const $ = (id) => document.getElementById(id);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const STAGES = [
  { key: 'customer_signal', label: 'Customer signal', states: ['ready_with_incident', 'investigating.customer_signal'], tab: 'evidence' },
  { key: 'telemetry', label: 'Telemetry', states: ['investigating.observability'], tab: 'evidence' },
  { key: 'change', label: 'Change correlation', states: ['investigating.change_correlation'], tab: 'evidence' },
  { key: 'recovery', label: 'Recovery plan', states: ['investigating.recovery_planning'], tab: 'dossier' },
  { key: 'approval', label: 'Approval', states: ['approval_required', 'approved_local', 'rejected_local'], tab: 'dossier' },
  { key: 'dossier', label: 'Dossier', states: ['dossier_ready', 'approval_required', 'approved_local', 'rejected_local'], tab: 'dossier' },
];

const STATE_ORDER = [
  'ready_with_incident',
  'investigating.customer_signal',
  'investigating.observability',
  'investigating.change_correlation',
  'investigating.recovery_planning',
  'dossier_ready',
  'approval_required',
  'approved_local',
  'rejected_local',
];

const PRODUCT_STATES = {
  disconnected: {
    label: 'Disconnected',
    focus: ['Connection required', 'Start the backend and DERA runtime before investigating.'],
    cta: { label: 'Backend required', action: 'none', enabled: false, reason: 'Waiting for backend connection.' },
    prompts: ['What is the connection status?'],
  },
  ready_with_incident: {
    label: 'Ready for investigation',
    focus: ['Start with DERA', 'Start the investigation, then inspect the evidence and specialist workstream as the case develops.'],
    cta: { label: 'Start investigation', action: 'advance', enabled: true, reason: null },
    prompts: ['What is happening?', 'What evidence will DERA inspect?', 'What remains operational?'],
  },
  'investigating.customer_signal': {
    label: 'Customer signal active',
    focus: ['Verify customer pain', 'Customer complaints are clustered. Continue to telemetry to prove whether the technical path matches symptoms.'],
    cta: { label: 'Continue to telemetry', action: 'advance', enabled: true, reason: null },
    prompts: ['What evidence supports this?', 'What is uncertain?', 'What should I watch next?'],
  },
  'investigating.observability': {
    label: 'Telemetry active',
    focus: ['Compare with telemetry', 'Auth latency and 504s are visible. Correlate the incident window with recent changes.'],
    cta: { label: 'Correlate CHG-1048', action: 'advance', enabled: true, reason: null },
    prompts: ['Show me the technical timeline.', 'What evidence supports this?', 'What remains operational for customers?'],
  },
  'investigating.change_correlation': {
    label: 'Change correlation active',
    focus: ['Challenge CHG-1048', 'A nearby change is suspected. Continue only if the recovery plan stays local and approval-gated.'],
    cta: { label: 'Draft recovery plan', action: 'advance', enabled: true, reason: null },
    prompts: ['Why do you suspect CHG-1048?', 'What risks remain?', 'What should I approve?'],
  },
  'investigating.recovery_planning': {
    label: 'Recovery planning active',
    focus: ['Review recovery wording', 'DERA has enough evidence to build a local safe-mode dossier and approval gate.'],
    cta: { label: 'Build dossier', action: 'advance', enabled: true, reason: null },
    prompts: ['Draft a customer-safe message.', 'What validation checks matter?', 'What should I approve?'],
  },
  dossier_ready: {
    label: 'Dossier ready',
    focus: ['Open the human gate', 'The recovery dossier is ready. Continue to the supervised approval gate.'],
    cta: { label: 'Open approval gate', action: 'advance', enabled: true, reason: null },
    prompts: ['Summarize the dossier.', 'List unresolved risks.', 'What should I approve?'],
  },
  revising_dossier: {
    label: 'Revising dossier',
    focus: ['DERA is revising', 'A live DERA dossier revision is in progress. Keep review local and approval-gated.'],
    cta: { label: 'Revision in progress', action: 'none', enabled: false, reason: 'Waiting for DERA to revise the dossier.' },
    prompts: ['What changed in the revision?', 'List unresolved risks.'],
  },
  approval_required: {
    label: 'Approval required',
    focus: ['Human gate', 'Approve or reject the local recovery decision only after reviewing the dossier.'],
    cta: { label: 'Review local approval gate', action: 'show_dossier', enabled: true, reason: null },
    prompts: ['What should I approve?', 'Revise the customer message.', 'Why is this safe-mode only?'],
  },
  approved_local: {
    label: 'Approved locally',
    focus: ['Local decision recorded', 'Local approval was recorded. No real customer, rollback, or banking system action occurred.'],
    cta: { label: 'Approved locally', action: 'none', enabled: false, reason: 'Local approval already recorded.' },
    prompts: ['Summarize the final decision.', 'What should be monitored next?'],
  },
  rejected_local: {
    label: 'Rejected locally',
    focus: ['Recommendation rejected', 'Local rejection was recorded. No real customer, rollback, or banking system action occurred.'],
    cta: { label: 'Rejected locally', action: 'none', enabled: false, reason: 'Local rejection already recorded.' },
    prompts: ['Explain the rejection record.', 'What alternative should we consider?'],
  },
  error: {
    label: 'Error',
    focus: ['Needs attention', 'A local product error occurred. Check the raw stream and retry when ready.'],
    cta: { label: 'Retry investigation', action: 'advance', enabled: true, reason: null },
    prompts: ['What failed?', 'Can I retry safely?'],
  },
};

const EVIDENCE_EXPLAINERS = {
  ev_customer_complaints: {
    supports: ['Customer-facing Login / Authentication impact', 'MFA code non-arrival symptom cluster', 'SEV-2 impact plausibility'],
    limitations: ['Does not prove the backend failure mode alone', 'Samples are masked practice evidence'],
  },
  ev_telemetry_latency: {
    supports: ['Auth gateway latency spike', '504 timeout behavior matching login failures'],
    limitations: ['Needs change-window comparison before root-cause confidence is high'],
  },
  ev_change_chg1048: {
    supports: ['CHG-1048 occurred five minutes before incident start', 'IAM Gateway is on the affected journey path'],
    limitations: ['Temporal correlation is not proof without recovery validation'],
  },
  ev_recovery_plan: {
    supports: ['Rollback target and validation checks exist', 'Customer-safe communication can be drafted'],
    limitations: ['Requires explicit local approval; does not execute real rollback or customer send'],
  },
};

const AGENT_BY_TARGET_STATE = {
  'investigating.customer_signal': 'customer_signal',
  'investigating.observability': 'observability',
  'investigating.change_correlation': 'change_correlation',
  'investigating.recovery_planning': 'recovery',
  dossier_ready: 'supervisor',
  approval_required: 'supervisor',
};

const AGENT_WORK_SCRIPTS = {
  customer_signal: [
    'Loading masked complaint samples',
    'Clustering MFA-delay language',
    'Separating customer impact from root-cause inference',
    'Linking complaint evidence to Login / Authentication journey',
  ],
  observability: [
    'Reading auth gateway latency',
    'Checking 504 error-rate movement',
    'Comparing login completion and MFA validation symptoms',
    'Preparing telemetry confidence summary',
  ],
  change_correlation: [
    'Opening CHG-1048 change record',
    'Comparing deployment time against incident window',
    'Checking affected IAM Gateway surface',
    'Separating correlation from proof',
  ],
  recovery: [
    'Reviewing rollback candidate stable-v4.12.2',
    'Drafting validation checks',
    'Preparing customer-safe communication wording',
    'Flagging local approval requirements',
  ],
  supervisor: [
    'Reconciling specialist findings',
    'Checking evidence IDs and uncertainty',
    'Preparing supervised approval gate',
    'Building replayable dossier summary',
  ],
};

const AGENT_REASONING_SUMMARIES = {
  customer_signal: 'Visible reasoning summary: compare masked complaint phrases against the affected journey, quantify impact, and avoid claiming a technical cause from customer text alone.',
  observability: 'Visible reasoning summary: check whether telemetry explains the login symptoms before accepting the customer-signal hypothesis as technical.',
  change_correlation: 'Visible reasoning summary: compare CHG-1048 timing and service scope with the incident window while preserving uncertainty about correlation versus proof.',
  recovery: 'Visible reasoning summary: produce a non-executing recovery option, validation checklist, and customer-safe wording that remains behind local approval.',
  supervisor: 'Visible reasoning summary: reconcile specialist outputs, evidence IDs, confidence, and approval policy into a replayable operator decision.',
};

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`);
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
}

function currentState() { return state.incident?.state || 'disconnected'; }
function currentConfig() { return PRODUCT_STATES[currentState()] || PRODUCT_STATES.error; }
function orderIndex(productState) { return Math.max(0, STATE_ORDER.indexOf(productState)); }

function setRuntimeStatus(health) {
  state.connected = true;
  state.hermesConnected = Boolean(health.hermes_enabled);
  $('backendStatus').textContent = 'Backend connected';
  $('backendStatus').className = 'pill good';
  $('hermesStatus').textContent = state.hermesConnected ? 'DERA connected' : 'DERA adapter ready';
  $('hermesStatus').className = state.hermesConnected ? 'pill good' : 'pill warn';
}

function adapterLabel(adapterMode) {
  if (adapterMode === 'hermes-api') return 'Live DERA';
  if (adapterMode) return 'DERA unavailable';
  return '';
}

function formatHermesContent(content) {
  const text = String(content || '').trim();
  if (!text) return '';
  const escaped = escapeHtml(text);
  const sections = escaped.split(/\n\s*\n/).filter(Boolean);
  if (sections.length <= 1) return `<p>${escaped}</p>`;
  return sections.map((section) => {
    const lines = section.split('\n').filter(Boolean);
    const first = lines[0].replace(/[:：]$/, '');
    const looksLikeHeading = lines.length > 1 && first.length < 70 && !first.includes('|');
    if (looksLikeHeading) {
      return `<section class="answer-section"><h3>${first}</h3><p>${lines.slice(1).join('<br>')}</p></section>`;
    }
    return `<p>${lines.join('<br>')}</p>`;
  }).join('');
}

function addChat(role, content, adapterMode = '') {
  const item = document.createElement('div');
  item.className = `chat-message ${role}`;
  const liveLabel = role === 'hermes' && adapterMode ? `<em>${adapterLabel(adapterMode)}</em>` : '';
  item.innerHTML = `<strong>${role === 'operator' ? 'You' : 'DERA'} ${liveLabel}</strong><div class="message-body">${role === 'hermes' ? formatHermesContent(content) : `<p>${escapeHtml(content)}</p>`}</div>`;
  $('chatLog').appendChild(item);
  $('chatLog').scrollTop = $('chatLog').scrollHeight;
  return item;
}

function addHermesWritingMessage(phase = 'Opening incident context...') {
  state.streamPhase = 'stream_opening';
  const item = document.createElement('div');
  item.className = 'chat-message hermes typing';
  item.dataset.firstDelta = 'false';
  item.innerHTML = `<strong>DERA <em>Live DERA</em></strong><div class="message-body"><div class="hermes-progress"><span class="pulse-dot"></span><span data-progress-text>${escapeHtml(phase)}</span></div></div>`;
  $('chatLog').appendChild(item);
  $('chatLog').scrollTop = $('chatLog').scrollHeight;
  return item;
}

function updateHermesProgress(item, message) {
  const target = item.querySelector('[data-progress-text]');
  if (target) target.textContent = message;
}

function ensureStreamTarget(item, adapterMode = 'hermes-api') {
  if (item.dataset.firstDelta !== 'true') {
    item.dataset.firstDelta = 'true';
    item.className = 'chat-message hermes';
    item.innerHTML = `<strong>DERA <em>${adapterLabel(adapterMode)}</em></strong><div class="message-body"><p></p></div>`;
  }
  return item.querySelector('.message-body p');
}

async function typeHermesMessage(item, content, adapterMode = '') {
  item.className = 'chat-message hermes';
  item.dataset.firstDelta = 'true';
  item.innerHTML = `<strong>DERA <em>${adapterLabel(adapterMode)}</em></strong><div class="message-body"><p></p></div>`;
  const target = item.querySelector('p');
  const text = String(content || '');
  const chunkSize = text.length > 900 ? 18 : 9;
  for (let index = 0; index < text.length; index += chunkSize) {
    target.textContent = text.slice(0, index + chunkSize);
    if (state.voiceMode) handleVoiceDelta(text.slice(index, index + chunkSize));
    $('chatLog').scrollTop = $('chatLog').scrollHeight;
    await wait(14);
  }
  flushVoiceBuffer();
  item.querySelector('.message-body').innerHTML = formatHermesContent(text);
}

function setVoiceBubble(title, detail, tone = 'idle') {
  const bubble = $('voiceBubble');
  if (!bubble) return;
  bubble.hidden = !state.voiceMode;
  bubble.dataset.voiceState = tone;
  $('voiceBubbleTitle').textContent = title;
  $('voiceBubbleText').textContent = detail;
  $('voiceStatus').textContent = detail;
}

function updateVoiceControls() {
  $('voiceModeBtn').hidden = state.voiceMode;
  $('micVoiceBtn').hidden = !state.voiceMode;
  $('muteVoiceBtn').hidden = !state.voiceMode;
  $('stopVoiceBtn').hidden = !state.voiceMode;
  $('micVoiceBtn').textContent = state.micMuted ? 'Mic on' : 'Mic off';
  $('muteVoiceBtn').textContent = state.voiceMuted ? 'Unmute DERA' : 'Mute DERA';
  $('chatInput').placeholder = state.voiceMode ? 'Voice mode active — short answers, type anytime as fallback' : 'What is happening?';
  if (!state.voiceMode) $('voiceBubble').hidden = true;
}

async function primeAudioPlayback() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      state.audioContext = state.audioContext || new AudioContextClass();
      if (state.audioContext.state === 'suspended') await state.audioContext.resume();
      const source = state.audioContext.createBufferSource();
      source.buffer = state.audioContext.createBuffer(1, 1, 22050);
      source.connect(state.audioContext.destination);
      source.start(0);
    }
    state.audioUnlocked = true;
    return true;
  } catch (error) {
    state.audioUnlocked = false;
    setVoiceBubble('Tap to enable sound', 'Safari blocked audio playback. Press Talk again, then ask DERA.', 'muted');
    return false;
  }
}

function playAudioBlob(blob) {
  return new Promise((resolve, reject) => {
    const audio = new Audio(URL.createObjectURL(blob));
    const cleanup = () => URL.revokeObjectURL(audio.src);
    audio.onended = () => { cleanup(); resolve(); };
    audio.onerror = () => { cleanup(); reject(new Error('audio_playback_failed')); };
    audio.play().then(() => {
      state.audioUnlocked = true;
    }).catch((error) => { cleanup(); reject(error); });
  });
}

function fallbackBrowserSpeech(chunk, { interrupt = false } = {}) {
  if (!('speechSynthesis' in window)) return;
  if (interrupt) window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(chunk);
  utterance.rate = 1.12;
  utterance.pitch = 1.02;
  utterance.onstart = () => { state.voiceSpeaking = true; setVoiceBubble('DERA is talking', chunk, 'speaking'); };
  utterance.onend = () => { state.voiceSpeaking = false; if (state.voiceMode) setVoiceBubble('Voice mode listening', 'Ask another question, mute DERA, or stop conversation to return to text.', 'listening'); };
  window.speechSynthesis.speak(utterance);
}

async function speakWithKokoro(chunk) {
  const response = await fetch(`${apiBase}/api/voice/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: chunk }),
  });
  if (!response.ok) throw new Error(await response.text());
  state.kokoroAvailable = true;
  await playAudioBlob(await response.blob());
}

function speakLiveChunk(text, { interrupt = false } = {}) {
  const chunk = String(text || '').trim();
  if (!chunk || !state.voiceMode || state.voiceMuted) return;
  if (interrupt) {
    state.voiceAudioQueue = Promise.resolve();
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }
  setVoiceBubble('DERA is talking', chunk, 'speaking');
  state.voiceAudioQueue = state.voiceAudioQueue
    .then(() => speakWithKokoro(chunk))
    .catch(() => {
      state.kokoroAvailable = false;
      fallbackBrowserSpeech(chunk, { interrupt });
    });
}

function handleVoiceDelta(delta) {
  if (!state.voiceMode || state.voiceMuted) return;
  state.voiceStreamBuffer += delta;
  setVoiceBubble('DERA is writing and talking', 'Streaming response live. Speech starts on sentence chunks, not after the full answer.', 'speaking');
  const match = state.voiceStreamBuffer.match(/^([\s\S]*?[.!?])\s+/);
  if (!match) return;
  const sentence = match[1];
  state.voiceStreamBuffer = state.voiceStreamBuffer.slice(match[0].length);
  speakLiveChunk(sentence);
}

function flushVoiceBuffer() {
  if (!state.voiceMode || state.voiceMuted) { state.voiceStreamBuffer = ''; return; }
  const remaining = state.voiceStreamBuffer.trim();
  state.voiceStreamBuffer = '';
  if (remaining) speakLiveChunk(remaining);
}

async function startVoiceConversation() {
  state.voiceMode = true;
  state.voiceMuted = false;
  state.micMuted = false;
  state.voiceStreamBuffer = '';
  updateVoiceControls();
  await primeAudioPlayback();
  if (!state.recognition) {
    setVoiceBubble('Voice input unavailable', 'This browser has no SpeechRecognition. Type in the chat; DERA will answer shortly and Kokoro will speak when available.', 'muted');
    speakLiveChunk('Voice output is ready. Type a question and I’ll answer out loud.', { interrupt: true });
    return;
  }
  setVoiceBubble('Voice mode listening', 'Microphone input stays local to the browser. DERA will answer briefly and Kokoro will speak streamed chunks.', 'listening');
  speakLiveChunk('I’m listening. Ask me what to show or what to investigate.', { interrupt: true });
  try {
    state.recognition.start();
  } catch (_) {
    setVoiceBubble('Voice output ready', 'Speech recognition is already active or Safari blocked microphone start. Type a question and DERA will still speak.', 'listening');
  }
}

function stopVoiceConversation() {
  state.voiceMode = false;
  state.voiceStreamBuffer = '';
  state.voiceAudioQueue = Promise.resolve();
  try { state.recognition?.stop(); } catch (_) { /* ignore inactive recognizer */ }
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  updateVoiceControls();
  $('voiceStatus').textContent = 'Voice conversation stopped. Text input is active.';
  $('chatInput').focus();
}

function toggleMicMute() {
  state.micMuted = !state.micMuted;
  if (state.micMuted) {
    try { state.recognition?.stop(); } catch (_) { /* ignore inactive recognizer */ }
    setVoiceBubble('Microphone off', 'Mic is muted. Type instead, or turn Mic on to speak again.', 'muted');
  } else {
    setVoiceBubble('Listening', 'Microphone is on. Ask a short question.', 'listening');
    state.recognition?.start();
  }
  updateVoiceControls();
}

function toggleVoiceMute() {
  state.voiceMuted = !state.voiceMuted;
  if (state.voiceMuted && 'speechSynthesis' in window) window.speechSynthesis.cancel();
  updateVoiceControls();
  setVoiceBubble(state.voiceMuted ? 'DERA voice muted' : 'DERA voice unmuted', state.voiceMuted ? 'DERA will keep writing, but audio output is muted.' : 'DERA will speak upcoming streamed sentence chunks through Kokoro when available.', state.voiceMuted ? 'muted' : 'listening');
}

function dashboardContextForChat() {
  const config = currentConfig();
  const visibleEvidence = getVisibleEvidence().map((ev) => ({ id: ev.id, lane: ev.lane, title: ev.title, summary: ev.summary }));
  const selectedEvidence = state.selectedEvidence ? visibleEvidence.find((ev) => ev.id === state.selectedEvidence) || null : null;
  const activeAgent = state.activeAgentId ? agentById(state.activeAgentId) : (state.incident?.subagents || []).find((agent) => agent.status === 'running') || null;
  const activeTabLabels = { timeline: 'Chronology', evidence: 'Evidence', agents: 'Agents', dossier: 'Dossier', voice: 'Voice' };
  return {
    active_tab: state.activeTab,
    active_tab_label: activeTabLabels[state.activeTab] || state.activeTab,
    product_state: currentState(),
    product_state_label: config.label,
    operator_focus: config.focus,
    primary_cta: config.cta?.label || '',
    selected_evidence: selectedEvidence,
    active_agent: activeAgent ? { id: activeAgent.id, name: activeAgent.name, status: activeAgent.status, finding: activeAgent.finding, confidence: activeAgent.confidence } : null,
    dossier_ready_items: getDossierReadiness(),
    visible_evidence: visibleEvidence,
    chat_expanded: state.chatExpanded,
  };
}

async function streamHermesMessage(item, question) {
  updateHermesProgress(item, 'Opening live DERA stream...');
  const response = await fetch(`${apiBase}/api/incidents/${state.incident.id}/ask/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, voice_mode: state.voiceMode, dashboard_context: dashboardContextForChat() }),
  });
  if (!response.ok || !response.body) throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let adapterMode = 'hermes-api';
  let answer = '';
  const handleBlock = (block) => {
    const lines = block.split('\n');
    const event = (lines.find((line) => line.startsWith('event:')) || 'event: message').slice(6).trim();
    const dataLine = lines.find((line) => line.startsWith('data:'));
    if (!dataLine) return;
    const data = JSON.parse(dataLine.slice(5).trim());
    if (data.adapter_mode) {
      adapterMode = data.adapter_mode;
      const label = item.querySelector('em');
      if (label) label.textContent = adapterLabel(adapterMode);
    }
    if (event === 'status') {
      updateHermesProgress(item, data.message || 'Reading incident context...');
      return;
    }
    if (event === 'delta' && data.delta) {
      state.streamPhase = 'first_delta_received';
      const target = ensureStreamTarget(item, adapterMode);
      answer += data.delta;
      target.textContent = answer;
      handleVoiceDelta(data.delta);
      $('chatLog').scrollTop = $('chatLog').scrollHeight;
    }
    if (event === 'done') {
      state.streamPhase = 'stream_done';
      flushVoiceBuffer();
      if (!answer.trim()) updateHermesProgress(item, 'DERA returned no text. Try again.');
    }
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split('\n\n');
    buffer = blocks.pop() || '';
    blocks.forEach(handleBlock);
  }
  if (buffer.trim()) handleBlock(buffer);
  if (answer.trim()) item.querySelector('.message-body').innerHTML = formatHermesContent(answer);
  return adapterMode;
}

function toggleChatExpanded() {
  state.chatExpanded = !state.chatExpanded;
  document.body.classList.toggle('chat-expanded', state.chatExpanded);
  $('expandChatBtn').textContent = state.chatExpanded ? 'Collapse chat' : 'Expand chat';
  $('expandChatBtn').setAttribute('aria-pressed', String(state.chatExpanded));
}

function getVisibleEvidence() {
  if (!state.incident) return [];
  const idx = orderIndex(currentState());
  return (state.incident.evidence || []).filter((ev) => orderIndex(ev.visible_after) <= idx);
}

function getDossierReadiness() {
  const s = currentState();
  const idx = orderIndex(s);
  const doneAt = (requiredState) => orderIndex(requiredState) <= idx;
  return [
    { key: 'customer', label: 'Customer signal', tab: 'evidence', status: doneAt('investigating.customer_signal') ? 'complete' : 'pending', evidence: 'ev_customer_complaints' },
    { key: 'telemetry', label: 'Telemetry', tab: 'evidence', status: doneAt('investigating.observability') ? 'complete' : 'pending', evidence: 'ev_telemetry_latency' },
    { key: 'change', label: 'Change correlation', tab: 'evidence', status: doneAt('investigating.change_correlation') ? 'complete' : 'pending', evidence: 'ev_change_chg1048' },
    { key: 'recovery', label: 'Recovery plan', tab: 'dossier', status: doneAt('investigating.recovery_planning') ? 'complete' : 'pending', evidence: 'ev_recovery_plan' },
    { key: 'approval', label: 'Operator approval', tab: 'dossier', status: s === 'approved_local' || s === 'rejected_local' ? 'complete' : s === 'approval_required' ? 'pending' : 'not_required', evidence: null },
  ];
}

function nextIncidentState() {
  const current = currentState();
  if (current === 'ready_with_incident') return 'investigating.customer_signal';
  const idx = STATE_ORDER.indexOf(current);
  if (idx < 0 || idx >= STATE_ORDER.length - 1) return current;
  return STATE_ORDER[idx + 1];
}

function agentById(id) {
  return (state.incident?.subagents || []).find((agent) => agent.id === id);
}

function optimisticAgentFor(targetState) {
  const agentId = AGENT_BY_TARGET_STATE[targetState] || 'supervisor';
  const agent = agentById(agentId);
  if (!agent) return null;
  state.activeAgentId = agentId;
  state.activeAgentStage = targetState;
  state.agentWorkLog = [`Queued ${agent.name}`, 'Opening incident packet'];
  agent.status = 'running';
  agent.finding = 'DERA specialist is working through the supplied incident context.';
  agent.tool = 'live DERA specialist reasoning';
  agent.timestamp = new Date().toTimeString().slice(0, 5);
  return agent;
}

function startAgentWorkAnimation(agentId) {
  stopAgentWorkAnimation(false);
  const script = AGENT_WORK_SCRIPTS[agentId] || AGENT_WORK_SCRIPTS.supervisor;
  let index = 0;
  state.agentWorkTimer = window.setInterval(() => {
    if (index < script.length) {
      state.agentWorkLog.push(script[index]);
      index += 1;
      renderActiveWorkstream();
      renderAgents();
      if (!$('agentDrawer').hidden && state.activeAgentId === agentId) openAgentDrawer(agentId);
    } else {
      stopAgentWorkAnimation(false);
    }
  }, 650);
}

function stopAgentWorkAnimation(clear = true) {
  if (state.agentWorkTimer) window.clearInterval(state.agentWorkTimer);
  state.agentWorkTimer = null;
  if (clear) {
    state.activeAgentId = null;
    state.activeAgentStage = null;
    state.agentWorkLog = [];
  }
}

function renderActiveWorkstream() {
  const panel = $('activeWorkstream');
  if (!state.investigating || !state.activeAgentId) {
    panel.hidden = true;
    panel.innerHTML = '';
    return;
  }
  const agent = agentById(state.activeAgentId);
  if (!agent) return;
  const latest = state.agentWorkLog[state.agentWorkLog.length - 1] || 'Starting specialist work';
  panel.hidden = false;
  panel.innerHTML = `
    <div class="workstream-pulse"><span class="pulse-dot"></span><strong>${escapeHtml(agent.name)}</strong><em>running</em></div>
    <p>${escapeHtml(latest)}</p>
    <button class="btn secondary compact" type="button" data-open-agent="${escapeHtml(agent.id)}">Open live agent work</button>`;
  panel.querySelector('[data-open-agent]')?.addEventListener('click', () => openAgentDrawer(agent.id));
}

function renderIncident() {
  const incident = state.incident;
  if (!incident) return;
  const config = currentConfig();
  document.body.dataset.productState = incident.state;
  $('incidentState').textContent = state.investigating && state.activeAgentId ? `${agentById(state.activeAgentId)?.name || 'DERA agent'} running` : config.label;
  $('incidentTitle').textContent = incident.title;
  $('severityStatus').textContent = incident.severity;
  $('metricSpike').textContent = incident.impact.complaint_spike;
  $('metricJourney').textContent = incident.impact.affected_journey;
  $('metricUsers').textContent = incident.impact.estimated_users;
  $('metricOperational').textContent = 'Operational';
  $('operationalChips').innerHTML = ['Cards', 'ATM', 'Branch', 'Active sessions'].map((x) => `<span>${x}</span>`).join('');
  renderPrimaryCta(config);
  renderActiveWorkstream();
  $('rawState').textContent = JSON.stringify({ state: incident.state, events: incident.events?.slice(-8) || [] }, null, 2);
  renderStageTracker();
  renderEvidence();
  renderAgents();
  renderDossier();
  renderTimeline();
  renderOperatorFocus();
  renderPrompts();
}

function renderPrimaryCta(config) {
  const cta = config.cta;
  const disabledBecauseBusy = state.investigating;
  $('primaryCta').textContent = disabledBecauseBusy ? 'DERA is working...' : cta.label;
  $('primaryCta').disabled = disabledBecauseBusy || !cta.enabled;
  const reason = disabledBecauseBusy ? 'Waiting for DERA to finish this investigation step.' : cta.reason;
  $('primaryCtaReason').textContent = reason || '';
  $('primaryCtaReason').hidden = !reason;
}

function renderStageTracker() {
  const s = currentState();
  const idx = orderIndex(s);
  $('stageTracker').innerHTML = STAGES.map((stage) => {
    let status = 'pending';
    const stageStateIndex = Math.min(...stage.states.map(orderIndex));
    if (stage.states.includes(s)) status = 'active';
    else if (idx > stageStateIndex) status = 'complete';
    if (stage.key === 'approval' && ['approved_local', 'rejected_local'].includes(s)) status = 'complete';
    return `<button class="stage-step ${status}" type="button" data-stage-tab="${stage.tab}"><span>${escapeHtml(stage.label)}</span><em>${status}</em></button>`;
  }).join('');
  document.querySelectorAll('[data-stage-tab]').forEach((btn) => btn.addEventListener('click', () => setActiveTab(btn.dataset.stageTab)));
}

function renderEvidence() {
  const lanes = [
    ['customer', 'A. Customer signal lane'],
    ['telemetry', 'B. Technical telemetry lane'],
    ['change', 'C. Change timeline lane'],
    ['recovery', 'D. Recovery lane'],
  ];
  const visible = getVisibleEvidence();
  $('evidenceCanvas').innerHTML = lanes.map(([lane, label]) => {
    const cards = visible.filter((ev) => ev.lane === lane);
    const body = cards.length ? cards.map((ev) => {
      const isSelected = state.selectedEvidence === ev.id;
      return `<button class="evidence-card ${isSelected ? 'selected' : ''}" data-evidence-id="${ev.id}"><span>${label.split('.')[0]}</span><strong>${escapeHtml(ev.title)}</strong><p>${escapeHtml(ev.summary)}</p><small>${escapeHtml((EVIDENCE_EXPLAINERS[ev.id]?.supports || ['Supports current case'])[0])}</small></button>`;
    }).join('') : '<div class="evidence-placeholder">Pending this investigation stage.</div>';
    return `<section class="evidence-lane" data-lane="${lane}"><h3>${label}</h3>${body}</section>`;
  }).join('');
  document.querySelectorAll('[data-evidence-id]').forEach((btn) => btn.addEventListener('click', () => openEvidence(btn.dataset.evidenceId)));
}

function agentHistory(agent) {
  const base = [`${agent.timestamp || 'now'} ${agent.status}`];
  if (agent.status === 'queued') base.push('Waiting for prerequisite evidence');
  if (agent.status === 'running') base.push('Reading evidence packet');
  if (agent.status === 'complete') base.push(`Finding produced: ${agent.finding}`);
  if (agent.status === 'blocked') base.push('Blocked: live DERA specialist reasoning unavailable');
  return base;
}

function renderAgentFlowGraph() {
  const agents = state.incident.subagents || [];
  const byId = Object.fromEntries(agents.map((agent) => [agent.id, agent]));
  const flow = [
    ['customer_signal', '1', 'Customer signal', 'complaints → journey impact'],
    ['observability', '2', 'Observability', 'latency → error rate'],
    ['change_correlation', '3', 'Change correlation', 'release window → blast radius'],
    ['recovery', '4', 'Recovery', 'rollback plan → customer wording'],
  ];
  const supervisor = byId.supervisor || agents[0];
  const activeAgent = agentById(state.activeAgentId) || agents.find((agent) => agent.status === 'running') || supervisor;
  const completeCount = agents.filter((agent) => agent.status === 'complete').length;
  const runningCount = agents.filter((agent) => agent.status === 'running').length;
  const queuedCount = agents.filter((agent) => agent.status === 'queued').length;
  const progress = agents.length ? Math.round((completeCount / agents.length) * 100) : 0;
  const currentOperation = activeAgent
    ? (state.activeAgentId === activeAgent.id && state.agentWorkLog.length ? state.agentWorkLog[state.agentWorkLog.length - 1] : activeAgent.finding)
    : 'Ready to coordinate the specialist flow.';
  const specialistNodes = flow.map(([id, step, label, route], index) => {
    const agent = byId[id];
    if (!agent) return '';
    const isActive = state.activeAgentId === id || (!state.activeAgentId && agent.status === 'running');
    const status = isActive && state.investigating ? 'working now' : agent.status;
    const confidence = agent.confidence == null ? 'pending' : `${Math.round(agent.confidence * 100)}%`;
    return `
      <button class="agent-flow-step ${agent.status} ${isActive ? 'active' : ''}" data-agent-open="${escapeHtml(id)}" style="--i:${index}">
        <span class="step-index">${escapeHtml(step)}</span>
        <span class="step-copy">
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml(route)}</small>
        </span>
        <span class="step-meta">
          <span class="node-orb"></span>
          <em>${escapeHtml(status)}</em>
          <small>${escapeHtml(confidence)}</small>
        </span>
      </button>`;
  }).join('');
  return `
    <section class="agent-flow" aria-label="DERA agent hierarchy and information flow">
      <div class="agent-flow-hero">
        <div class="agent-flow-copy">
          <span class="eyebrow">Living DERA agent graph</span>
          <h3>Supervisor hub with specialist dependency flow</h3>
          <p>DERA routes customer pain through technical evidence, change correlation, and recovery planning, then returns a supervised decision package.</p>
        </div>
        <div class="agent-flow-stats" aria-label="Agent work summary">
          <span><strong>${completeCount}</strong> complete</span>
          <span><strong>${runningCount}</strong> running</span>
          <span><strong>${queuedCount}</strong> queued</span>
        </div>
      </div>
      <div class="agent-map-shell">
        <button class="agent-supervisor-hub ${supervisor?.status || 'queued'} ${state.activeAgentId === 'supervisor' ? 'active' : ''}" data-agent-open="supervisor">
          <span class="hub-ring"><span class="hub-core"><span class="node-orb"></span></span></span>
          <span class="hub-copy">
            <em>Supervisor</em>
            <strong>${escapeHtml(supervisor?.name || 'Digital Experience Supervisor')}</strong>
            <small>${escapeHtml(supervisor?.status || 'queued')} · evidence router</small>
          </span>
        </button>
        <div class="agent-dependency-rail" aria-label="Specialist dependency chain">${specialistNodes}</div>
        <div class="agent-pulse-panel">
          <span class="eyebrow">Active pulse</span>
          <strong>${escapeHtml(activeAgent?.name || 'DERA')}</strong>
          <p>${escapeHtml(currentOperation)}</p>
          <div class="agent-progress"><span style="width:${progress}%"></span></div>
          <small>${progress}% of specialist work complete</small>
        </div>
      </div>
    </section>`;
}

function renderAgents() {
  const cards = state.incident.subagents.map((agent) => {
    const evidenceId = agent.evidence_id;
    const evidenceChip = evidenceId ? `<button class="evidence-chip" data-evidence-id="${evidenceId}">${evidenceId}</button>` : '<span class="muted-text">No evidence linked</span>';
    const isActive = state.activeAgentId === agent.id;
    return `
    <article class="agent-card ${agent.status} ${isActive ? 'active-agent' : ''}" data-agent-id="${escapeHtml(agent.id)}">
      <div><strong>${escapeHtml(agent.name)}</strong><span class="agent-status">${escapeHtml(isActive && state.investigating ? 'running live' : agent.status)}</span></div>
      <p><b>Task:</b> ${escapeHtml(agent.task)}</p>
      <p><b>Current operation:</b> ${escapeHtml(isActive && state.agentWorkLog.length ? state.agentWorkLog[state.agentWorkLog.length - 1] : agent.tool)}</p>
      <p><b>Finding:</b> ${escapeHtml(agent.finding)}</p>
      <div class="agent-evidence"><b>Evidence:</b> ${evidenceChip}</div>
      <ol class="agent-history">${agentHistory(agent).map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ol>
      <footer><span>Confidence: ${agent.confidence == null ? 'pending' : agent.confidence.toFixed(2)}</span><button class="link-btn" data-agent-open="${escapeHtml(agent.id)}">Open work</button><button class="link-btn" data-evidence-id="${evidenceId}">View evidence</button><span>${escapeHtml(agent.timestamp)}</span></footer>
    </article>`;
  }).join('');
  $('agentList').innerHTML = `${renderAgentFlowGraph()}<div class="agent-card-grid">${cards}</div>`;
  document.querySelectorAll('.agent-card, .agent-flow-step, .agent-supervisor-hub').forEach((card) => card.addEventListener('click', (event) => {
    if (event.target.closest('[data-evidence-id]')) return;
    openAgentDrawer(card.dataset.agentId || card.dataset.agentOpen);
  }));
  document.querySelectorAll('[data-agent-open]').forEach((btn) => btn.addEventListener('click', (event) => { event.stopPropagation(); openAgentDrawer(btn.dataset.agentOpen); }));
  document.querySelectorAll('.agent-card [data-evidence-id]').forEach((btn) => btn.addEventListener('click', (event) => { event.stopPropagation(); openEvidence(btn.dataset.evidenceId); }));
}

function openAgentDrawer(agentId) {
  const agent = agentById(agentId);
  if (!agent) return;
  const isActive = state.activeAgentId === agent.id && state.investigating;
  const workLog = isActive ? state.agentWorkLog : agentHistory(agent);
  const evidenceId = agent.evidence_id;
  $('agentDrawerKicker').textContent = isActive ? 'Live agent workstream' : 'Agent workstream';
  $('agentDrawerTitle').textContent = agent.name;
  $('agentDrawerSummary').textContent = isActive ? 'DERA is actively working on this specialist step now.' : agent.finding;
  $('agentDrawerBody').innerHTML = `
    <section><h3>Status</h3><p><strong>${escapeHtml(isActive ? 'running live' : agent.status)}</strong> · Confidence ${agent.confidence == null ? 'pending' : agent.confidence.toFixed(2)}</p></section>
    <section><h3>Visible reasoning summary</h3><p>${escapeHtml(AGENT_REASONING_SUMMARIES[agent.id] || AGENT_REASONING_SUMMARIES.supervisor)}</p><p class="microcopy">This is an operator-facing summary of the agent's work, not hidden chain-of-thought.</p></section>
    <section><h3>Tool / action</h3><p>${escapeHtml(isActive && workLog.length ? workLog[workLog.length - 1] : agent.tool)}</p></section>
    <section><h3>Work log</h3><ol>${workLog.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ol></section>
    <section><h3>Evidence consumed</h3>${evidenceId ? `<button class="evidence-chip" data-evidence-id="${escapeHtml(evidenceId)}">${escapeHtml(evidenceId)}</button>` : '<p class="muted-text">No evidence linked yet.</p>'}</section>`;
  $('agentDrawer').hidden = false;
  $('agentDrawerBody').querySelector('[data-evidence-id]')?.addEventListener('click', (event) => openEvidence(event.currentTarget.dataset.evidenceId));
}

function renderDossierReadiness() {
  const items = getDossierReadiness();
  $('dossierReadiness').innerHTML = `<h3>Dossier readiness</h3><div class="readiness-grid">${items.map((item) => `<button class="readiness-item ${item.status}" type="button" data-readiness-tab="${item.tab}" data-evidence-id="${item.evidence || ''}"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.status.replace('_', ' '))}</span>${item.evidence ? `<small>${escapeHtml(item.evidence)}</small>` : '<small>local gate</small>'}</button>`).join('')}</div>`;
  document.querySelectorAll('[data-readiness-tab]').forEach((btn) => btn.addEventListener('click', () => {
    setActiveTab(btn.dataset.readinessTab);
    if (btn.dataset.evidenceId) openEvidence(btn.dataset.evidenceId);
  }));
}

function renderDossier() {
  const { dossier } = state.incident;
  const ready = ['dossier_ready', 'approval_required', 'approved_local', 'rejected_local'].includes(state.incident.state);
  renderDossierReadiness();
  $('dossierStatus').textContent = ready ? 'Recovery dossier ready for decision' : 'Dossier prerequisites pending';
  $('confidenceChip').textContent = ready ? `Confidence ${dossier.confidence.toFixed(2)}` : 'Confidence pending';
  $('confidenceChip').className = ready ? 'pill good' : 'pill muted';
  $('revisionTools').hidden = !ready;
  $('approvalGate').hidden = state.incident.state !== 'approval_required';
  if (!ready) {
    const pending = getDossierReadiness().filter((item) => item.status === 'pending').map((item) => item.label).join(', ');
    $('dossierContent').innerHTML = `<p class="muted-text">DERA still needs: ${escapeHtml(pending || 'final synthesis')}. Use the primary CTA to continue the investigation.</p>`;
    return;
  }
  $('dossierContent').innerHTML = `
    <div><span>Executive summary</span><p>${escapeHtml(dossier.executive_summary)}</p></div>
    <div><span>Customer impact</span><p>${escapeHtml(dossier.customer_impact)}</p></div>
    <div><span>Evidence chain</span><p>${escapeHtml(dossier.evidence_chain.join(' → '))}</p></div>
    <div><span>Root-cause hypothesis</span><p>${escapeHtml(dossier.root_cause_hypothesis)}</p></div>
    <div><span>Recommended recovery</span><p>${escapeHtml(dossier.recommended_recovery)}</p></div>
    <div><span>Validation plan</span><p>MFA latency, auth gateway 504 rate, login completion, complaint trend, and delayed SMS backlog.</p></div>
    <div><span>Customer communication</span><p>${escapeHtml(dossier.customer_communication)}</p></div>
    <div><span>What remains operational</span><p>${escapeHtml(dossier.operational_remainder)}</p></div>
    <div><span>Risks and uncertainty</span><p>${escapeHtml(dossier.risks)}</p></div>`;
}

function renderTimeline() {
  if (!state.incident) return;
  const fixed = [
    { time: '09:51', title: 'Customer pain emerges', body: 'Complaint spike: MFA codes not arriving during login.', state: 'ready_with_incident', source: 'Practice baseline' },
    { time: '09:52', title: 'Customer signal clustering', body: 'DERA Customer Signal Agent clusters masked complaints.', state: 'investigating.customer_signal', source: 'DERA event' },
    { time: '09:53', title: 'Telemetry check', body: 'Observability examines auth gateway latency and 504 errors.', state: 'investigating.observability', source: 'DERA event' },
    { time: '09:54', title: 'Change correlation', body: 'DERA compares the incident window with CHG-1048.', state: 'investigating.change_correlation', source: 'DERA event' },
    { time: '09:55', title: 'Recovery planning', body: 'Recovery & Communication Agent prepares rollback and messaging.', state: 'investigating.recovery_planning', source: 'DERA event' },
    { time: '09:56', title: 'Human gate', body: 'Dossier is ready for local approval or rejection.', state: 'approval_required', source: 'Operator action' },
  ];
  const currentIdx = orderIndex(state.incident.state);
  const liveEvents = (state.incident.events || []).slice(-8).map((event) => ({ time: (event.created_at || '').slice(11, 16) || 'now', title: event.event_type, body: JSON.stringify(event.payload), live: true, source: 'Runtime event' }));
  $('timelineRail').innerHTML = [
    ...fixed.map((item) => {
      const done = orderIndex(item.state) <= currentIdx;
      return `<article class="timeline-item ${done ? 'done' : ''}"><time>${item.time}</time><div><strong>${escapeHtml(item.title)}</strong><span class="source-badge">${escapeHtml(item.source)}</span><p>${escapeHtml(item.body)}</p></div></article>`;
    }),
    ...liveEvents.map((item) => `<article class="timeline-item live"><time>${item.time}</time><div><strong>${escapeHtml(item.title)}</strong><span class="source-badge">${escapeHtml(item.source)}</span><p>${escapeHtml(item.body)}</p></div></article>`),
  ].join('');
}

function renderOperatorFocus() {
  const focus = currentConfig().focus;
  $('operatorFocus').textContent = focus[0];
  $('operatorGuidance').textContent = focus[1];
}

function setActiveTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.tab').forEach((button) => button.classList.toggle('active', button.dataset.tab === tab));
  document.querySelectorAll('.tab-panel').forEach((panel) => panel.classList.toggle('active', panel.id === `tab-${tab}`));
}

function renderPrompts() {
  const prompts = currentConfig().prompts || PRODUCT_STATES.ready_with_incident.prompts;
  $('suggestedPrompts').innerHTML = prompts.map((prompt) => `<button class="prompt-chip" type="button">${escapeHtml(prompt)}</button>`).join('');
  document.querySelectorAll('.prompt-chip').forEach((btn) => btn.addEventListener('click', () => askHermes(btn.textContent)));
}

function openEvidence(id) {
  const evidence = (state.incident.evidence || []).find((item) => item.id === id);
  if (!evidence) return;
  state.selectedEvidence = id;
  const explainer = EVIDENCE_EXPLAINERS[id] || { supports: ['Supports current incident analysis'], limitations: ['No additional limitations supplied'] };
  $('drawerLane').textContent = `${evidence.lane} evidence`;
  $('drawerTitle').textContent = evidence.title;
  $('drawerSummary').textContent = evidence.summary;
  $('drawerHumanDetails').innerHTML = `
    <section><h3>What this supports</h3><ul>${explainer.supports.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section>
    <section><h3>Limitations</h3><ul>${explainer.limitations.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section>`;
  $('drawerDetails').textContent = JSON.stringify(evidence.details, null, 2);
  $('evidenceDrawer').hidden = false;
  renderEvidence();
}

async function init() {
  try {
    const health = await api('/health');
    setRuntimeStatus(health);
    state.incident = await api('/api/incidents', { method: 'POST', body: JSON.stringify({}) });
    renderIncident();
    state.incident.chat.forEach((msg) => addChat(msg.role, msg.content, msg.adapter_mode));
  } catch (error) {
    $('backendStatus').textContent = 'Backend not connected';
    $('backendStatus').className = 'pill danger';
    $('hermesStatus').textContent = 'Waiting for backend';
    $('incidentState').textContent = 'Connection required';
    addChat('hermes', `Backend connection failed: ${error.message}`);
  }
}

async function performPrimaryAction() {
  const action = currentConfig().cta.action;
  if (action === 'show_dossier') { setActiveTab('dossier'); return; }
  if (action === 'advance') { await advanceInvestigationStep(); }
}

async function advanceInvestigationStep() {
  if (!state.incident || state.investigating) return;
  if (['approval_required', 'approved_local', 'rejected_local'].includes(state.incident.state)) { setActiveTab('dossier'); return; }
  const targetState = nextIncidentState();
  const activeAgent = optimisticAgentFor(targetState);
  state.investigating = true;
  setActiveTab('agents');
  renderIncident();
  renderActiveWorkstream();
  if (activeAgent) startAgentWorkAnimation(activeAgent.id);
  try {
    const [updatedIncident] = await Promise.all([
      api(`/api/incidents/${state.incident.id}/investigate`, { method: 'POST', body: JSON.stringify({}) }),
      wait(900),
    ]);
    state.incident = updatedIncident;
    stopAgentWorkAnimation(false);
    const completedAgentId = AGENT_BY_TARGET_STATE[state.incident.state] || state.activeAgentId;
    state.activeAgentId = completedAgentId;
    state.agentWorkLog.push('DERA returned specialist result');
    const nextTab = ['dossier_ready', 'approval_required'].includes(state.incident.state) ? 'dossier' : 'agents';
    setActiveTab(nextTab);
    renderIncident();
    if (!$('agentDrawer').hidden && completedAgentId) openAgentDrawer(completedAgentId);
    if (state.incident.state === 'approval_required') addChat('hermes', 'The evidence chain is complete. Review the recovery dossier and use the supervised approval gate.');
    window.setTimeout(() => { if (!state.investigating) stopAgentWorkAnimation(true); renderIncident(); }, 1400);
  } catch (error) {
    stopAgentWorkAnimation(true);
    addChat('hermes', `Investigation error: ${error.message}`, 'hermes-unavailable');
  } finally {
    state.investigating = false;
    renderIncident();
  }
}

function showChatInputHint(message = 'Type a question, or click one of the suggested prompt chips above.') {
  const hint = $('chatHint');
  if (hint) {
    hint.textContent = message;
    hint.hidden = false;
  }
  $('chatInput').classList.add('needs-input');
  $('chatInput').focus();
  window.setTimeout(() => {
    $('chatInput').classList.remove('needs-input');
  }, 900);
}

function clearChatInputHint() {
  const hint = $('chatHint');
  if (hint) hint.hidden = true;
  $('chatInput').classList.remove('needs-input');
}

function chatQuestionFromInput() {
  return $('chatInput').value.trim();
}

async function routeDashboardCommand(question) {
  const q = question.toLowerCase();
  if (/\b(technical timeline|why|what|how|explain|summarize|list|compare)\b/.test(q)) return false;
  let action = '';
  if (/\b(show|open|switch|bring).*(agent|workstream|working)|\bagents?\b.*\bworking\b/.test(q)) {
    setActiveTab('agents');
    action = 'Opening the live agent workstream now. You can see who is queued, running, complete, and which evidence each agent is using.';
  } else if (/\b(show|open|switch|bring).*(evidence|proof)/.test(q)) {
    setActiveTab('evidence');
    action = 'Opening the evidence canvas now, with customer signal, telemetry, change, and recovery evidence grouped by lane.';
  } else if (/\b(show|open|switch|bring).*(dossier|approval|recovery plan)/.test(q)) {
    setActiveTab('dossier');
    action = 'Opening the recovery dossier now, including readiness, recommended action, risks, and the local approval gate when available.';
  } else if (/\b(show|open|switch|bring).*(timeline|chronology)/.test(q)) {
    setActiveTab('timeline');
    action = 'Opening the chronology now so you can follow the incident sequence in order.';
  } else if (/\b(show|open|switch|bring).*(voice|talk)|\bvoice mode\b/.test(q)) {
    setActiveTab('voice');
    action = 'Opening voice mode settings now. Talk stays in the DERA command rail, with microphone and audio controls separated.';
  } else if (/\b(expand|bigger|larger|full).*(chat|hermes)|\bfullscreen chat\b/.test(q)) {
    if (!state.chatExpanded) toggleChatExpanded();
    action = 'Expanded the DERA command rail so the conversation has more room.';
  } else if (/\b(collapse|smaller).*(chat|hermes)/.test(q)) {
    if (state.chatExpanded) toggleChatExpanded();
    action = 'Collapsed the DERA command rail back to the normal cockpit layout.';
  } else if (/\b(start|continue|advance|next).*(investigation|telemetry|correlate|recovery|dossier)|\bstart investigation\b|\bcontinue\b/.test(q)) {
    action = 'Advancing the investigation now. I’ll move the cockpit to the next workstream and show the live agent activity.';
    await performPrimaryAction();
  }
  if (!action) return false;
  addChat('hermes', action, state.hermesConnected ? 'hermes-api' : 'hermes-unavailable');
  speakLiveChunk(action, { interrupt: true });
  return true;
}

function inferDashboardPlacement(question) {
  const q = question.toLowerCase();
  let targetTab = '';
  let selectedEvidence = '';
  if (/\b(evidence|proof|support|supports|why|suspect|uncertain|uncertainty|complaint|telemetry|latency|504|change|chg-?1048|rollback)\b/.test(q)) {
    targetTab = 'evidence';
  }
  if (/\b(agent|agents|workstream|working|specialist|supervisor|observability|customer signal|correlation|recovery agent)\b/.test(q)) {
    targetTab = 'agents';
  }
  if (/\b(dossier|approve|approval|risk|risks|customer message|executive|recovery plan|decision)\b/.test(q)) {
    targetTab = 'dossier';
  }
  if (/\b(timeline|chronology|sequence|when|window|history|unfolded)\b/.test(q)) {
    targetTab = 'timeline';
  }
  if (/\bvoice|sound|talk|mic|microphone\b/.test(q)) {
    targetTab = 'voice';
  }
  if (/complaint|customer pain|mfa|customer signal/.test(q)) selectedEvidence = 'ev_customer_complaints';
  if (/telemetry|latency|504|auth gateway|observability/.test(q)) selectedEvidence = 'ev_telemetry_latency';
  if (/chg-?1048|change|release|deploy/.test(q)) selectedEvidence = 'ev_change_chg1048';
  if (/rollback|recovery plan|validation|customer message/.test(q)) selectedEvidence = 'ev_recovery_plan';
  return { targetTab, selectedEvidence };
}

function applyQuestionPlacement(question) {
  const placement = inferDashboardPlacement(question);
  if (!placement.targetTab) return null;
  if (placement.targetTab !== state.activeTab) setActiveTab(placement.targetTab);
  if (placement.selectedEvidence && placement.targetTab === 'evidence') {
    state.selectedEvidence = placement.selectedEvidence;
    renderEvidence();
  }
  return placement;
}

async function askHermes(question) {
  const cleanQuestion = String(question || '').trim();
  if (!cleanQuestion) {
    showChatInputHint();
    return;
  }
  if (!state.incident) return;
  clearChatInputHint();
  addChat('operator', cleanQuestion);
  $('chatInput').value = '';
  if (await routeDashboardCommand(cleanQuestion)) return;
  applyQuestionPlacement(cleanQuestion);
  const pending = addHermesWritingMessage('Opening incident and dashboard context...');
  try {
    await streamHermesMessage(pending, cleanQuestion);
  } catch (streamError) {
    state.streamPhase = 'stream_error';
    updateHermesProgress(pending, 'Streaming failed. Trying non-streaming DERA response...');
    try {
      const result = await api(`/api/incidents/${state.incident.id}/ask`, { method: 'POST', body: JSON.stringify({ question: cleanQuestion, voice_mode: state.voiceMode, dashboard_context: dashboardContextForChat() }) });
      await typeHermesMessage(pending, result.answer, result.adapter_mode);
    } catch (error) {
      await typeHermesMessage(pending, `I could not answer from the backend: ${error.message || streamError.message}`, 'hermes-unavailable');
    }
  }
}

async function reviseDossier() {
  if (!state.incident) return;
  const field = $('revisionField').value;
  const instruction = $('revisionInstruction').value || 'Make this clearer and safer for operators.';
  addChat('operator', `Revise ${field}: ${instruction}`);
  const pending = addHermesWritingMessage('Sending dossier revision to DERA...');
  try {
    await api(`/api/incidents/${state.incident.id}/dossier/revise`, { method: 'POST', body: JSON.stringify({ field, instruction }) });
    state.incident = await api(`/api/incidents/${state.incident.id}/state`);
    renderIncident();
    await typeHermesMessage(pending, `Revised ${field}. The dossier is ready for local approval review.`, state.hermesConnected ? 'hermes-api' : 'hermes-unavailable');
  } catch (error) {
    await typeHermesMessage(pending, `Dossier revision failed: ${error.message}`, 'hermes-unavailable');
  }
}

async function recordApproval(decision) {
  state.incident = await api(`/api/incidents/${state.incident.id}/approval`, { method: 'POST', body: JSON.stringify({ decision }) });
  renderIncident();
  addChat('hermes', decision === 'approved_local' ? 'Local recovery approval recorded. No external action was executed.' : 'Recommendation rejected locally. No external action was executed.', state.hermesConnected ? 'hermes-api' : 'hermes-unavailable');
}

function speak(text) {
  if (!('speechSynthesis' in window)) { $('voiceStatus').textContent = 'Browser speech synthesis unavailable. Text chat remains available.'; return; }
  state.voiceMode = true;
  updateVoiceControls();
  setVoiceBubble('DERA is talking', 'Speaking the requested summary — no telephony connected.', 'speaking');
  speakLiveChunk(text, { interrupt: true });
}

function setupVoice() {
  updateVoiceControls();
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    $('voiceListenBtn').disabled = true;
    $('voiceStatus').textContent = 'Browser speech recognition unavailable. Text chat is always available.';
    return;
  }
  state.recognition = new Recognition();
  state.recognition.lang = 'en-US';
  state.recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript;
    $('chatInput').value = transcript;
    setVoiceBubble('DERA heard you', transcript, 'listening');
    askHermes(transcript);
  };
  state.recognition.onstart = () => setVoiceBubble('Listening', 'Listening through browser microphone permission — no telephony connected.', 'listening');
  state.recognition.onerror = () => setVoiceBubble('Voice input failed', 'Permission failed or browser voice input stopped. Text chat is still available.', 'muted');
  state.recognition.onend = () => { if (state.voiceMode) setVoiceBubble('Voice mode ready', 'Ask another question, mute, or stop conversation to return to text.', 'listening'); };
}

function bind() {
  document.querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => setActiveTab(button.dataset.tab)));
  $('expandChatBtn').addEventListener('click', toggleChatExpanded);
  $('primaryCta').addEventListener('click', performPrimaryAction);
  $('chatForm').addEventListener('submit', (event) => { event.preventDefault(); askHermes(chatQuestionFromInput()); });
  $('technicalTimelineBtn').addEventListener('click', () => askHermes('Show me the technical timeline.'));
  $('drawerClose').addEventListener('click', () => { $('evidenceDrawer').hidden = true; state.selectedEvidence = null; renderEvidence(); });
  $('agentDrawerClose').addEventListener('click', () => { $('agentDrawer').hidden = true; });
  $('reviseBtn').addEventListener('click', reviseDossier);
  $('approveBtn').addEventListener('click', () => recordApproval('approved_local'));
  $('rejectBtn').addEventListener('click', () => recordApproval('rejected_local'));
  $('voiceModeBtn').addEventListener('click', startVoiceConversation);
  $('micVoiceBtn').addEventListener('click', toggleMicMute);
  $('muteVoiceBtn').addEventListener('click', toggleVoiceMute);
  $('stopVoiceBtn').addEventListener('click', stopVoiceConversation);
  $('voiceListenBtn').addEventListener('click', startVoiceConversation);
  $('speakSituationBtn').addEventListener('click', () => speak(`Current situation: ${state.incident?.title}. ${state.incident?.impact.complaint_spike} complaint spike in ${state.incident?.impact.affected_journey}.`));
  $('speakDossierBtn').addEventListener('click', () => speak(state.incident?.dossier?.executive_summary || 'The dossier is not ready yet.'));
  $('simulateCallerBtn').addEventListener('click', () => askHermes('I cannot receive my MFA code. Is my card still working?'));
}

bind();
setupVoice();
init();
