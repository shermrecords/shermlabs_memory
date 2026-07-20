let availableVoices = [];

function loadVoices() {
  if (!("speechSynthesis" in window)) return;

  availableVoices = window.speechSynthesis.getVoices();

  const voiceSelect = document.getElementById("speechVoice");
  if (!voiceSelect) return;

  voiceSelect.innerHTML = "";

  availableVoices.forEach((voice, index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = `${voice.name} (${voice.lang})`;
    voiceSelect.appendChild(option);
  });

  const preferred = availableVoices.findIndex(
    v =>
      v.name.includes("Jenny") ||
      v.name.includes("Aria") ||
      v.name.includes("Zira") ||
      v.name.includes("Natural")
  );

  if (preferred >= 0) {
    voiceSelect.value = preferred;
  }
}

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

function getWorkingCopyTextarea() {
  return document.getElementById("workingCopy");
}

function getWorkingCopyText() {
  const textarea = getWorkingCopyTextarea();
  return textarea ? textarea.value : "";
}

function getSelectedWorkingCopyText() {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return "";

  return textarea.value
    .substring(textarea.selectionStart, textarea.selectionEnd)
    .trim();
}

function copySelectionToNote() {
  const selected = getSelectedWorkingCopyText();

  if (!selected) {
    alert("Highlight text in the working copy first.");
    return;
  }

  const noteBody = document.getElementById("noteBody");

  if (noteBody) {
    noteBody.value = selected;
  }
}

function cleanupWhitespace(text) {
  return text
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function removeParentheses() {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return;

  if (!confirm("Remove all (...) text from working copy?")) {
    return;
  }

  textarea.value = cleanupWhitespace(
    textarea.value.replace(/\([^)]*\)/g, "")
  );
}

function removeSquareBrackets() {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return;

  if (!confirm("Remove all [...] text from working copy?")) {
    return;
  }

  textarea.value = cleanupWhitespace(
    textarea.value.replace(/\[[^\]]*\]/g, "")
  );
}

function cleanForListening() {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return;

  if (!confirm("Clean transcript for listening?")) {
    return;
  }

  let text = textarea.value;

  text = text.replace(/\([^)]*\)/g, "");
  text = text.replace(/\[[^\]]*\]/g, "");
  text = text.replace(/\{[^}]*\}/g, "");

  text = text.replace(/\b[A-Z][A-Za-z]+ et al\.,?\s*\d{4}\b/g, "");
  text = text.replace(/\b[A-Z][A-Za-z]+,\s*\d{4}\b/g, "");

  textarea.value = cleanupWhitespace(text);
}

function speakText(text) {
  if (!("speechSynthesis" in window)) {
    alert("Text-to-speech is not supported in this browser.");
    return;
  }

  if (!text.trim()) {
    alert("No text to read.");
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const speedSelect = document.getElementById("speechRate");

  utterance.rate = speedSelect ? parseFloat(speedSelect.value) : 0.8;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  const voiceSelect = document.getElementById("speechVoice");

  if (voiceSelect && availableVoices[voiceSelect.value]) {
    utterance.voice = availableVoices[voiceSelect.value];
  }

  window.speechSynthesis.speak(utterance);
}

function speakWorkingCopy() {
  speakText(getWorkingCopyText());
}

function speakSelection() {
  const selected = getSelectedWorkingCopyText();

  if (!selected) {
    alert("Highlight text in the working copy first.");
    return;
  }

  speakText(selected);
}

function speakFromCursor() {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return;

  const cursorPosition = textarea.selectionStart;
  const textFromCursor = textarea.value.substring(cursorPosition).trim();

  if (!textFromCursor) {
    alert("No text after cursor to read.");
    return;
  }

  speakText(textFromCursor);
}

function pauseSpeech() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.pause();
  }
}

function resumeSpeech() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.resume();
  }
}

function stopSpeech() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

async function lookupSynonyms() {
  const selected = getSelectedWorkingCopyText();

  if (!selected) {
    alert("Highlight one word first.");
    return;
  }

  const word = selected.trim().split(/\s+/)[0];
  const box = document.getElementById("synonymBox");

  if (!box) return;

  box.style.display = "block";
  box.innerHTML = `<p class="muted">Looking up synonyms for <strong>${word}</strong>...</p>`;

  try {
    const response = await fetch(`https://api.datamuse.com/words?rel_syn=${encodeURIComponent(word)}&max=12`);
    const data = await response.json();

    if (!data.length) {
      box.innerHTML = `<p>No synonyms found for <strong>${word}</strong>.</p>`;
      return;
    }

    box.innerHTML = `
      <strong>Synonyms for "${word}"</strong>
      <div class="synonym-list">
        ${data.map(item => `
          <button type="button" onclick="replaceSelection('${escapeForAttribute(item.word)}')">
            ${item.word}
          </button>
        `).join("")}
      </div>
    `;
  } catch (error) {
    box.innerHTML = `<p>Could not load synonyms.</p>`;
  }
}

function escapeForAttribute(text) {
  return text.replace(/'/g, "\\'");
}

function replaceSelection(replacement) {
  const textarea = getWorkingCopyTextarea();

  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  if (start === end) {
    alert("Highlight the word you want to replace.");
    return;
  }

  textarea.value =
    textarea.value.substring(0, start) +
    replacement +
    textarea.value.substring(end);

  textarea.focus();
  textarea.selectionStart = start;
  textarea.selectionEnd = start + replacement.length;
}

function showLoadingOverlay(message) {
  let overlay = document.getElementById("loadingOverlay");

  if (!overlay) {
    overlay = document.createElement("div");

    overlay.id = "loadingOverlay";
    overlay.className = "loading-overlay";

    overlay.innerHTML = `
      <div class="spinner"></div>
      <p id="loadingOverlayMessage">Working...</p>
    `;

    document.body.appendChild(overlay);
  }

  const msg = document.getElementById("loadingOverlayMessage");

  if (msg) {
    msg.textContent = message || "Working...";
  }

  overlay.classList.add("active");
}

function attachUploadLoadingOverlay() {
  const uploadForm = document.querySelector(
    "form[data-loading='upload']"
  );

  if (!uploadForm) return;

  uploadForm.addEventListener("submit", function () {
    showLoadingOverlay("Uploading and transcribing audio...");
  });
}

document.addEventListener("DOMContentLoaded", function() {
  attachUploadLoadingOverlay();
  loadVoices();
});
