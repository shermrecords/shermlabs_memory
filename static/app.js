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

function setupMicrophoneRecorder() {
  const startButton = document.getElementById("startRecordingButton");
  const stopButton = document.getElementById("stopRecordingButton");
  const discardButton = document.getElementById("discardRecordingButton");
  const audioInput = document.getElementById("audioFileInput");
  const preview = document.getElementById("recordingPreview");
  const status = document.getElementById("recordingStatus");
  const timer = document.getElementById("recordingTimer");
  const dot = document.getElementById("recordingDot");
  const help = document.getElementById("recorderHelp");

  if (!startButton || !audioInput) return;

  if (!navigator.mediaDevices?.getUserMedia || !("MediaRecorder" in window)) {
    startButton.disabled = true;
    status.textContent = "Unavailable";
    help.textContent = "This browser does not support microphone recording. You can still upload an audio file.";
    return;
  }

  let recorder = null;
  let stream = null;
  let chunks = [];
  let objectUrl = null;
  let timerId = null;
  let startedAt = 0;

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
    const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${minutes}:${remainder}`;
  };

  const updateTimer = () => {
    timer.textContent = formatTime((Date.now() - startedAt) / 1000);
  };

  const stopTracks = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
  };

  const chooseMimeType = () => {
    const choices = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg;codecs=opus"
    ];
    return choices.find(type => MediaRecorder.isTypeSupported(type)) || "";
  };

  const extensionForMime = (mimeType) => {
    if (mimeType.includes("mp4")) return "m4a";
    if (mimeType.includes("ogg")) return "ogg";
    return "webm";
  };

  const resetRecording = () => {
    clearInterval(timerId);
    timerId = null;
    stopTracks();
    recorder = null;
    chunks = [];
    timer.textContent = "00:00";
    status.textContent = "Ready";
    dot.classList.remove("active");
    startButton.disabled = false;
    stopButton.disabled = true;
    discardButton.hidden = true;
    preview.hidden = true;
    preview.removeAttribute("src");
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null;
    audioInput.value = "";
  };

  startButton.addEventListener("click", async () => {
    try {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = null;
      preview.hidden = true;
      preview.removeAttribute("src");
      audioInput.value = "";
      chunks = [];

      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const mimeType = chooseMimeType();
      recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recorder.addEventListener("dataavailable", event => {
        if (event.data && event.data.size > 0) chunks.push(event.data);
      });

      recorder.addEventListener("stop", () => {
        clearInterval(timerId);
        timerId = null;
        stopTracks();

        const finalMimeType = recorder.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunks, { type: finalMimeType });
        const extension = extensionForMime(finalMimeType);
        const stamp = new Date().toISOString().replace(/[:.]/g, "-");
        const file = new File([blob], `microphone_recording_${stamp}.${extension}`, {
          type: finalMimeType,
          lastModified: Date.now()
        });

        const transfer = new DataTransfer();
        transfer.items.add(file);
        audioInput.files = transfer.files;

        objectUrl = URL.createObjectURL(blob);
        preview.src = objectUrl;
        preview.hidden = false;
        status.textContent = "Recording ready";
        dot.classList.remove("active");
        startButton.disabled = false;
        startButton.textContent = "Record Again";
        stopButton.disabled = true;
        discardButton.hidden = false;
        help.textContent = "Your recording is attached below. Preview it, then click Create Entry.";
      });

      recorder.start(250);
      startedAt = Date.now();
      updateTimer();
      timerId = setInterval(updateTimer, 250);
      status.textContent = "Recording";
      dot.classList.add("active");
      startButton.disabled = true;
      stopButton.disabled = false;
      discardButton.hidden = true;
      help.textContent = "Speak normally. Click Stop when you are finished.";
    } catch (error) {
      stopTracks();
      status.textContent = "Microphone blocked";
      startButton.disabled = false;
      stopButton.disabled = true;
      help.textContent = error?.name === "NotAllowedError"
        ? "Microphone permission was denied. Allow microphone access in your browser settings and try again."
        : `Could not start recording: ${error?.message || "Unknown error"}`;
    }
  });

  stopButton.addEventListener("click", () => {
    if (recorder && recorder.state !== "inactive") recorder.stop();
  });

  discardButton.addEventListener("click", () => {
    resetRecording();
    startButton.textContent = "Start Recording";
    help.textContent = "Microphone access requires HTTPS on the live site or localhost during development.";
  });

  audioInput.addEventListener("change", () => {
    if (audioInput.files.length && !audioInput.files[0].name.startsWith("microphone_recording_")) {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = null;
      preview.hidden = true;
      discardButton.hidden = true;
      status.textContent = "File selected";
      startButton.textContent = "Start Recording";
    }
  });

  window.addEventListener("beforeunload", stopTracks);
}

document.addEventListener("DOMContentLoaded", setupMicrophoneRecorder);
