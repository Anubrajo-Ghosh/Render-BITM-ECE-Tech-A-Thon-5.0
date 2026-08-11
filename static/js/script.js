const dropzone = document.getElementById("dropzone");
const dropzoneEmpty = document.getElementById("dropzone-empty");
const fileInput = document.getElementById("file-input");
const previewImg = document.getElementById("preview-img");
const scanLine = document.getElementById("scan-line");
const scanBtn = document.getElementById("scan-btn");
const scanStatus = document.getElementById("scan-status");

const resultEmpty = document.getElementById("result-empty");
const resultBody = document.getElementById("result-body");
const severityBadge = document.getElementById("severity-badge");
const resultLabel = document.getElementById("result-label");
const confidenceFill = document.getElementById("confidence-fill");
const confidenceNum = document.getElementById("confidence-num");
const lowConfWarning = document.getElementById("low-conf-warning");
const top3El = document.getElementById("top3");
const remedyText = document.getElementById("remedy-text");
const downloadBtn = document.getElementById("download-btn");
const langToggle = document.getElementById("lang-toggle");

const logTable = document.getElementById("log-table");
const logEmpty = document.getElementById("log-empty");
const clearHistoryBtn = document.getElementById("clear-history-btn");

let selectedFile = null;
let lastResult = null;
let currentLang = "en";

// ---------------- Upload handling ----------------
dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  if (!file.type.match(/image\/(jpeg|png|jpg)/)) {
    scanStatus.textContent = "Unsupported file — use a JPG or PNG.";
    return;
  }
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.style.display = "block";
    dropzoneEmpty.style.display = "none";
  };
  reader.readAsDataURL(file);
  scanBtn.disabled = false;
  scanStatus.textContent = "Specimen loaded. Ready to scan.";
}

// ---------------- Run diagnosis ----------------
scanBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  scanBtn.disabled = true;
  scanLine.classList.add("active");
  scanStatus.textContent = "Analyzing tissue pattern…";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/api/predict", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      scanStatus.textContent = data.error || "Something went wrong.";
      scanBtn.disabled = false;
      scanLine.classList.remove("active");
      return;
    }

    lastResult = data;
    renderResult(data);
    scanStatus.textContent = "Scan complete.";
    loadHistory();
  } catch (err) {
    scanStatus.textContent = "Network error — is the server running?";
  } finally {
    scanBtn.disabled = false;
    scanLine.classList.remove("active");
  }
});

function renderResult(data) {
  resultEmpty.style.display = "none";
  resultBody.style.display = "block";

  severityBadge.textContent = data.severity.level;
  severityBadge.className = "severity-badge " + data.severity.code;

  resultLabel.textContent = data.label;

  confidenceFill.style.width = data.confidence + "%";
  confidenceNum.textContent = data.confidence + "%";

  lowConfWarning.style.display = data.low_confidence ? "block" : "none";

  top3El.innerHTML = "";
  data.top3.forEach((item) => {
    const row = document.createElement("div");
    row.className = "top3-row";
    row.innerHTML = `
      <span class="top3-name">${item.label}</span>
      <div class="top3-track"><div class="top3-fill" style="width:${item.confidence}%"></div></div>
      <span class="top3-val">${item.confidence}%</span>
    `;
    top3El.appendChild(row);
  });

  remedyText.textContent = data.remedy[currentLang];
}

// ---------------- Language toggle ----------------
langToggle.addEventListener("click", (e) => {
  const btn = e.target.closest(".lang-btn");
  if (!btn) return;
  currentLang = btn.dataset.lang;
  [...langToggle.children].forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  if (lastResult) remedyText.textContent = lastResult.remedy[currentLang];
});

// ---------------- Download report ----------------
downloadBtn.addEventListener("click", () => {
  if (!lastResult) return;
  const r = lastResult;
  const report = `========================================
CROP DISEASE DIAGNOSTIC REPORT
========================================
Date/Time: ${r.timestamp}
File Analyzed: ${r.filename}

DIAGNOSIS RESULTS:
- Identified Condition: ${r.label}
- Confidence Score: ${r.confidence}%
- Severity Status: ${r.severity.level}

RECOMMENDED REMEDY:
${r.remedy.en}
========================================
Generated by AgroScan — BITM ECE Tech-A-Thon
`;
  const blob = new Blob([report], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Report_${r.label.replace(/\s+/g, "_")}.txt`;
  a.click();
  URL.revokeObjectURL(url);
});

// ---------------- History log ----------------
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const rows = await res.json();
    logTable.innerHTML = "";
    if (!rows.length) {
      logTable.appendChild(logEmpty);
      return;
    }
    rows.forEach((r) => {
      const row = document.createElement("div");
      row.className = "log-row";
      row.innerHTML = `
        <span class="log-file">${r.filename}</span>
        <span class="log-result">${r.result}</span>
        <span class="log-conf">${r.confidence}</span>
        <span class="log-time">${r.timestamp}</span>
      `;
      logTable.appendChild(row);
    });
  } catch (err) {
    // silent — history is non-critical
  }
}

clearHistoryBtn.addEventListener("click", async () => {
  await fetch("/api/history/clear", { method: "POST" });
  loadHistory();
});

loadHistory();
