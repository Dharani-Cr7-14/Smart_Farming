import { useEffect, useMemo, useRef, useState } from "react";

const navItems = [
  ["/", "Dashboard", "fa-chart-line"],
  ["/seed_dashboard", "Crop & Seeds", "fa-seedling"],
  ["/disease_dashboard", "Plant Disease", "fa-leaf"],
  ["/chatbot", "AI Assistant", "fa-robot"],
  ["/history", "Prediction History", "fa-clock-rotate-left"],
];

const emptyCropForm = { pH: "", N: "", P: "", K: "", Temp: "", Rainfall: "", Humidity: "", Soil_Type: "Loamy", Region: "South" };
const API_BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

function api(path, options = {}) {
  return fetch(`${API_BASE_URL}${path}`, { credentials: "include", ...options, headers: { Accept: "application/json", ...(options.headers || {}) } });
}

function formatDate(value) {
  return value ? value.slice(0, 16).replace("T", " ") : "-";
}

function Icon({ name }) { return <i className={`fa-solid ${name}`} aria-hidden="true" />; }

function LanguageSelect({ lang, onChange }) {
  return <div className="select-lang-container"><select value={lang} onChange={(event) => onChange(event.target.value)} aria-label="Language">
    <option value="en">English</option><option value="ta">தமிழ் (Tamil)</option><option value="hi">हिन्दी (Hindi)</option>
  </select></div>;
}

function AuthScreen({ lang, setLang, initialMessage }) {
  const [mode, setMode] = useState(initialMessage?.register ? "register" : "login");
  const [form, setForm] = useState({ username: "", email: "", password: "", region: "South" });
  const [message, setMessage] = useState(initialMessage?.text || "");
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault(); setError(""); setMessage("");
    const data = new FormData(); Object.entries({ ...form, lang }).forEach(([key, value]) => data.append(key, value));
    const response = await api(`/auth/${mode}`, { method: "POST", body: data });
    const payload = await response.json().catch(() => ({}));
    if (response.ok && payload.ok) { window.location.assign("/"); }
    else if (payload.success) { setMessage(payload.success); setMode("login"); }
    else { setError(payload.error || "Unable to complete this request."); }
  };
  return <div className="auth-wrapper"><div className="auth-card">
    <div className="auth-header"><Icon name="fa-wheat-awn" /><h1>Smart Farming</h1><p>Decision Support System for better cultivation.</p></div>
    {error && <div className="alert-popup error"><Icon name="fa-circle-exclamation" /><span>{error}</span></div>}
    {message && <div className="alert-popup success"><Icon name="fa-circle-check" /><span>{message}</span></div>}
    <div className="tab-container" style={{ justifyContent: "center", borderBottom: "none", marginBottom: 30 }}>
      <button className={`tab-btn ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>Sign In</button>
      <button className={`tab-btn ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>Register</button>
    </div>
    <form onSubmit={submit}>
      <div className="form-group"><label><Icon name={mode === "login" ? "fa-user" : "fa-user-plus"} /> {mode === "login" ? "Username" : "Enter Username"}</label><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="Enter username" required /></div>
      <div className="form-group"><label><Icon name="fa-envelope" /> Email Address</label><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="farmer@example.com" required /></div>
      <div className="form-group"><label><Icon name="fa-lock" /> Password</label><input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={mode === "login" ? "Enter password" : "Choose password"} required /></div>
      {mode === "register" && <div className="form-group"><label><Icon name="fa-map-location-dot" /> Farming Region</label><select value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })}>{["North", "South", "East", "West", "Central"].map((item) => <option key={item}>{item}</option>)}</select></div>}
      <button type="submit" className="premium-btn primary" style={{ width: "100%", marginTop: 10 }}><Icon name={mode === "login" ? "fa-right-to-bracket" : "fa-user-check" } /> {mode === "login" ? "Sign In" : "Register Account"}</button>
    </form>
    <div style={{ marginTop: 30, textAlign: "center" }}><LanguageSelect lang={lang} onChange={setLang} /></div>
  </div></div>;
}

function Shell({ user, lang, setLang, page, children }) {
  const [open, setOpen] = useState(false);
  const navigate = (path) => { setOpen(false); window.history.pushState({}, "", `${path}?lang=${lang}`); window.dispatchEvent(new PopStateEvent("popstate")); };
  const logout = async () => { await api("/auth/logout"); window.location.assign("/auth/login"); };
  return <div className="app-container"><aside className={`sidebar ${open ? "mobile-open" : ""}`}>
    <div className="sidebar-header"><Icon name="fa-wheat-awn" /><h1>Smart Farming</h1></div>
    <ul className="sidebar-menu">{navItems.map(([path, label, icon]) => <li key={path} className={`sidebar-menu-item ${page === path ? "active" : ""}`}><a href={`${path}?lang=${lang}`} onClick={(e) => { e.preventDefault(); navigate(path); }}><Icon name={icon} /><span>{label}</span></a></li>)}</ul>
    <div className="sidebar-footer"><div className="user-profile-badge"><div className="user-avatar">{user.username[0].toUpperCase()}</div><div className="user-info"><div className="user-name">{user.username}</div><button className="user-logout-btn button-reset" onClick={logout}><Icon name="fa-right-from-bracket" /> Logout</button></div></div></div>
  </aside><div className={`sidebar-overlay ${open ? "visible" : ""}`} onClick={() => setOpen(false)} />
    <main className="main-workspace"><header className="top-nav"><div className="page-title"><button className="premium-btn secondary" style={{ display: "none", padding: "8px 12px", marginRight: 12 }} onClick={() => setOpen(true)} aria-label="Open navigation"><Icon name="fa-bars" /></button><h2>{navItems.find(([path]) => path === page)?.[1] || "Dashboard"}</h2></div><div className="nav-actions"><LanguageSelect lang={lang} onChange={setLang} /></div></header><div className="content-body react-page">{children}</div></main>
  </div>;
}

const WEATHER_DESCRIPTIONS = { 0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers", 81: "Rain showers", 82: "Heavy showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm" };

function weatherDescription(code) { return WEATHER_DESCRIPTIONS[code] || "Current conditions"; }

function Dashboard({ user, data, navigate, weather, weatherError, refreshWeather }) {
  const [tab, setTab] = useState("crop");
  const cropCount = data.crop_logs?.length || 0;
  const diseaseCount = data.disease_logs?.length || 0;
  const temperature = weather ? `${weather.temperature.toFixed(1)} °C` : "--";
  const humidity = weather ? `${weather.humidity.toFixed(0)} %` : "--";
  const rainfall = weather ? `${weather.rainfall_30d.toFixed(1)} mm` : "--";
  const weatherNote = weather ? weatherDescription(weather.weather_code) : weatherError || "Requesting your location...";

  return <div className="dashboard-page">
    <section className="dashboard-hero">
      <div className="hero-copy"><span className="hero-kicker"><Icon name="fa-sparkles" /> FARM COMMAND CENTER</span><h2>Good to see you, <span>{user.username}</span>.</h2><p>Your farming workspace is ready with recommendations, diagnostics, and practical guidance for the <b>{user.region || "South"}</b> region.</p><div className="hero-status"><span><i className="status-dot" /> Systems operational</span><span><Icon name="fa-location-dot" /> {user.region || "South"} region</span></div></div>
      <div className="hero-weather"><Icon name="fa-cloud-sun-rain" /><strong>{weather ? `${weather.temperature.toFixed(1)}°` : "--"}</strong><span>{weatherNote}</span>{weatherError && <button className="activity-link" onClick={refreshWeather}>Try again</button>}</div>
    </section>

    <section className="dashboard-stat-grid" aria-label="Farm overview">
      <StatCard icon="fa-temperature-three-quarters" label="Temperature" value={temperature} note={weather ? weatherDescription(weather.weather_code) : weatherNote} tone="green" />
      <StatCard icon="fa-droplet" label="Humidity" value={humidity} note={weather ? "Live reading for your location" : weatherNote} tone="cyan" />
      <StatCard icon="fa-cloud-rain" label="Rainfall (30 days)" value={rainfall} note={weather ? "Total for the last 30 days" : weatherNote} tone="yellow" />
      <StatCard icon="fa-chart-line" label="Saved insights" value={cropCount + diseaseCount} note={`${cropCount} crop · ${diseaseCount} disease`} tone="pink" />
    </section>

    <section className="dashboard-section-heading"><div><span className="section-kicker">TOOLS FOR TODAY</span><h3>Make the next decision count</h3></div><span className="section-rule" /></section>
    <section className="dashboard-action-grid"><Shortcut title="Crop & Seeds" icon="fa-seedling" copy="Match your soil and climate to suitable crops and regional seed varieties." action="Open recommendations" onClick={() => navigate("/seed_dashboard")} tone="green" /><Shortcut title="Disease Classifier" icon="fa-leaf" copy="Upload a leaf photo and get a fast pathogen classification with confidence." action="Start a scan" onClick={() => navigate("/disease_dashboard")} tone="cyan" /></section>

    <section className="premium-card activity-card"><div className="activity-heading"><div><span className="section-kicker">YOUR TRAIL</span><h3><Icon name="fa-clock-rotate-left" /> Recent activity</h3></div><button className="activity-link" onClick={() => navigate("/history")}>View full history <Icon name="fa-arrow-right" /></button></div><div className="tab-container"><button className={`tab-btn ${tab === "crop" ? "active" : ""}`} onClick={() => setTab("crop")}>Crop searches <span>{cropCount}</span></button><button className={`tab-btn ${tab === "disease" ? "active" : ""}`} onClick={() => setTab("disease")}>Disease scans <span>{diseaseCount}</span></button></div>{tab === "crop" ? <CropTable logs={data.crop_logs} compact /> : <DiseaseTable logs={data.disease_logs} compact />}</section>
  </div>;
}

function StatCard({ icon, label, value, note, tone }) { return <div className={`dashboard-stat tone-${tone}`}><div className="stat-icon"><Icon name={icon} /></div><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>; }

function Shortcut({ title, icon, copy, action, onClick, tone }) { return <article className={`dashboard-action tone-${tone}`}><div className="action-icon"><Icon name={icon} /></div><div className="action-copy"><span className="action-label">{tone === "green" ? "RECOMMENDATION ENGINE" : "VISUAL DIAGNOSTICS"}</span><h3>{title}</h3><p>{copy}</p><button className="action-button" onClick={onClick}>{action} <Icon name="fa-arrow-up-right-from-square" /></button></div></article>; }

function SoilReportUpload({ onExtracted }) {
  const [file, setFile] = useState(null); const [busy, setBusy] = useState(false); const [message, setMessage] = useState(""); const [error, setError] = useState("");
  const submit = async (event) => { event.preventDefault(); if (!file) return; setBusy(true); setError(""); setMessage(""); const data = new FormData(); data.append("file", file); try { const response = await api("/api/soil-report", { method: "POST", body: data }); const payload = await response.json().catch(() => ({})); if (!response.ok || !payload.ok) { setError(payload.error || "Could not read the soil report."); return; } onExtracted(payload.report.values); setMessage(`Extracted ${Object.keys(payload.report.values).length} values. Please review them below.`); } catch { setError("Could not upload the soil report."); } finally { setBusy(false); } };
  return <div className="soil-report-upload"><div className="form-group"><label htmlFor="soil-report"><Icon name="fa-file-pdf" /> Import soil report (PDF)</label><input id="soil-report" type="file" accept=".pdf,application/pdf" onChange={(event) => { setFile(event.target.files[0] || null); setError(""); setMessage(""); }} /></div><button className="premium-btn secondary" type="button" onClick={submit} disabled={!file || busy}><Icon name="fa-file-import" /> {busy ? "Reading report..." : "Extract Soil Values"}</button>{message && <p className="field-success">{message}</p>}{error && <p className="field-error">{error}</p>}</div>;
}

function CropPage({ weather }) {
  const [form, setForm] = useState(() => ({ ...emptyCropForm, ...(weather ? { Temp: String(weather.temperature), Rainfall: String(weather.rainfall_30d), Humidity: String(weather.humidity) } : {}) })); const [result, setResult] = useState(null); const [error, setError] = useState(""); const set = (key, value) => setForm({ ...form, [key]: value }); const applyReport = (values) => setForm((current) => ({ ...current, ...Object.fromEntries(Object.entries(values).filter(([key]) => ["pH", "N", "P", "K"].includes(key)).map(([key, value]) => [key, String(value)])) }));
  useEffect(() => { if (weather) setForm((current) => ({ ...current, Temp: current.Temp || String(weather.temperature), Rainfall: current.Rainfall || String(weather.rainfall_30d), Humidity: current.Humidity || String(weather.humidity) })); }, [weather]);
  const submit = async (event) => { event.preventDefault(); setError(""); const data = new FormData(); Object.entries(form).forEach(([key, value]) => data.append(key, value)); const response = await api("/seed_dashboard", { method: "POST", body: data }); const payload = await response.json().catch(() => ({})); if (response.ok && payload.ok) setResult(payload.prediction); else setError(payload.error || "Prediction failed."); };
  return <div className="dashboard-grid seed-dashboard-grid"><div className="premium-card seed-form-card"><div className="seed-form-header"><div className="seed-section-icon"><Icon name="fa-file-invoice" /></div><div><h3>Enter Farm Metrics</h3><p>Temperature, rainfall, and humidity are auto-filled from your location when available.</p></div></div><SoilReportUpload onExtracted={applyReport} /><form onSubmit={submit}><Field label="Soil pH" name="pH" value={form.pH} set={set} step="0.01" placeholder="e.g. 6.5" /><div className="seed-nutrient-grid"><Field label="Nitrogen (N)" name="N" value={form.N} set={set} step="0.01" placeholder="N" /><Field label="Phosphorus (P)" name="P" value={form.P} set={set} step="0.01" placeholder="P" /><Field label="Potassium (K)" name="K" value={form.K} set={set} step="0.01" placeholder="K" /></div><Field label="Temperature (°C)" name="Temp" value={form.Temp} set={set} step="0.1" placeholder="e.g. 28.5" /><Field label="Rainfall (last 30 days, mm)" name="Rainfall" value={form.Rainfall} set={set} step="0.1" placeholder="e.g. 150" /><Field label="Humidity (%)" name="Humidity" value={form.Humidity} set={set} step="0.1" placeholder="e.g. 70" /><div className="seed-select-grid"><SelectField label="Soil Type" name="Soil_Type" value={form.Soil_Type} set={set} options={["Loamy", "Sandy", "Clay", "Red", "Black"]} /><SelectField label="Region" name="Region" value={form.Region} set={set} options={["North", "South", "East", "West", "Central"]} /></div>{error && <p className="field-error">{error}</p>}<button className="premium-btn primary" style={{ width: "100%", marginTop: 10 }}><Icon name="fa-calculator" /> Get Recommendation</button></form></div><div className="seed-outcome">{result ? <div className="premium-card seed-result-card"><h3 className="seed-result-heading"><Icon name="fa-circle-check" /> Recommendation Result</h3><div className="seed-crop-name">Predicted Crop: <b>{result.pred_crop}</b></div><h4>Top Recommended Seed Varieties</h4><div className="seed-list">{result.top_seeds.map(([seed, probability]) => <div className="seed-list-row" key={seed}><b>{seed}</b><b>{probability}</b></div>)}</div></div> : <EmptySeedState />}</div></div>;
}

function Field({ label, name, value, set, step, placeholder }) { return <div className="form-group field-wide"><label htmlFor={name}>{label}</label><input id={name} type="number" step={step} value={value} placeholder={placeholder} onChange={(e) => set(name, e.target.value)} required /></div>; }
function SelectField({ label, name, value, set, options }) { return <div className="form-group"><label htmlFor={name}>{label}</label><select id={name} value={value} onChange={(e) => set(name, e.target.value)} required>{options.map((option) => <option key={option}>{option}</option>)}</select></div>; }
function EmptySeedState() { return <div className="premium-card seed-empty-state"><div className="seed-empty-icon"><Icon name="fa-seedling" /></div><span className="seed-empty-kicker">PERSONALIZED GUIDANCE</span><h3>Ready for a recommendation?</h3><p>Enter your farm metrics to find seed varieties suited to your crop and region.</p><div className="seed-empty-points"><span><Icon name="fa-check" /> Crop suitability</span><span><Icon name="fa-check" /> Regional matches</span></div></div>; }

const DISEASE_ADVICE = {
  "bacterial spot": {
    symptoms: "Small dark water-soaked spots that may enlarge, merge, and cause yellowing or leaf drop.",
    nextSteps: ["Remove badly affected leaves and dispose of them away from the field.", "Avoid overhead irrigation and keep foliage dry.", "Use disease-free seed or planting material and ask a local expert about an approved treatment."]
  },
  "early blight": {
    symptoms: "Brown circular leaf spots, often with concentric rings, followed by yellowing and early leaf loss.",
    nextSteps: ["Remove infected leaves and clear crop debris.", "Improve airflow by maintaining suitable plant spacing.", "Rotate crops and use an approved fungicide only according to its label."]
  },
  "late blight": {
    symptoms: "Irregular dark brown or black lesions that spread quickly, sometimes with a pale or grey edge.",
    nextSteps: ["Isolate affected plants and remove infected tissue promptly.", "Avoid working in wet foliage and reduce leaf wetness.", "Contact an agricultural officer quickly because this disease can spread rapidly."]
  },
  "powdery mildew": {
    symptoms: "White powder-like growth on leaf surfaces, with curling, yellowing, or reduced plant growth.",
    nextSteps: ["Remove heavily infected leaves and improve sunlight and air circulation.", "Avoid excess nitrogen and overhead watering.", "Use a locally approved mildew treatment following the product label."]
  },
  "common rust": {
    symptoms: "Small orange, brown, or rust-colored pustules on leaves that can reduce green leaf area.",
    nextSteps: ["Remove severely affected leaves and crop residue.", "Improve airflow and avoid excessive leaf wetness.", "Ask a local expert whether an approved rust fungicide is needed."]
  },
  "leaf blight": {
    symptoms: "Brown or tan patches that expand across leaves and may cause premature drying.",
    nextSteps: ["Remove infected foliage and destroy crop debris.", "Avoid overhead irrigation and improve field drainage.", "Use resistant varieties and an approved treatment when recommended locally."]
  },
  "septoria leaf spot": {
    symptoms: "Many small circular spots with dark margins and pale centres, often starting on older leaves.",
    nextSteps: ["Remove lower infected leaves and clear fallen debris.", "Water at the soil line and improve plant spacing.", "Rotate crops and follow local fungicide guidance if symptoms continue."]
  },
  "spider mites": {
    symptoms: "Fine webbing, pale stippling, bronzed leaves, and possible leaf drying.",
    nextSteps: ["Inspect the undersides of leaves and separate heavily affected plants.", "Wash foliage with a firm water spray when appropriate.", "Protect beneficial insects and seek local advice before applying a miticide."]
  },
  healthy: {
    symptoms: "No visible disease symptoms were identified in the uploaded leaf.",
    nextSteps: ["Continue regular monitoring of new leaves.", "Maintain balanced irrigation, nutrition, and good airflow.", "Re-scan or consult an agricultural expert if spots, wilting, or discoloration appear."]
  },
  unknown: {
    symptoms: "The detected disease does not have a detailed guide in the current catalog. Watch for spreading spots, discoloration, curling, wilting, or unusual growth.",
    nextSteps: ["Separate severely affected plants where practical.", "Remove fallen or heavily infected leaves and avoid spreading plant material.", "Take a clear close-up image and contact a local agricultural expert for confirmation and treatment advice."]
  }
};

function diseaseAdviceFor(label) {
  const normalized = label.toLowerCase().replace(/_/g, " ");
  const match = Object.keys(DISEASE_ADVICE).find((key) => normalized.includes(key));
  return DISEASE_ADVICE[match || (normalized.includes("healthy") ? "healthy" : "unknown")];
}

function DiseaseAdvice({ disease }) {
  const advice = diseaseAdviceFor(disease);
  return <div className="premium-card disease-advice-card"><h3><Icon name="fa-notes-medical" /> Symptoms and next steps</h3><p><strong>What to look for:</strong> {advice.symptoms}</p><h4>Suggested next steps</h4><ol>{advice.nextSteps.map((step) => <li key={step}>{step}</li>)}</ol><small>Diagnosis is an AI-supported screening result. Confirm treatment choices with a local agricultural expert.</small></div>;
}

function DiseasePage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const choose = (picked) => { if (!picked) return; setFile(picked); setPreview(URL.createObjectURL(picked)); };
  const submit = async (event) => {
    event.preventDefault();
    if (!file) return;
    setError("");
    const data = new FormData();
    data.append("file", file);
    const response = await api("/disease_dashboard", { method: "POST", body: data });
    const payload = await response.json().catch(() => ({}));
    if (response.ok && payload.ok) setResult(payload.prediction);
    else setError(payload.error || "Image processing failed.");
  };
  return <div className="dashboard-grid disease-layout"><div className="premium-card disease-upload-card"><div className="disease-section-heading"><div className="disease-section-icon"><Icon name="fa-camera" /></div><div><h3>Diagnostic Scan</h3><p>Upload a clear leaf photo for analysis.</p></div></div><form onSubmit={submit}><label className={`image-upload-wrapper ${file ? "upload-dragging" : ""}`} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]); }}><Icon name="fa-cloud-arrow-up" /><strong>Drop your leaf photo here</strong><span>or <b>browse files</b></span><small>JPG, PNG, or WEBP · Max 10 MB</small><input className="dropzone-input" type="file" accept="image/*" onChange={(e) => choose(e.target.files[0])} required={!file} /></label>{preview && <div className="image-preview-panel"><img src={preview} alt="Selected leaf preview" /></div>}{file && <div className="file-details"><span><Icon name="fa-image" /><b>{file.name}</b></span><span>{(file.size / 1024 / 1024).toFixed(1)} MB</span></div>}{file && <button type="button" className="clear-file-btn" onClick={() => { setFile(null); setPreview(""); }}><Icon name="fa-xmark" /> Remove selected image</button>}{error && <p className="field-error">{error}</p>}<button className="premium-btn primary" style={{ width: "100%", marginTop: 20 }}><Icon name="fa-flask" /> Scan Leaf Image</button></form></div><div>{result ? <><div className="premium-card disease-result-card"><h3 className="disease-result-heading"><Icon name="fa-circle-check" /> Diagnostic Result</h3><div className="disease-result-summary"><img src={result.image_path} alt="Analyzed leaf" /><div><div className="disease-name">Pathogen class: <b>{result.pred_class}</b></div><div>Confidence score: <strong className="good">{Number(result.confidence).toFixed(2)}%</strong></div><div className="confidence-meter"><span style={{ width: `${result.confidence}%` }} /></div></div></div></div><DiseaseAdvice disease={result.pred_class} /></> : <div className="premium-card disease-placeholder"><Icon name="fa-file-image" />Select and upload a leaf photo to diagnose potential crop diseases.</div>}<Guidance /></div></div>;
}
function Guidance() { return <div className="premium-card disease-guidance-card"><div className="disease-guidance-header"><div className="disease-section-icon"><Icon name="fa-leaf" /></div><div><h3>Scan Guidance</h3><p>Small details make the diagnosis easier to interpret.</p></div></div><div className="disease-guidance-grid">{[["Use natural light", "Avoid harsh shadows, flash glare, and very dark images."], ["Center one leaf", "Keep the affected area visible and the leaf in focus."], ["Review the confidence", "Use the score as guidance and confirm with an expert."]].map(([title, copy], index) => <div className="disease-guidance-item" key={title}><span className="disease-guidance-number">0{index + 1}</span><div><strong>{title}</strong><p>{copy}</p></div></div>)}</div></div>; }

function ChatPage({ lang, logs = [] }) {
  const savedMessages = logs.slice().reverse().map((log) => ({ role: log.role === "user" ? "user" : "bot", text: log.message }));
  const [messages, setMessages] = useState(savedMessages.length ? savedMessages : [{ role: "bot", text: "Welcome to the Smart Farming AI Assistant! Ask me about crop cultivation, seed treatment, pest controls, fertilizers, or farming best practices." }]);
  const [value, setValue] = useState("");
  const [pending, setPending] = useState(false);
  const submit = async (event) => {
    event.preventDefault();
    const message = value.trim();
    if (!message || pending) return;
    setValue("");
    setMessages((current) => [...current, { role: "user", text: message }, { role: "bot", text: "...", pending: true }]);
    setPending(true);
    const data = new FormData();
    data.append("user_message", message);
    data.append("lang", lang);
    try {
      const response = await api("/chatbot_message", { method: "POST", body: data });
      const payload = await response.json();
      setMessages((current) => [...current.slice(0, -1), { role: "bot", text: payload.reply || "No response was generated." }]);
    } catch {
      setMessages((current) => [...current.slice(0, -1), { role: "bot", text: "Error: Could not connect to AI agricultural advisor." }]);
    } finally {
      setPending(false);
    }
  };
  return <div className="chat-container"><div className="chat-messages">{messages.map((message, index) => <div className={`chat-bubble ${message.role} ${message.pending ? "pending" : ""}`} key={`${index}-${message.text}`}>{message.text}</div>)}</div><form className="chat-input-bar" onSubmit={submit}><input value={value} onChange={(e) => setValue(e.target.value)} placeholder="Type your farming query here..." required autoComplete="off" /><button className="premium-btn primary" disabled={pending}><Icon name="fa-paper-plane" /> Send</button></form></div>;
}

function HistoryPage({ data }) { const [tab, setTab] = useState("crop"); return <div className="premium-card history-card"><p className="history-intro">Below are the historical prediction and chatbot logs saved for your farming profile.</p><div className="tab-container"><button className={`tab-btn ${tab === "crop" ? "active" : ""}`} onClick={() => setTab("crop")}>Crop & Seed Queries</button><button className={`tab-btn ${tab === "disease" ? "active" : ""}`} onClick={() => setTab("disease")}>Plant Disease Scans</button><button className={`tab-btn ${tab === "chat" ? "active" : ""}`} onClick={() => setTab("chat")}>Chatbot Advisor History</button></div>{tab === "crop" ? <CropTable logs={data.crop_logs} /> : tab === "disease" ? <DiseaseTable logs={data.disease_logs} /> : <ChatTable logs={data.chat_logs} />}</div>; }
function EmptyTable({ icon, text }) { return <div className="table-empty"><Icon name={icon} />{text}</div>; }
function CropTable({ logs = [], compact }) { if (!logs.length) return <EmptyTable icon="fa-seedling" text="No crop recommendation entries found." />; return <div className="table-responsive"><table className="premium-table"><thead><tr><th>Date</th><th>Region & Soil</th><th>pH</th><th>NPK</th><th>Predicted Crop</th>{!compact && <th>Top Seeds</th>}</tr></thead><tbody>{logs.map((log, index) => <tr key={index}><td>{formatDate(log.created_at)}</td><td>{compact ? log.soil_type : `${log.region} / ${log.soil_type}`}</td><td>{log.pH}</td><td>{log.N} - {log.P} - {log.K}</td><td className="good"><b>{String(log.predicted_crop).toUpperCase()}</b></td>{!compact && <td>{(log.top_seeds || []).map(([seed, probability]) => <div key={seed}>{seed} ({Number(probability).toFixed(1)})</div>)}</td>}</tr>)}</tbody></table></div>; }
function DiseaseTable({ logs = [], compact }) { if (!logs.length) return <EmptyTable icon="fa-leaf" text="No leaf disease scans found." />; return <div className="table-responsive"><table className="premium-table"><thead><tr><th>Date</th><th>Image</th><th>Predicted Pathogen</th><th>Confidence</th></tr></thead><tbody>{logs.map((log, index) => <tr key={index}><td>{formatDate(log.created_at)}</td><td>{log.image_name}</td><td className="warning"><b>{log.predicted_class}</b></td><td>{Number(log.confidence).toFixed(2)}%</td></tr>)}</tbody></table></div>; }
function ChatTable({ logs = [] }) { if (!logs.length) return <EmptyTable icon="fa-comments" text="No chatbot advisor history found." />; return <div className="table-responsive"><table className="premium-table"><thead><tr><th>Date</th><th>Language</th><th>Role</th><th>Message</th></tr></thead><tbody>{logs.map((log, index) => <tr key={index}><td>{formatDate(log.created_at)}</td><td>{String(log.language).toUpperCase()}</td><td>{log.role}</td><td>{log.message}</td></tr>)}</tbody></table></div>; }

function App() {
  const [user, setUser] = useState(undefined); const [page, setPage] = useState(window.location.pathname); const [lang, setLangState] = useState(new URLSearchParams(window.location.search).get("lang") || localStorage.getItem("selectedLang") || "en"); const [data, setData] = useState({ crop_logs: [], disease_logs: [], chat_logs: [] }); const [weather, setWeather] = useState(null); const [weatherError, setWeatherError] = useState(""); const [authMessage, setAuthMessage] = useState(null);
  const setLang = (value) => { localStorage.setItem("selectedLang", value); setLangState(value); const url = new URL(window.location.href); url.searchParams.set("lang", value); window.history.replaceState({}, "", url); };
  const load = async () => { const response = await api("/api/session"); const payload = await response.json(); setUser(payload.user || null); if (payload.user) { const history = await api("/api/history"); if (history.ok) setData(await history.json()); } };
  const refreshWeather = () => { if (!navigator.geolocation) { setWeatherError("Location is not supported by this browser."); return; } setWeatherError(""); navigator.geolocation.getCurrentPosition(async ({ coords }) => { const response = await api(`/api/weather?latitude=${encodeURIComponent(coords.latitude)}&longitude=${encodeURIComponent(coords.longitude)}`); const payload = await response.json().catch(() => ({})); if (response.ok) setWeather(payload); else setWeatherError(payload.error || "Unable to load local weather."); }, () => setWeatherError("Allow location access to load local weather."), { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }); };
  useEffect(() => { const onPop = () => setPage(window.location.pathname); window.addEventListener("popstate", onPop); load(); return () => window.removeEventListener("popstate", onPop); }, [page]);
  useEffect(() => { if (user) refreshWeather(); }, [user]);
  if (user === undefined) return <div className="react-loading">Loading your farm workspace...</div>;
  if (!user) return <AuthScreen lang={lang} setLang={setLang} initialMessage={authMessage} />;
  const navigate = (path) => { window.history.pushState({}, "", `${path}?lang=${lang}`); setPage(path); };
  const content = page === "/seed_dashboard" ? <CropPage weather={weather} /> : page === "/disease_dashboard" ? <DiseasePage /> : page === "/chatbot" ? <ChatPage lang={lang} logs={data.chat_logs} /> : page === "/history" ? <HistoryPage data={data} /> : <Dashboard user={user} data={data} navigate={navigate} weather={weather} weatherError={weatherError} refreshWeather={refreshWeather} />;
  return <Shell user={user} lang={lang} setLang={setLang} page={page}>{content}</Shell>;
}

export default App;