/**
 * AgriShield - Main Frontend Application
 * Fully offline-ready, multilingual (ta, hi, te, kn, ml, en), voice-first with Web Speech API
 */

let state = {
  currentPlotId: "plot_1",
  currentLang: localStorage.getItem("agrishield_lang") || "ta", // default Tamil for delta demo
  currentMode: "farmer", // 'farmer' or 'officer'
  currentTab: "protect",
  plots: [],
  currentPlotData: null,
  i18n: null,
  predictMap: null,
  predictPolygon: null,
  proveMap: null,
  proveGridLayer: null,
  proveCloudLayer: null,
  isRadarView: true,
  ndviChart: null,
  speechVoices: [],
  recognition: null,
  isListening: false
};

// Available languages metadata
const LANGUAGES_CONFIG = [
  { code: "ta", native: "தமிழ்", bcp: "ta-IN", speechName: "தமிழ்" },
  { code: "hi", native: "हिन्दी", bcp: "hi-IN", speechName: "हिन्दी" },
  { code: "te", native: "తెలుగు", bcp: "te-IN", speechName: "తెలుగు" },
  { code: "kn", native: "ಕನ್ನಡ", bcp: "kn-IN", speechName: "ಕನ್ನಡ" },
  { code: "ml", native: "മലയാളം", bcp: "ml-IN", speechName: "മലയാളം" },
  { code: "en", native: "English", bcp: "en-IN", speechName: "English" }
];

// Document Ready Initialization
document.addEventListener("DOMContentLoaded", async () => {
  initVoiceEngine();
  await loadI18n();
  renderLanguageBar();
  await loadPlots();
  applyLanguage(state.currentLang);
  await selectPlot(state.currentPlotId, false); // initial plot without auto-speech interrupt
});

// ----------------- VOICE ENGINE (Web Speech API) -----------------

function initVoiceEngine() {
  if ("speechSynthesis" in window) {
    const updateVoices = () => {
      state.speechVoices = window.speechSynthesis.getVoices();
    };
    updateVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }

  // Setup Web Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    try {
      state.recognition = new SpeechRecognition();
      state.recognition.continuous = false;
      state.recognition.interimResults = false;

      state.recognition.onstart = () => {
        state.isListening = true;
        const micBtn = document.getElementById("btn-farmer-mic");
        const micText = document.getElementById("btn-mic-text");
        if (micBtn) micBtn.classList.add("listening");
        if (micText) micText.innerText = getI18nText("ui.listening", "Listening...");
      };

      state.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleFarmerVoiceInput(transcript);
      };

      state.recognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        stopVoiceRecognition();
      };

      state.recognition.onend = () => {
        stopVoiceRecognition();
      };
    } catch (e) {
      console.warn("Speech recognition init error:", e);
    }
  }
}

function speakText(text, langCode = state.currentLang, onEndCallback = null) {
  if (!("speechSynthesis" in window)) {
    console.warn("Speech synthesis not supported");
    return;
  }

  window.speechSynthesis.cancel(); // Stop any pending speech

  const langObj = LANGUAGES_CONFIG.find(l => l.code === langCode) || LANGUAGES_CONFIG[5];
  const bcpCode = langObj.bcp;

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = bcpCode;
  utterance.rate = 0.95; // comfortable cadence for rural comprehension

  // Attempt to find voice matching language
  const voices = state.speechVoices.length ? state.speechVoices : window.speechSynthesis.getVoices();
  const matchedVoice = voices.find(v => v.lang === bcpCode || v.lang.startsWith(langCode));

  const warnEl = document.getElementById("voice-warning");
  if (matchedVoice) {
    utterance.voice = matchedVoice;
    if (warnEl) warnEl.style.display = "none";
  } else {
    // Fallback to English voice if device lacks Indic voice
    const enVoice = voices.find(v => v.lang.includes("en"));
    if (enVoice && langCode !== "en") {
      utterance.voice = enVoice;
      if (warnEl) warnEl.style.display = "block";
    }
  }

  utterance.onend = () => {
    if (onEndCallback) onEndCallback();
  };
  utterance.onerror = () => {
    if (onEndCallback) onEndCallback();
  };

  window.speechSynthesis.speak(utterance);
}

function stopVoiceRecognition() {
  state.isListening = false;
  const micBtn = document.getElementById("btn-farmer-mic");
  const micText = document.getElementById("btn-mic-text");
  if (micBtn) micBtn.classList.remove("listening");
  if (micText) micText.innerText = getI18nText("ui.ask_mic", "Ask AgriShield");
}

function toggleVoiceRecognition() {
  if (!state.recognition) {
    alert("Speech recognition is not supported in this browser. Please use the quick picture buttons below!");
    return;
  }
  if (state.isListening) {
    state.recognition.stop();
  } else {
    const langObj = LANGUAGES_CONFIG.find(l => l.code === state.currentLang);
    state.recognition.lang = langObj ? langObj.bcp : "ta-IN";
    try {
      state.recognition.start();
    } catch (e) {
      console.warn("Recognition start error:", e);
    }
  }
}

// ----------------- I18N AND LOCALIZATION -----------------

async function loadI18n() {
  try {
    const res = await fetch("/data/i18n.json");
    state.i18n = await res.json();
  } catch (e) {
    console.error("Failed to load i18n:", e);
  }
}

function getI18nText(path, fallback = "") {
  if (!state.i18n || !state.i18n.languages) return fallback;
  const langData = state.i18n.languages[state.currentLang] || state.i18n.languages["en"];
  const parts = path.split(".");
  let cur = langData;
  for (const part of parts) {
    if (!cur || cur[part] === undefined) return fallback;
    cur = cur[part];
  }
  return cur || fallback;
}

function renderLanguageBar() {
  const container = document.getElementById("lang-bar");
  if (!container) return;
  container.innerHTML = "";

  LANGUAGES_CONFIG.forEach(item => {
    const chip = document.createElement("button");
    chip.className = `lang-chip ${state.currentLang === item.code ? "active" : ""}`;
    chip.id = `lang-chip-${item.code}`;
    chip.innerHTML = `
      <span>${item.native}</span>
      <span class="lang-speak-icon" title="Listen language name">🔊</span>
    `;
    chip.onclick = () => {
      selectLanguage(item.code);
    };
    container.appendChild(chip);
  });
}

function selectLanguage(code) {
  state.currentLang = code;
  localStorage.setItem("agrishield_lang", code);

  // Update chips styling
  document.querySelectorAll(".lang-chip").forEach(el => el.classList.remove("active"));
  const activeChip = document.getElementById(`lang-chip-${code}`);
  if (activeChip) activeChip.classList.add("active");

  applyLanguage(code);

  // Pronounce language name
  const langObj = LANGUAGES_CONFIG.find(l => l.code === code);
  if (langObj) {
    speakText(langObj.speechName, code);
  }

  // Refresh current plot view with new language
  if (state.currentPlotData) {
    updateFarmerModeUI();
    updateSmsSimulator();
  }
}

function applyLanguage(code) {
  // Update header text
  const titleEl = document.getElementById("app-title");
  const subEl = document.getElementById("app-subtitle");
  const bannerEl = document.getElementById("banner-text");
  const farmerModeEl = document.getElementById("lbl-farmer-mode");
  const officerModeEl = document.getElementById("lbl-officer-mode");
  const selectFarmerEl = document.getElementById("lbl-select-farmer");
  const quickQEl = document.getElementById("lbl-quick-questions");

  if (titleEl) titleEl.innerText = getI18nText("ui.title", "AgriShield");
  if (subEl) subEl.innerText = getI18nText("ui.subtitle", "Protect • Predict • Prove • Pay");
  if (bannerEl) bannerEl.innerText = getI18nText("ui.sample_banner", "Demo uses simulated data modeled on Sentinel-1/2");
  if (farmerModeEl) farmerModeEl.innerText = getI18nText("ui.farmer_mode", "Farmer Voice Mode");
  if (officerModeEl) officerModeEl.innerText = getI18nText("ui.officer_mode", "Officer / Insurer Mode");
  if (selectFarmerEl) selectFarmerEl.innerText = getI18nText("ui.select_farmer", "Select Farmer");
  if (quickQEl) quickQEl.innerText = getI18nText("ui.quick_actions", "Quick Questions (Tap to Ask):");

  // Weather, Chatbot, and Loans UI labels
  const weatherTitle = document.getElementById("lbl-weather-title");
  const weatherSub = document.getElementById("lbl-weather-sub");
  const chatbotTitle = document.getElementById("lbl-chatbot-title");
  const chatbotSub = document.getElementById("lbl-chatbot-sub");
  const loanPortalTitle = document.getElementById("lbl-loan-portal-title");
  const applyLoanBtn = document.getElementById("btn-apply-loan-label");
  const damageMappingTitle = document.getElementById("lbl-damage-mapping-title");
  const firstStepTitle = document.getElementById("lbl-first-step-title");
  const reqTitle = document.getElementById("lbl-requirements-title");
  const whereApplyTitle = document.getElementById("lbl-where-apply-title");
  const chatInput = document.getElementById("chat-input");

  if (weatherTitle) weatherTitle.innerText = getI18nText("ui.weather_title", "Weather & Satellite Resources");
  if (weatherSub) weatherSub.innerText = getI18nText("ui.weather_subtitle", "Sentinel-1 Radar Moisture, Rainfall Forecast & Agro-Advisories");
  if (chatbotTitle) chatbotTitle.innerText = getI18nText("ui.chatbot_title", "AgriShield AI Assistant");
  if (chatbotSub) chatbotSub.innerText = getI18nText("ui.chatbot_subtitle", "Ask questions to analyze crop health, weather, and farm credit decisions");
  if (loanPortalTitle) loanPortalTitle.innerText = getI18nText("ui.loan_portal_title", "Crop Loans & Disaster Relief Portal");
  if (applyLoanBtn) applyLoanBtn.innerText = getI18nText("ui.apply_loan_btn", "📝 Apply for Loan / Relief Now");
  if (damageMappingTitle) damageMappingTitle.innerText = getI18nText("ui.damage_mapping_title", "For Which Damage What Loan Applies?");
  if (firstStepTitle) firstStepTitle.innerText = getI18nText("ui.first_step_title", "First Step What Farmer Must Take");
  if (reqTitle) reqTitle.innerText = getI18nText("ui.requirements_title", "📋 Required Documents Checklist:");
  if (whereApplyTitle) whereApplyTitle.innerText = getI18nText("ui.where_apply_title", "📍 Where to Apply:");
  if (chatInput) chatInput.placeholder = getI18nText("ui.chat_placeholder", "Ask about crop health, rain, flood, or loans...");

  // Render 5 large picture buttons
  renderPictureIntents();
  updateChatbotWelcome();
}

function renderPictureIntents() {
  const container = document.getElementById("picture-intents");
  if (!container || !state.i18n) return;

  const quickBtns = state.i18n.languages[state.currentLang]?.quick_buttons || state.i18n.languages["en"].quick_buttons;
  container.innerHTML = "";

  Object.entries(quickBtns).forEach(([key, btn]) => {
    const btnEl = document.createElement("button");
    btnEl.className = "picture-intent-btn";
    btnEl.innerHTML = `
      <span class="picture-intent-icon">${btn.icon}</span>
      <span class="picture-intent-label">${btn.label}</span>
    `;
    btnEl.onclick = () => {
      triggerIntent(key, btn.question);
    };
    container.appendChild(btnEl);
  });
}

// ----------------- PLOTS DATA LOADING -----------------

async function loadPlots() {
  try {
    const res = await fetch("/api/plots");
    const data = await res.json();
    state.plots = data.plots;
    renderFarmerChips();
  } catch (e) {
    console.error("Failed to load plots:", e);
  }
}

function renderFarmerChips() {
  const container = document.getElementById("farmer-chips");
  if (!container) return;
  container.innerHTML = "";

  state.plots.forEach(plot => {
    const chip = document.createElement("div");
    chip.className = `farmer-chip-card ${plot.id === state.currentPlotId ? "active" : ""}`;
    chip.id = `farmer-chip-${plot.id}`;

    let badgeClass = "badge-healthy";
    let badgeLabel = "Healthy Control";
    if (plot.flooded_pct >= 50) {
      badgeClass = "badge-severe";
      badgeLabel = "Severe Flood (78%)";
    } else if (plot.flooded_pct > 10) {
      badgeClass = "badge-resilient";
      badgeLabel = "Resilient Plan (30%)";
    }

    chip.innerHTML = `
      <div class="farmer-chip-info">
        <h4><span>🌾</span> ${plot.farmer_name}</h4>
        <p>${plot.village} • ${plot.acreage} Acres</p>
      </div>
      <div>
        <span class="farmer-badge ${badgeClass}">${badgeLabel}</span>
      </div>
    `;

    chip.onclick = () => {
      selectPlot(plot.id, true);
    };
    container.appendChild(chip);
  });
}

async function selectPlot(plotId, speakOnSelect = true) {
  state.currentPlotId = plotId;

  // Highlight chip
  document.querySelectorAll(".farmer-chip-card").forEach(c => c.classList.remove("active"));
  const active = document.getElementById(`farmer-chip-${plotId}`);
  if (active) active.classList.add("active");

  // Fetch plot details in parallel
  try {
    const [healthRes, floodRes, planRes, claimRes, alertsRes, weatherRes, loansRes] = await Promise.all([
      fetch(`/api/plot/${plotId}/health`),
      fetch(`/api/plot/${plotId}/flood`),
      fetch(`/api/plan/${plotId}`),
      fetch(`/api/claim/${plotId}?lang=${state.currentLang}`),
      fetch(`/api/alerts/${plotId}?lang=${state.currentLang}`),
      fetch(`/api/weather/${plotId}`),
      fetch(`/api/loans/recommend/${plotId}`)
    ]);

    const health = await healthRes.json();
    const flood = await floodRes.json();
    const plan = await planRes.json();
    const claim = await claimRes.json();
    const alerts = await alertsRes.json();
    const weather = await weatherRes.json();
    const loans = await loansRes.json();

    state.currentPlotData = { health, flood, plan, claim, alerts, weather, loans };

    // Update views
    updateFarmerModeUI();
    updateWeatherSection(weather);
    updateChatbotWelcome();
    updateLoansPortal(loans);
    updateProtectTab(plan);
    updatePredictTab(health);
    updateProveTab(flood);
    updatePayTab(claim);
    updateInsurerTab();

    // Auto-play status in Farmer Mode
    if (speakOnSelect && state.currentMode === "farmer") {
      speakCurrentFarmerStatus();
    }
  } catch (e) {
    console.error("Error loading plot details:", e);
  }
}

// ----------------- MODE SWITCHING -----------------

function switchAppMode(mode) {
  state.currentMode = mode;
  const farmerView = document.getElementById("farmer-mode-view");
  const officerView = document.getElementById("officer-mode-view");
  const btnFarmer = document.getElementById("btn-mode-farmer");
  const btnOfficer = document.getElementById("btn-mode-officer");

  if (mode === "farmer") {
    farmerView.style.display = "flex";
    officerView.style.display = "none";
    btnFarmer.classList.add("active");
    btnOfficer.classList.remove("active");
  } else {
    farmerView.style.display = "none";
    officerView.style.display = "flex";
    btnFarmer.classList.remove("active");
    btnOfficer.classList.add("active");

    // Invalidate map size so Leaflet renders correctly after display switch
    setTimeout(() => {
      if (state.predictMap) state.predictMap.invalidateSize();
      if (state.proveMap) state.proveMap.invalidateSize();
    }, 150);
  }
}

function switchTab(tabId) {
  state.currentTab = tabId;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  const btn = document.getElementById(`tab-btn-${tabId}`);
  const pane = document.getElementById(`pane-${tabId}`);
  if (btn) btn.classList.add("active");
  if (pane) pane.classList.add("active");

  if (tabId === "predict" && state.predictMap) {
    setTimeout(() => state.predictMap.invalidateSize(), 100);
  }
  if (tabId === "prove" && state.proveMap) {
    setTimeout(() => state.proveMap.invalidateSize(), 100);
  }
}

// ----------------- FARMER MODE LOGIC -----------------

function updateFarmerModeUI() {
  if (!state.currentPlotData) return;
  const { health, alerts } = state.currentPlotData;

  const card = document.getElementById("traffic-card");
  const face = document.getElementById("traffic-face");
  const title = document.getElementById("traffic-status-title");
  const sub = document.getElementById("traffic-status-subtitle");

  card.className = "traffic-light-card";
  if (health.health_color === "green") {
    card.classList.add("border-green");
    face.innerText = "😊";
    title.innerText = getI18nText("ui.status_healthy", "Crop is Healthy & Thriving");
    title.style.color = "#15803d";
    sub.innerText = "Optimal growth observed from Sentinel-2 satellite canopy index.";
  } else if (health.health_color === "yellow") {
    card.classList.add("border-yellow");
    face.innerText = "😐";
    title.innerText = getI18nText("ui.status_warning", "Crop Stress Warning");
    title.style.color = "#d97706";
    sub.innerText = "Water deficit detected at week 9. Immediate irrigation advised.";
  } else {
    card.classList.add("border-red");
    face.innerText = "😟";
    title.innerText = getI18nText("ui.status_danger", "Severe Flood Damage Detected");
    title.style.color = "#dc2626";
    sub.innerText = "Radar satellite confirms 78% plot submergence. Insurance claim recommended.";
  }

  // Active Alert Card
  const alertCard = document.getElementById("farmer-alert-card");
  const alertIcon = document.getElementById("farmer-alert-icon");
  const alertTitle = document.getElementById("farmer-alert-title");
  const alertBody = document.getElementById("farmer-alert-body");

  const latestAlert = alerts.alerts[alerts.alerts.length - 1];
  if (latestAlert) {
    alertIcon.innerText = latestAlert.icon;
    alertTitle.innerText = latestAlert.title;
    alertBody.innerText = latestAlert.text;
  }
}

function speakCurrentFarmerStatus() {
  if (!state.currentPlotData) return;
  const { health, alerts } = state.currentPlotData;
  const latestAlert = alerts.alerts[alerts.alerts.length - 1];

  let spokenMsg = `${health.face_emoji} ${health.farmer_name}. `;
  if (latestAlert) {
    spokenMsg += latestAlert.text;
  } else {
    spokenMsg += getI18nText("alerts.all_clear", "Crop conditions are healthy.");
  }

  const btnListen = document.getElementById("btn-farmer-listen");
  const btnText = document.getElementById("btn-listen-text");
  if (btnText) btnText.innerText = getI18nText("ui.speaking", "Speaking...");

  speakText(spokenMsg, state.currentLang, () => {
    if (btnText) btnText.innerText = getI18nText("ui.listen", "Listen");
  });
}

function speakFarmerAlert() {
  if (!state.currentPlotData) return;
  const { alerts } = state.currentPlotData;
  const latestAlert = alerts.alerts[alerts.alerts.length - 1];
  if (latestAlert) {
    speakText(latestAlert.text, state.currentLang);
  }
}

async function triggerIntent(intentKey, questionText) {
  // Show dialogue bubble
  const bubble = document.getElementById("qa-bubble");
  const qBox = document.getElementById("qa-question-text");
  const aBox = document.getElementById("qa-answer-text");

  bubble.classList.add("active");
  qBox.innerText = questionText;
  aBox.innerText = "...";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plot_id: state.currentPlotId,
        language: state.currentLang,
        question_text: questionText
      })
    });
    const data = await res.json();
    aBox.innerText = data.answer;
    speakText(data.answer, state.currentLang);
  } catch (e) {
    // Client offline fallback from i18n
    const fallbackAnswer = state.i18n?.languages[state.currentLang]?.intents[intentKey]?.answers[state.currentPlotId]
      || "Status recorded by AgriShield.";
    aBox.innerText = fallbackAnswer;
    speakText(fallbackAnswer, state.currentLang);
  }
}

async function handleFarmerVoiceInput(spokenText) {
  const bubble = document.getElementById("qa-bubble");
  const qBox = document.getElementById("qa-question-text");
  const aBox = document.getElementById("qa-answer-text");

  bubble.classList.add("active");
  qBox.innerText = spokenText;
  aBox.innerText = "...";

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plot_id: state.currentPlotId,
        language: state.currentLang,
        question_text: spokenText
      })
    });
    const data = await res.json();
    aBox.innerText = data.answer;
    speakText(data.answer, state.currentLang);
  } catch (e) {
    aBox.innerText = "Error answering question.";
  }
}

function speakQaAnswer() {
  const text = document.getElementById("qa-answer-text")?.innerText;
  if (text) speakText(text, state.currentLang);
}

// ----------------- OFFICER MODE: TAB 1 PROTECT -----------------

function updateProtectTab(plan) {
  document.getElementById("protect-farmer-variety").innerText = plan.farmer_variety;
  
  // Progress bar
  const scorePct = plan.protection_score;
  document.getElementById("protect-score-pct").innerText = `${scorePct}%`;
  const fill = document.getElementById("protect-score-fill");
  fill.style.width = `${scorePct}%`;
  fill.style.backgroundColor = scorePct >= 70 ? "#16a34a" : (scorePct >= 40 ? "#f59e0b" : "#dc2626");

  // Checklist
  const taskList = document.getElementById("protect-task-list");
  taskList.innerHTML = "";
  plan.farmer_tasks.forEach((t, idx) => {
    const li = document.createElement("li");
    li.className = `task-item ${t.done ? "done" : ""}`;
    li.innerHTML = `
      <input type="checkbox" ${t.done ? "checked" : ""} onchange="toggleTaskDone(${idx})">
      <span><b>Wk ${t.week}:</b> ${t.task}</span>
    `;
    taskList.appendChild(li);
  });

  // Risk Calendar 16 Blocks
  const calendarBlocks = document.getElementById("risk-calendar-blocks");
  calendarBlocks.innerHTML = "";
  for (let w = 1; w <= 16; w++) {
    const box = document.createElement("div");
    box.className = "calendar-week-box";
    let icon = "🌱";
    let label = `W${w}`;

    if (w >= 5 && w <= 7) {
      box.classList.add("risk-blast");
      icon = "🐛";
    } else if (w >= 8 && w <= 10) {
      box.classList.add("risk-stress");
      icon = "💧";
    } else if (w >= 11 && w <= 13) {
      box.classList.add("risk-flood");
      icon = "🌧️";
    }

    box.innerHTML = `
      <span class="week-icon">${icon}</span>
      <span>${label}</span>
    `;
    calendarBlocks.appendChild(box);
  }

  // Active Risks
  const risksContainer = document.getElementById("protect-active-risks");
  risksContainer.innerHTML = "";
  plan.active_risks.forEach(r => {
    const div = document.createElement("div");
    div.style.cssText = "background:#fee2e2; border-left:4px solid #ef4444; padding:8px 12px; border-radius:6px; font-size:0.85rem;";
    div.innerHTML = `
      <b>[Wk ${r.triggered_week}] ${r.name} (${r.severity}):</b> ${r.condition}<br>
      <i>Action: ${r.action}</i>
    `;
    risksContainer.appendChild(div);
  });

  // Pre disaster protocol
  const preDisasterUl = document.getElementById("protect-predisaster-list");
  preDisasterUl.innerHTML = "";
  plan.pre_disaster_protocol.forEach(item => {
    const li = document.createElement("li");
    li.innerText = item;
    preDisasterUl.appendChild(li);
  });
}

function toggleTaskDone(taskIdx) {
  if (!state.currentPlotData) return;
  const tasks = state.currentPlotData.plan.farmer_tasks;
  tasks[taskIdx].done = !tasks[taskIdx].done;
  const doneCount = tasks.filter(t => t.done).length;
  const newScore = Math.round((doneCount / tasks.length) * 100);
  state.currentPlotData.plan.protection_score = newScore;
  
  document.getElementById("protect-score-pct").innerText = `${newScore}%`;
  const fill = document.getElementById("protect-score-fill");
  fill.style.width = `${newScore}%`;
  fill.style.backgroundColor = newScore >= 70 ? "#16a34a" : (newScore >= 40 ? "#f59e0b" : "#dc2626");
}

// ----------------- OFFICER MODE: TAB 2 PREDICT -----------------

function updatePredictTab(health) {
  const plot = state.plots.find(p => p.id === state.currentPlotId);
  if (!plot) return;

  // Initialize or update Leaflet Health Map
  const mapCenter = [plot.lat, plot.lon];
  if (!state.predictMap) {
    state.predictMap = L.map("map-predict").setView(mapCenter, 16);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors"
    }).addTo(state.predictMap);
  } else {
    state.predictMap.setView(mapCenter, 16);
  }

  // Draw plot polygon
  if (state.predictPolygon) {
    state.predictMap.removeLayer(state.predictPolygon);
  }

  const polygonColor = health.health_color === "green" ? "#16a34a" : (health.health_color === "yellow" ? "#f59e0b" : "#dc2626");
  
  // Create polygon box around center
  const coords = [
    [plot.lat - 0.0006, plot.lon - 0.0006],
    [plot.lat + 0.0006, plot.lon - 0.0006],
    [plot.lat + 0.0006, plot.lon + 0.0006],
    [plot.lat - 0.0006, plot.lon + 0.0006]
  ];

  state.predictPolygon = L.polygon(coords, {
    color: polygonColor,
    fillColor: polygonColor,
    fillOpacity: 0.45,
    weight: 3
  }).addTo(state.predictMap);

  state.predictPolygon.bindPopup(`
    <b>Farmer:</b> ${health.farmer_name}<br>
    <b>Status:</b> ${health.status_label}<br>
    <b>Baseline NDVI:</b> ${health.baseline_ndvi}<br>
    <b>Current NDVI:</b> ${health.latest_ndvi}
  `).openPopup();

  // Update badge
  const badge = document.getElementById("predict-health-badge");
  badge.innerText = health.status_label;
  badge.style.background = health.health_color === "green" ? "#dcfce7" : (health.health_color === "yellow" ? "#fef3c7" : "#fee2e2");
  badge.style.color = health.health_color === "green" ? "#15803d" : (health.health_color === "yellow" ? "#b45309" : "#dc2626");

  // Chart.js NDVI Timeline
  renderNdviChart(health);

  // Update SMS simulator
  updateSmsSimulator();
}

function renderNdviChart(health) {
  const ctx = document.getElementById("chart-ndvi")?.getContext("2d");
  if (!ctx) return;

  if (state.ndviChart) {
    state.ndviChart.destroy();
  }

  const weeks = health.weeks.map(w => `W${w}`);
  const baselineData = health.weeks.map(() => health.baseline_ndvi);
  const stressThresholdData = health.weeks.map(() => health.stress_threshold);

  state.ndviChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: weeks,
      datasets: [
        {
          label: "Plot NDVI",
          data: health.ndvi_timeline,
          borderColor: health.health_color === "red" ? "#dc2626" : "#16a34a",
          backgroundColor: "rgba(22, 163, 74, 0.1)",
          borderWidth: 3,
          pointRadius: 4,
          pointBackgroundColor: health.ndvi_timeline.map(val => val < health.stress_threshold ? "#dc2626" : "#16a34a"),
          tension: 0.2
        },
        {
          label: "Baseline (0.76)",
          data: baselineData,
          borderColor: "#2563eb",
          borderDash: [5, 5],
          borderWidth: 2,
          pointRadius: 0,
          fill: false
        },
        {
          label: "Stress Trigger (-15%)",
          data: stressThresholdData,
          borderColor: "#d97706",
          borderDash: [2, 2],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0.15,
          max: 0.95,
          title: { display: true, text: "NDVI Index" }
        },
        x: {
          title: { display: true, text: "Season Week" }
        }
      },
      plugins: {
        legend: { position: "top" }
      }
    }
  });
}

function updateSmsSimulator() {
  const alertText = state.currentPlotData?.alerts?.alerts[state.currentPlotData.alerts.alerts.length - 1]?.text
    || getI18nText("alerts.all_clear", "Crop healthy.");
  const smsDisplay = document.getElementById("sms-text-display");
  if (smsDisplay) smsDisplay.innerText = alertText;
}

function playIvrVoiceCall() {
  const smsText = document.getElementById("sms-text-display")?.innerText;
  if (smsText) {
    const ivrIntro = state.currentLang === "ta" ? "வணக்கம். அக்ரிஷீல்ட் குரல் சேவை: " : "AgriShield automated IVR voice bulletin: ";
    speakText(ivrIntro + smsText, state.currentLang);
  }
}

// ----------------- OFFICER MODE: TAB 3 PROVE -----------------

function updateProveTab(flood) {
  const plot = state.plots.find(p => p.id === state.currentPlotId);
  if (!plot) return;

  // Initialize or update Prove Map
  const mapCenter = [plot.lat, plot.lon];
  if (!state.proveMap) {
    state.proveMap = L.map("map-prove").setView(mapCenter, 17);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors"
    }).addTo(state.proveMap);
  } else {
    state.proveMap.setView(mapCenter, 17);
  }

  // Remove existing layers
  if (state.proveGridLayer) {
    state.proveMap.removeLayer(state.proveGridLayer);
  }
  if (state.proveCloudLayer) {
    state.proveMap.removeLayer(state.proveCloudLayer);
  }

  // Create 20x20 cell rectangles
  state.proveGridLayer = L.layerGroup();
  const cellSize = 0.00004;

  flood.grid.forEach(row => {
    row.forEach(cell => {
      const bounds = [
        [cell.lat - cellSize/2, cell.lon - cellSize/2],
        [cell.lat + cellSize/2, cell.lon + cellSize/2]
      ];
      const isFlooded = cell.is_flooded;
      const cellRect = L.rectangle(bounds, {
        color: isFlooded ? "#0284c7" : "#16a34a",
        fillColor: isFlooded ? "#0284c7" : "#22c55e",
        fillOpacity: isFlooded ? 0.75 : 0.35,
        weight: 0.5
      });
      cellRect.bindTooltip(`SAR: ${cell.after_db} dB (${cell.delta_db} dB)<br>${isFlooded ? "🌊 FLOODED" : "🌱 VEGETATED"}`);
      state.proveGridLayer.addLayer(cellRect);
    });
  });

  state.proveGridLayer.addTo(state.proveMap);

  // Update big numbers
  document.getElementById("prove-flooded-pct").innerText = `${flood.flooded_pct}%`;
  document.getElementById("prove-sar-before").innerText = `${flood.sar_before_db} dB`;
  document.getElementById("prove-sar-after").innerText = `${flood.sar_after_db} dB`;
}

function toggleRadarOpticalView() {
  state.isRadarView = !state.isRadarView;
  const btn = document.getElementById("btn-toggle-view");
  const warn = document.getElementById("optical-warning-box");

  if (!state.isRadarView) {
    // Optical View: show cloud cover
    btn.innerHTML = "🛰️ Switch to Radar (SAR) View";
    btn.style.background = "#0284c7";
    warn.style.display = "block";

    if (state.proveMap && !state.proveCloudLayer) {
      const plot = state.plots.find(p => p.id === state.currentPlotId);
      const bounds = [
        [plot.lat - 0.001, plot.lon - 0.001],
        [plot.lat + 0.001, plot.lon + 0.001]
      ];
      state.proveCloudLayer = L.rectangle(bounds, {
        color: "#ffffff",
        fillColor: "#ffffff",
        fillOpacity: 0.88,
        weight: 1
      }).addTo(state.proveMap);
      state.proveCloudLayer.bindTooltip("🌧️ 92% Dense Monsoon Cloud Obscuration - Optical Blinded");
    }
  } else {
    // Radar View
    btn.innerHTML = "☁️ Switch to Optical View";
    btn.style.background = "#16a34a";
    warn.style.display = "none";

    if (state.proveCloudLayer && state.proveMap) {
      state.proveMap.removeLayer(state.proveCloudLayer);
      state.proveCloudLayer = null;
    }
  }
}

// ----------------- OFFICER MODE: TAB 4 PAY -----------------

function updatePayTab(claim) {
  const banner = document.getElementById("pay-decision-banner");
  const decText = document.getElementById("pay-decision-text");
  const decSub = document.getElementById("pay-decision-sub");

  decText.innerText = claim.decision;
  decSub.innerText = `Loss Score: ${claim.loss_score} | Confidence: ${Math.round(claim.confidence * 100)}% | Payout: ${claim.estimated_payout_pct}%`;
  banner.style.backgroundColor = claim.decision_color;

  // Formula values
  document.getElementById("pay-calc-ndvi").innerText = `${claim.ndvi_drop_fraction} × 0.5 = ${(claim.ndvi_drop_fraction * 0.5).toFixed(3)}`;
  document.getElementById("pay-calc-flood").innerText = `${claim.flooded_fraction} × 0.4 = ${(claim.flooded_fraction * 0.4).toFixed(3)}`;
  document.getElementById("pay-calc-weather").innerText = `${claim.weather_severity} × 0.1 = ${(claim.weather_severity * 0.1).toFixed(3)}`;
  document.getElementById("pay-calc-total").innerText = `${claim.loss_score}`;
  document.getElementById("pay-confidence-score").innerText = `${Math.round(claim.confidence * 100)}%`;

  // Reasoning
  document.getElementById("pay-reasoning-text").innerText = claim.reasoning_localized || claim.reasoning;
}

function downloadClaimPdf() {
  window.open(`/api/claim/${state.currentPlotId}/pdf`, "_blank");
}

// ----------------- OFFICER MODE: TAB 5 INSURER DASHBOARD -----------------

async function updateInsurerTab() {
  try {
    const [insurerRes, fraudRes] = await Promise.all([
      fetch("/api/insurer"),
      fetch(`/api/fraud/${state.currentPlotId}`)
    ]);

    const insurerData = await insurerRes.json();
    const fraudData = await fraudRes.json();

    // Render table
    const tbody = document.getElementById("insurer-table-body");
    tbody.innerHTML = "";

    insurerData.ranking.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><b>#${idx + 1}</b></td>
        <td><b>${r.farmer_name}</b></td>
        <td>${r.variety}</td>
        <td><span style="font-weight:700; color:${r.protection_score >= 70 ? '#16a34a' : '#dc2626'}">${r.protection_score}%</span></td>
        <td>${r.flooded_pct}%</td>
        <td><b>${r.loss_score}</b></td>
        <td>${Math.round(r.confidence * 100)}%</td>
        <td><span class="farmer-badge" style="background:${r.decision_color}; color:white;">${r.decision}</span></td>
        <td>${r.decision_code === 'APPROVE' ? '⚡ Instant' : '🔍 Inspection'}</td>
      `;
      tbody.appendChild(tr);
    });

    // Update fraud card
    const fraudBadge = document.getElementById("fraud-status-badge");
    const fraudText = document.getElementById("fraud-details-text");

    if (fraudData.is_fraud_anomaly) {
      fraudBadge.innerText = "FLAGGED FOR AUDIT";
      fraudBadge.style.background = "#fee2e2";
      fraudBadge.style.color = "#dc2626";
    } else {
      fraudBadge.innerText = "REGIONAL CORROBORATED";
      fraudBadge.style.background = "#dcfce7";
      fraudBadge.style.color = "#15803d";
    }

    fraudText.innerHTML = `
      <b>Farmer ${fraudData.farmer_name}:</b> ${fraudData.details}<br>
      Average flood in 10km regional corridor: <b>${fraudData.regional_average_flood_pct}%</b> across ${fraudData.regional_plots_compared} audited delta plots.
    `;
  } catch (e) {
    console.error("Insurer tab error:", e);
  }
}

// ----------------- WEATHER & SATELLITE RESOURCES -----------------

function updateWeatherSection(weather) {
  if (!weather) return;
  const temp = document.getElementById("weather-temp");
  const humidity = document.getElementById("weather-humidity");
  const rain = document.getElementById("weather-rain");
  const wind = document.getElementById("weather-wind");
  const advisory = document.getElementById("weather-agro-advisory");
  
  if (temp) temp.innerText = `${weather.current_weather.temperature_c}°C`;
  if (humidity) humidity.innerText = `${weather.current_weather.humidity_pct}%`;
  if (rain) rain.innerText = `${weather.current_weather.rainfall_recorded_mm} mm`;
  if (wind) wind.innerText = `${weather.current_weather.wind_speed_kmh} km/h`;
  if (advisory) advisory.innerText = weather.agro_advisory;

  // Satellite meters
  const ndviVal = document.getElementById("sat-ndvi-val");
  const ndviPill = document.getElementById("sat-ndvi-pill");
  const sarDb = document.getElementById("sat-sar-db");
  const sarPill = document.getElementById("sat-sar-pill");

  if (ndviVal) ndviVal.innerText = weather.satellite_resources.optical_sentinel2.ndvi_canopy_reading;
  if (sarDb) sarDb.innerText = `${weather.satellite_resources.radar_sentinel1_sar.backscatter_db} dB`;

  if (weather.satellite_resources.radar_sentinel1_sar.backscatter_db < -15) {
    if (sarPill) {
      sarPill.className = "sat-status-pill pill-blocked";
      sarPill.innerText = "🌊 Submerged";
    }
  } else {
    if (sarPill) {
      sarPill.className = "sat-status-pill pill-active";
      sarPill.innerText = "🌱 Vegetated";
    }
  }

  if (weather.satellite_resources.optical_sentinel2.ndvi_canopy_reading < 0.6) {
    if (ndviPill) {
      ndviPill.className = "sat-status-pill pill-blocked";
      ndviPill.innerText = "⚠️ Stress / Loss";
    }
  } else {
    if (ndviPill) {
      ndviPill.className = "sat-status-pill pill-active";
      ndviPill.innerText = "✅ Healthy";
    }
  }
}

function speakWeatherAdvisory() {
  const text = document.getElementById("weather-agro-advisory")?.innerText;
  if (text) speakText(text, state.currentLang);
}

// ----------------- AI CHATBOT (SAHAYAK) -----------------

function updateChatbotWelcome() {
  const welcomeEl = document.getElementById("chat-welcome-msg");
  if (!welcomeEl) return;
  const farmerName = state.currentPlotData?.health?.farmer_name || "Farmer";
  
  const greetings = {
    ta: `வணக்கம் ${farmerName}! நான் உங்கள் அக்ரிஷீல்ட் AI உதவியாளர். உங்கள் பயிர் நலம், வானிலை, மற்றும் பயிர் கடன்கள் பற்றி என்னிடம் கேட்கலாம்.`,
    hi: `नमस्ते ${farmerName} जी! मैं आपका एग्रीशील्ड AI सहायक हूँ। आप मुझसे फसल स्वास्थ्य, मौसम, और कृषि ऋण के बारे में पूछ सकते हैं।`,
    te: `నమస్కారం ${farmerName} గారు! నేను మీ అగ్రిషీల్డ్ AI సహాయకుడిని. పంట ఆరోగ్యం, వాతావరణం, మరియు రుణాల గురించి అడగండి.`,
    kn: `ನಮಸ್ಕಾರ ${farmerName} ಅವರೇ! ನಾನು ನಿಮ್ಮ ಅಗ್ರಿಶೀಲ್ಡ್ AI ಸಹಾಯಕ. ಬೆಳೆ ಆರೋಗ್ಯ, ಹವಾಮಾನ ಮತ್ತು ಸಾಲಗಳ ಬಗ್ಗೆ ಕೇಳಿ.`,
    ml: `നമസ്കാരം ${farmerName}! ഞാൻ നിങ്ങളുടെ അഗ്രിഷീൽഡ് AI സഹായിയാണ്. വിള ആരോഗ്യം, കാലാവസ്ഥ, വായ്പകൾ എന്നിവയെക്കുറിച്ച് ചോദിക്കാം.`,
    en: `Hello Farmer ${farmerName}! I am your AgriShield AI Assistant. Ask me to analyze crop health, weather forecasts, or which loan/relief applies to you.`
  };
  welcomeEl.innerText = greetings[state.currentLang] || greetings["en"];
}

async function askChatbotPrompt(type) {
  const prompts = {
    weather_forecast: {
      ta: "இன்றைய வானிலை மற்றும் மழை முன்னறிவிப்பு என்ன?",
      hi: "आज का मौसम और बारिश का पूर्वानुमान क्या है?",
      te: "నేటి వాతావరణం మరియు వర్షపాత సూచన ఏమిటి?",
      kn: "ಇಂದಿನ ಹವಾಮಾನ ಮತ್ತು ಮಳೆ ಮುನ್ಸೂಚನೆ ಏನು?",
      ml: "ഇന്നത്തെ കാലാവസ്ഥയും മഴ പ്രവചനവും എന്താണ്?",
      en: "What is today's weather forecast and rainfall status?"
    },
    crop_health: {
      ta: "என் பயிர் நலம் எப்படி உள்ளது? செயற்கைக்கோள் என்ன சொல்கிறது?",
      hi: "मेरी फसल कैसी है? उपग्रह डेटा क्या दिखाता है?",
      te: "నా పంట ఆరోగ్యం ఎలా ఉంది? శాటిలైట్ డేటా ఏం చెబుతోంది?",
      kn: "ನನ್ನ ಬೆಳೆ ಆರೋಗ್ಯ ಹೇಗಿದೆ? ಉಪಗ್ರಹ ಮಾಹಿತಿ ಏನು ಹೇಳುತ್ತದೆ?",
      ml: "എന്റെ വിള ആരോഗ്യം എങ്ങനെയുണ്ട്? ഉപഗ്രഹം എന്ത് പറയുന്നു?",
      en: "How is my crop health according to satellite imagery?"
    },
    loan_options: {
      ta: "என் பயிர் பாதிப்பிற்கு என்ன கடன் அல்லது நிவாரணம் கிடைக்கும்?",
      hi: "मेरी फसल नुकसान के लिए कौन सा ऋण या मुआवजा मिलेगा?",
      te: "నా పంట నష్టానికి ఏ రుణం లేదా పరిహారం వర్తిస్తుంది?",
      kn: "ನನ್ನ ಬೆಳೆ ಹಾನಿಗೆ ಯಾವ ಸಾಲ ಅಥವಾ ಪರಿಹಾರ ಸಿಗುತ್ತದೆ?",
      ml: "എന്റെ വിള നാശത്തിന് എന്ത് വായ്പയോ നഷ്ടപരിഹാരമോ ലഭിക്കും?",
      en: "What loan or disaster relief applies to my crop damage?"
    },
    loan_docs: {
      ta: "நிவாரணம் அல்லது கடன் பெற என்ன ஆவணங்கள் தேவை?",
      hi: "ऋण या राहत पाने के लिए कौन से दस्तावेज चाहिए?",
      te: "రుణం లేదా సహాయం పొందడానికి ఏ పత్రాలు కావాలి?",
      kn: "ಸಾಲ ಅಥವಾ ಪರಿಹಾರ ಪಡೆಯಲು ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
      ml: "വായ്പയോ ആശ്വാസമോ ലഭിക്കാൻ എന്തെല്ലാം രേഖകൾ വേണം?",
      en: "What documents are required to apply for loan or relief?"
    },
    first_step: {
      ta: "பாதிப்பிற்குப் பிறகு நான் எடுக்க வேண்டிய முதல் நடவடிக்கை என்ன?",
      hi: "फसल नुकसान के बाद मुझे सबसे पहला कदम क्या उठाना चाहिए?",
      te: "పంట నష్టం తర్వాత నేను తీసుకోవలసిన మొదటి చర్య ఏమిటి?",
      kn: "ಬೆಳೆ ಹಾನಿಯ ನಂತರ ನಾನು ತೆಗೆದುಕೊಳ್ಳಬೇಕಾದ ಮೊದಲ ಹೆಜ್ಜೆ ಏನು?",
      ml: "വിള നാശത്തിന് ശേഷം ഞാൻ ആദ്യം ചെയ്യേണ്ടത് എന്താണ്?",
      en: "What is my immediate first step after crop damage?"
    }
  };

  const text = prompts[type]?.[state.currentLang] || prompts[type]?.["en"] || "What should I do?";
  const inputEl = document.getElementById("chat-input");
  if (inputEl) inputEl.value = text;
  await sendChatMessage();
}

async function sendChatMessage() {
  const inputEl = document.getElementById("chat-input");
  const qText = inputEl?.value?.trim();
  if (!qText) return;

  // Add user bubble
  appendChatBubble("user", qText);
  inputEl.value = "";

  // Maintain conversation history
  if (!state.chatHistory) state.chatHistory = [];

  // Add loading bot bubble
  const loadingId = "bot-loading-" + Date.now();
  appendChatBubble("bot", "...", loadingId);

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plot_id: state.currentPlotId,
        language: state.currentLang,
        question_text: qText,
        history: state.chatHistory.slice(-6)
      })
    });
    const data = await res.json();
    const answer = data.answer || "Status verified.";
    const sourceLabel = data.source ? `✦ ${data.source}` : "✦ AgriShield AI";
    
    // Track history
    state.chatHistory.push({ role: "user", content: qText });
    state.chatHistory.push({ role: "assistant", content: answer });

    // Update loading bubble
    const loadingBubble = document.getElementById(loadingId);
    if (loadingBubble) {
      loadingBubble.innerHTML = `
        <div style="font-size: 0.75rem; color: #166534; font-weight: 700; margin-bottom: 4px;">${sourceLabel}</div>
        <div style="white-space: pre-line;">${answer}</div>
        <div class="chat-bubble-actions">
          <button class="chat-listen-btn" onclick="speakText('${answer.replace(/'/g, "\\'")}')">🔊 Listen</button>
        </div>
      `;
    }
    // Speak automatically in farmer mode
    speakText(answer, state.currentLang);
  } catch (e) {
    const loadingBubble = document.getElementById(loadingId);
    if (loadingBubble) {
      loadingBubble.innerText = "Error connecting to AI Assistant: " + e.message;
    }
  }
}

function handleChatEnter(e) {
  if (e.key === "Enter") {
    sendChatMessage();
  }
}

function appendChatBubble(role, text, id = null) {
  const container = document.getElementById("chatbot-messages");
  if (!container) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  if (id) bubble.id = id;

  if (role === "bot" && id !== null && text === "...") {
    bubble.innerHTML = `<span>⏳ Thinking...</span>`;
  } else if (role === "bot") {
    bubble.innerHTML = `
      <div>${text}</div>
      <div class="chat-bubble-actions">
        <button class="chat-listen-btn" onclick="speakText('${text.replace(/'/g, "\\'")}')">🔊 Listen</button>
      </div>
    `;
  } else {
    bubble.innerText = text;
  }

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

let isChatMicActive = false;
function toggleChatMic() {
  if (!state.recognition) {
    alert("Speech recognition is not supported in this browser.");
    return;
  }
  const micBtn = document.getElementById("btn-chat-mic");
  if (isChatMicActive) {
    state.recognition.stop();
    isChatMicActive = false;
    if (micBtn) micBtn.classList.remove("listening");
  } else {
    const langObj = LANGUAGES_CONFIG.find(l => l.code === state.currentLang);
    state.recognition.lang = langObj ? langObj.bcp : "ta-IN";
    try {
      state.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const inputEl = document.getElementById("chat-input");
        if (inputEl) inputEl.value = transcript;
        sendChatMessage();
      };
      state.recognition.onend = () => {
        isChatMicActive = false;
        if (micBtn) micBtn.classList.remove("listening");
      };
      state.recognition.start();
      isChatMicActive = true;
      if (micBtn) micBtn.classList.add("listening");
    } catch (e) {
      console.warn("Chat mic error:", e);
    }
  }
}

// ----------------- LOANS & RELIEF PORTAL -----------------

function updateLoansPortal(loans) {
  if (!loans) return;

  const schemeName = document.getElementById("loan-rec-scheme-name");
  const reliefType = document.getElementById("loan-rec-relief-type");
  const amount = document.getElementById("loan-rec-amount");
  const damageTag = document.getElementById("loan-rec-damage-tag");
  const whereText = document.getElementById("loan-where-apply-text");

  if (schemeName) schemeName.innerText = loans.recommended_scheme.name;
  if (reliefType) reliefType.innerText = `${loans.recommended_scheme.relief_type} | Secondary: ${loans.recommended_scheme.secondary_scheme}`;
  if (amount) amount.innerText = `₹${loans.recommended_scheme.estimated_eligible_amount_inr.toLocaleString('en-IN')}`;

  if (damageTag) {
    if (loans.verified_damage_type === "flood_submergence") {
      damageTag.className = "farmer-badge badge-severe";
      damageTag.innerText = `🌊 Flood Submergence (${loans.flooded_pct}%)`;
    } else if (loans.verified_damage_type === "water_deficit_drought") {
      damageTag.className = "farmer-badge badge-warning";
      damageTag.innerText = "☀️ Water Stress / Canal Lag";
    } else {
      damageTag.className = "farmer-badge badge-healthy";
      damageTag.innerText = "🌱 Normal / Expansion Loan";
    }
  }

  if (whereText) {
    whereText.innerHTML = `
      <b>Designated Center:</b> ${loans.where_to_apply}<br>
      <span style="font-size:0.8rem; color:#64748b;">Nearest CSC Center & Taluk Agriculture Office pre-notified with satellite proof.</span>
    `;
  }
}

function speakLoanRecommendation() {
  const loans = state.currentPlotData?.loans;
  if (!loans) return;
  const msg = `${loans.farmer_name}, for your plot condition, the recommended scheme is ${loans.recommended_scheme.name}. Eligible amount is ₹${loans.recommended_scheme.estimated_eligible_amount_inr}. First step: ${loans.first_step}`;
  speakText(msg, state.currentLang);
}

function openLoanModal() {
  const loans = state.currentPlotData?.loans;
  if (!loans) return;

  document.getElementById("loan-app-farmer-name").value = loans.farmer_name;
  document.getElementById("loan-app-village").value = loans.village;
  document.getElementById("loan-app-scheme-name").value = loans.recommended_scheme.name;
  document.getElementById("loan-app-damage-type").value = `${loans.verified_damage_type.replace('_', ' ').toUpperCase()} (${loans.flooded_pct}% Loss)`;
  document.getElementById("loan-app-amount").value = loans.recommended_scheme.estimated_eligible_amount_inr;

  // Reset modal state to form
  document.getElementById("modal-form-content").style.display = "flex";
  document.getElementById("modal-footer-actions").style.display = "flex";
  document.getElementById("modal-receipt-content").style.display = "none";
  document.getElementById("modal-footer-receipt").style.display = "none";

  const modal = document.getElementById("loan-application-modal");
  if (modal) modal.classList.add("open");
}

function closeLoanModal() {
  const modal = document.getElementById("loan-application-modal");
  if (modal) modal.classList.remove("open");
}

async function submitLoanForm() {
  const loans = state.currentPlotData?.loans;
  if (!loans) return;

  const reqData = {
    plot_id: state.currentPlotId,
    farmer_name: document.getElementById("loan-app-farmer-name").value,
    scheme_id: loans.recommended_scheme.id,
    scheme_name: document.getElementById("loan-app-scheme-name").value,
    requested_amount: parseFloat(document.getElementById("loan-app-amount").value) || loans.recommended_scheme.estimated_eligible_amount_inr,
    village: document.getElementById("loan-app-village").value,
    aadhaar_last4: document.getElementById("loan-app-aadhaar").value || "8821",
    survey_number: document.getElementById("loan-app-survey").value || "142/3B",
    bank_name: document.getElementById("loan-app-bank").value
  };

  try {
    const res = await fetch("/api/loans/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reqData)
    });
    const receipt = await res.json();

    // Show receipt in modal
    document.getElementById("modal-form-content").style.display = "none";
    document.getElementById("modal-footer-actions").style.display = "none";
    document.getElementById("modal-receipt-content").style.display = "block";
    document.getElementById("modal-footer-receipt").style.display = "flex";

    document.getElementById("receipt-ref-id").innerText = receipt.application_ref_id;
    document.getElementById("receipt-farmer-name").innerText = receipt.farmer_name;
    document.getElementById("receipt-scheme-name").innerText = receipt.scheme_name;
    document.getElementById("receipt-amount").innerText = `₹${receipt.requested_amount_inr.toLocaleString('en-IN')}`;
    document.getElementById("receipt-instructions").innerText = receipt.next_step_instructions;

    // Speak confirmation
    speakText(`Application registered successfully! Reference ID is ${receipt.application_ref_id}. Please visit PACCS within 5 days.`, state.currentLang);
  } catch (e) {
    alert("Application error: " + e.message);
  }
}
