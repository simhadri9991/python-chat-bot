// Initialize external icons
lucide.createIcons();

// --- UI CONTROLS ---
function toggleSettings() {
    const drawer = document.getElementById('settingsDrawer');
    if (drawer.classList.contains('translate-x-full')) {
        drawer.classList.remove('translate-x-full');
    } else {
        drawer.classList.add('translate-x-full');
    }
}

// --- LOCAL STORAGE AND STATE ---
window.addEventListener('DOMContentLoaded', () => {
    const savedKey = localStorage.getItem('gemini_api_key') || '';
    document.getElementById('apiKeyInput').value = savedKey;
    updateBadgeState(savedKey);
});

function saveApiKey() {
    const keyVal = document.getElementById('apiKeyInput').value.trim();
    localStorage.setItem('gemini_api_key', keyVal);
    updateBadgeState(keyVal);
}

function updateBadgeState(key) {
    const headerBadge = document.getElementById('headerBadge');
    const modeStat = document.getElementById('modeStat');
    if (key.length > 5) {
        headerBadge.innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-emerald-500 inline-block mr-1.5 animate-pulse"></span>Pro Engine Active`;
        headerBadge.className = "text-[10px] text-emerald-400 font-semibold flex items-center";
        modeStat.innerText = "Pro Conversational";
        modeStat.className = "text-emerald-400 font-semibold";
    } else {
        headerBadge.innerHTML = `<span class="h-1.5 w-1.5 rounded-full bg-amber-500 inline-block mr-1.5"></span>Local Core Active`;
        headerBadge.className = "text-[10px] text-amber-500 font-semibold flex items-center";
        modeStat.innerText = "Local Fallback";
        modeStat.className = "text-amber-500 font-semibold";
    }
}

// --- VOICE ASSISTANT LOGIC ---
function startDictation() {
    if (window.hasOwnProperty('webkitSpeechRecognition') || window.hasOwnProperty('SpeechRecognition')) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        const inputField = document.getElementById('userInput');
        const originalPlaceholder = inputField.placeholder;
        inputField.placeholder = "Listening...";

        recognition.start();

        recognition.onresult = function(e) {
            inputField.value = e.results[0][0].transcript;
            inputField.placeholder = originalPlaceholder;
            recognition.stop();
        };

        recognition.onerror = function(e) {
            inputField.placeholder = "Microphone error. Try again.";
            recognition.stop();
        }
    } else {
        alert("Voice recognition is not supported in this browser.");
    }
}

function speakText(text) {
    if ('speechSynthesis' in window) {
        const cleanText = text.replace(/[*#_`]/g, '').trim();
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'en-US';
        utterance.rate = 1.0; 
        utterance.pitch = 1.0; 
        
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
    }
}

// --- MESSAGE HANDLING LOGIC ---
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function fillAndSubmit(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
}

async function sendMessage() {
    const inputField = document.getElementById('userInput');
    const userText = inputField.value.trim();
    const stream = document.getElementById('messageStream');
    
    if (!userText) return;

    // Render User Message
    stream.innerHTML += `
        <div class="max-w-2xl mx-auto flex flex-col items-end space-y-1.5 animate-fadeIn">
            <span class="text-[10px] text-slate-500 font-bold uppercase tracking-widest px-1">You</span>
            <div class="bg-indigo-600/10 border border-indigo-500/15 text-slate-200 rounded-2xl px-6 py-4 text-sm max-w-[85%] leading-relaxed">
                ${userText}
            </div>
        </div>
    `;
    
    inputField.value = '';
    stream.scrollTop = stream.scrollHeight;

    // Render Loading Indicator
    const tempId = 'loading-' + Date.now();
    stream.innerHTML += `
        <div class="max-w-2xl mx-auto flex space-x-4 animate-pulse pt-6" id="${tempId}">
            <div class="h-9 w-9 rounded-xl bg-indigo-950/30 border border-indigo-800/20 flex items-center justify-center text-indigo-400 shrink-0">
                <i data-lucide="cpu" class="h-4.5 w-4.5"></i>
            </div>
            <div class="flex-1 space-y-2.5 pt-2">
                <div class="h-3.5 bg-slate-800 rounded w-1/4"></div>
                <div class="h-2.5 bg-slate-900 rounded w-full"></div>
                <div class="h-2.5 bg-slate-900 rounded w-2/3"></div>
            </div>
        </div>
    `;
    lucide.createIcons();
    stream.scrollTop = stream.scrollHeight;

    const activeApiKey = document.getElementById('apiKeyInput').value.trim();

    try {
        // Fetch to Vercel Backend
        const response = await fetch('https://python-chat-bot-lac.vercel.app/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userText, apiKey: activeApiKey })
        });
        
        const data = await response.json();
        document.getElementById(tempId).remove();

        if (data.latency_ms !== undefined) {
            document.getElementById('latencyStat').innerText = data.latency_ms + 'ms';
        }

        const cleanHTML = marked.parse(data.answer || data.detail);

        // Render Bot Response
        stream.innerHTML += `
            <div class="max-w-2xl mx-auto flex space-x-4 pt-6 animate-fadeIn">
                <div class="h-9 w-9 rounded-xl bg-indigo-950/50 border border-indigo-800/20 flex items-center justify-center text-indigo-400 shrink-0">
                    <i data-lucide="bot" class="h-4.5 w-4.5"></i>
                </div>
                <div class="flex-1 text-sm text-slate-300 pt-0.5 markdown-body overflow-hidden">
                    ${cleanHTML}
                </div>
            </div>
        `;
        
        // Apply syntax highlighting and speak the response out loud
        Prism.highlightAll();
        speakText(data.answer || data.detail);
        
    } catch (error) {
        document.getElementById(tempId).remove();
        stream.innerHTML += `
            <div class="max-w-2xl mx-auto flex space-x-4 pt-6">
                <div class="h-9 w-9 rounded-xl bg-rose-950/20 border border-rose-900/30 flex items-center justify-center text-rose-400 shrink-0">
                    <i data-lucide="alert-octagon" class="h-4.5 w-4.5"></i>
                </div>
                <div class="flex-1 text-sm text-rose-400 pt-1 font-semibold">
                    Backend Connection Loss: Ensure your cloud server is running.
                </div>
            </div>
        `;
    }

    lucide.createIcons();
    stream.scrollTop = stream.scrollHeight;
}