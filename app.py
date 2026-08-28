<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Full AI Assistant - Voice + Search + Memory</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 1000px;
            height: 100vh;
            max-height: 750px;
            display: flex;
            flex-direction: column;
            background: #161b22;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin: 20px;
        }
        .header {
            padding: 14px 20px;
            background: #21262d;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }
        .header h1 {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header h1 span { background: #238636; font-size: 10px; padding: 2px 10px; border-radius: 20px; font-weight: 400; }
        .header .stats { font-size: 12px; color: #8b949e; display: flex; gap: 12px; flex-wrap: wrap; }
        .header .stats .online { color: #238636; }
        .tabs {
            display: flex;
            background: #0d1117;
            border-bottom: 1px solid #30363d;
            padding: 0 20px;
            gap: 4px;
        }
        .tabs button {
            padding: 10px 16px;
            background: transparent;
            border: none;
            color: #8b949e;
            font-size: 13px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            font-weight: 500;
        }
        .tabs button:hover { color: #e6edf3; background: #21262d; }
        .tabs button.active { color: #e6edf3; border-bottom-color: #238636; }
        .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .tab-content { display: none; flex: 1; overflow: hidden; }
        .tab-content.active { display: flex; flex-direction: column; }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #0d1117;
        }
        .messages::-webkit-scrollbar { width: 5px; }
        .messages::-webkit-scrollbar-track { background: #161b22; }
        .messages::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
        .msg {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 12px;
            line-height: 1.5;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease;
            position: relative;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .msg.user { align-self: flex-end; background: #238636; color: #fff; border-bottom-right-radius: 4px; }
        .msg.assistant { align-self: flex-start; background: #21262d; border-bottom-left-radius: 4px; }
        .msg .time { font-size: 9px; opacity: 0.5; margin-top: 4px; display: block; }
        .msg .actions { font-size: 11px; margin-top: 6px; display: flex; gap: 10px; }
        .msg .actions button {
            background: transparent;
            border: none;
            color: #8b949e;
            cursor: pointer;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            transition: 0.2s;
        }
        .msg .actions button:hover { background: #30363d; color: #e6edf3; }
        .input-area {
            padding: 12px 20px;
            background: #161b22;
            border-top: 1px solid #30363d;
            display: flex;
            gap: 10px;
            align-items: end;
        }
        .input-area textarea {
            flex: 1;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #e6edf3;
            font-size: 14px;
            resize: none;
            font-family: inherit;
            min-height: 40px;
            max-height: 100px;
            outline: none;
            transition: border 0.2s;
        }
        .input-area textarea:focus { border-color: #238636; }
        .input-area textarea::placeholder { color: #484f58; }
        .input-area button {
            padding: 10px 18px;
            border: none;
            border-radius: 10px;
            background: #238636;
            color: #fff;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
            height: 44px;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .input-area button:hover { background: #2ea043; }
        .input-area button:active { transform: scale(0.96); }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .input-area button.voice-btn { background: #1f6feb; }
        .input-area button.voice-btn:hover { background: #388bfd; }
        .input-area button.voice-btn.listening { background: #da3633; animation: pulse 0.8s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .settings-bar {
            padding: 10px 20px;
            background: #161b22;
            border-top: 1px solid #30363d;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .settings-bar input {
            flex: 1;
            min-width: 120px;
            padding: 7px 12px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #e6edf3;
            font-size: 13px;
            outline: none;
        }
        .settings-bar input:focus { border-color: #238636; }
        .settings-bar input::placeholder { color: #484f58; }
        .settings-bar select {
            padding: 7px 12px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #e6edf3;
            font-size: 13px;
            outline: none;
            cursor: pointer;
        }
        .settings-bar .badge { font-size: 11px; color: #8b949e; }
        .settings-bar .badge.green { color: #238636; }
        .cmd-hint {
            padding: 6px 20px 10px;
            background: #161b22;
            font-size: 11px;
            color: #484f58;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            border-top: 1px solid #21262d;
        }
        .cmd-hint kbd {
            background: #21262d;
            padding: 2px 8px;
            border-radius: 4px;
            color: #8b949e;
            font-size: 10px;
        }
        .typing { align-self: flex-start; color: #8b949e; font-size: 13px; padding: 8px 16px; background: #21262d; border-radius: 12px; animation: pulse 1.2s ease-in-out infinite; }
        .search-results { padding: 10px 20px; background: #0d1117; border-bottom: 1px solid #30363d; max-height: 150px; overflow-y: auto; }
        .search-results .result { padding: 6px 10px; border-radius: 6px; font-size: 13px; cursor: pointer; }
        .search-results .result:hover { background: #21262d; }
        .search-results .result .snippet { color: #8b949e; font-size: 12px; }
        .history-list { padding: 16px 20px; overflow-y: auto; flex: 1; }
        .history-item { padding: 10px 14px; background: #21262d; border-radius: 8px; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
        .history-item:hover { background: #30363d; }
        .history-item .date { font-size: 11px; color: #8b949e; }
        .history-item .preview { font-size: 13px; color: #e6edf3; margin-top: 4px; }
        .history-item .msg-count { font-size: 11px; color: #8b949e; }
        @media (max-width: 600px) {
            .container { max-height: 100vh; border-radius: 0; margin: 0; }
            .msg { max-width: 92%; }
            .settings-bar { flex-direction: column; align-items: stretch; }
            .input-area { flex-wrap: wrap; }
            .header h1 { font-size: 16px; }
            .tabs button { font-size: 12px; padding: 8px 12px; }
        }
    </style>
</head>
<body>
<div class="container">
    <!-- Header -->
    <div class="header">
        <h1>🤖 AI Assistant <span>Full</span></h1>
        <div class="stats">
            <span id="statsDisplay">💬 0 msgs · 📚 0 facts</span>
            <span class="online" id="connectionStatus">⚪ Offline</span>
        </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button class="active" data-tab="chat">💬 Chat</button>
        <button data-tab="history">📜 History</button>
        <button data-tab="search">🔍 Search</button>
    </div>

    <!-- Main Content -->
    <div class="main-content">

        <!-- Chat Tab -->
        <div class="tab-content active" id="tab-chat">
            <div class="messages" id="messageContainer">
                <div class="msg assistant">
                    👋 Hello! I'm your full-featured AI assistant with voice, search, and long-term memory.
                    <span class="time">Just now</span>
                </div>
            </div>
            <div class="input-area">
                <textarea id="userInput" rows="1" placeholder="Type your message... (Shift+Enter for new line)"></textarea>
                <button id="voiceBtn" class="voice-btn" title="Click to speak">🎤</button>
                <button id="sendBtn">Send</button>
            </div>
        </div>

        <!-- History Tab -->
        <div class="tab-content" id="tab-history">
            <div style="padding: 10px 20px; background: #161b22; display: flex; gap: 10px; flex-wrap: wrap; border-bottom: 1px solid #30363d;">
                <button id="refreshHistoryBtn" style="padding: 6px 14px; background: #21262d; color: #e6edf3; border: none; border-radius: 6px; cursor: pointer;">🔄 Refresh</button>
                <button id="clearHistoryBtn" style="padding: 6px 14px; background: #21262d; color: #da3633; border: none; border-radius: 6px; cursor: pointer;">🗑️ Clear All</button>
                <span style="color: #8b949e; font-size: 13px; align-self: center;">Click a conversation to load it</span>
            </div>
            <div class="history-list" id="historyList">
                <div style="color: #484f58; text-align: center; padding: 40px;">No conversations saved yet</div>
            </div>
        </div>

        <!-- Search Tab -->
        <div class="tab-content" id="tab-search">
            <div style="padding: 10px 20px; background: #161b22; display: flex; gap: 10px; border-bottom: 1px solid #30363d;">
                <input type="text" id="searchInput" placeholder="Search your conversations..." style="flex:1; padding: 8px 14px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: #e6edf3; outline: none;" />
                <button id="searchBtn" style="padding: 8px 18px; background: #238636; color: #fff; border: none; border-radius: 8px; cursor: pointer;">🔍 Search</button>
            </div>
            <div class="search-results" id="searchResults"></div>
            <div style="flex:1; overflow-y: auto; padding: 16px 20px;" id="searchContent">
                <div style="color: #484f58; text-align: center; padding: 40px;">Search for keywords in your conversations</div>
            </div>
        </div>

        <!-- Settings -->
        <div class="settings-bar">
            <input type="text" id="apiKeyInput" placeholder="🔑 OpenAI API Key" />
            <select id="modelSelect">
                <option value="gpt-5.5">GPT-5.5</option>
                <option value="gpt-5.4">GPT-5.4</option>
                <option value="gpt-5.2">GPT-5.2</option>
            </select>
            <input type="text" id="webSearchKey" placeholder="🔍 Google Search API Key (optional)" />
            <span class="badge" id="statusBadge">⚪ Not connected</span>
        </div>

        <div class="cmd-hint">
            <span><kbd>/clear</kbd> Clear chat</span>
            <span><kbd>/stats</kbd> Show stats</span>
            <span><kbd>/name</kbd> Set name</span>
            <span><kbd>/interest</kbd> Add interest</span>
            <span><kbd>/facts</kbd> Show facts</span>
            <span><kbd>/export</kbd> Download chat</span>
            <span><kbd>/search</kbd> Search web</span>
            <span><kbd>/voice</kbd> Toggle voice</span>
        </div>
    </div>
</div>

<script>
// ============================================================
//  FULL AI ASSISTANT - Voice + Search + Long-term Memory
//  Everything runs in your browser!
// ============================================================

// ---------- STATE ----------
const state = {
    apiKey: localStorage.getItem('ai_assistant_key') || '',
    model: localStorage.getItem('ai_assistant_model') || 'gpt-5.5',
    webSearchKey: localStorage.getItem('ai_web_search_key') || '',
    conversation: JSON.parse(localStorage.getItem('ai_conversation') || '[]'),
    userName: localStorage.getItem('ai_assistant_name') || null,
    interests: JSON.parse(localStorage.getItem('ai_assistant_interests') || '[]'),
    facts: JSON.parse(localStorage.getItem('ai_assistant_facts') || '[]'),
    messageCount: parseInt(localStorage.getItem('ai_message_count') || '0'),
    isProcessing: false,
    voiceEnabled: localStorage.getItem('ai_voice_enabled') === 'true',
    conversations: JSON.parse(localStorage.getItem('ai_conversations_history') || '[]'),
    currentConvId: localStorage.getItem('ai_current_conv_id') || Date.now().toString()
};

// ---------- DOM REFS ----------
const container = document.getElementById('messageContainer');
const input = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const apiInput = document.getElementById('apiKeyInput');
const modelSelect = document.getElementById('modelSelect');
const webSearchKey = document.getElementById('webSearchKey');
const statusBadge = document.getElementById('statusBadge');
const statsDisplay = document.getElementById('statsDisplay');
const connectionStatus = document.getElementById('connectionStatus');

// ---------- INIT ----------
apiInput.value = state.apiKey;
modelSelect.value = state.model;
webSearchKey.value = state.webSearchKey;

if (state.apiKey) {
    setStatus('🟢 Connected', '#238636');
    connectionStatus.textContent = '🟢 Online';
    connectionStatus.style.color = '#238636';
}

// Load conversation if exists
if (state.conversation.length > 0) {
    container.innerHTML = '';
    state.conversation.forEach(msg => addMessageToUI(msg.role, msg.content, msg.timestamp, false));
}

updateStats();

// ---------- SPEECH RECOGNITION ----------
let recognition = null;
let isListening = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                input.value = transcript;
                voiceBtn.classList.remove('listening');
                isListening = false;
                // Auto-send after voice input
                setTimeout(handleSend, 300);
            }
        }
        if (!event.results[event.results.length-1].isFinal) {
            input.value = transcript + '...';
        }
    };

    recognition.onerror = function(event) {
        voiceBtn.classList.remove('listening');
        isListening = false;
        if (event.error !== 'no-speech') {
            addMessage('assistant', `🎤 Voice error: ${event.error}`);
        }
    };

    recognition.onend = function() {
        voiceBtn.classList.remove('listening');
        isListening = false;
    };
}

voiceBtn.addEventListener('click', function() {
    if (!recognition) {
        addMessage('assistant', '⚠️ Voice recognition not supported in this browser. Try Chrome or Edge.');
        return;
    }
    if (isListening) {
        recognition.stop();
        voiceBtn.classList.remove('listening');
        isListening = false;
        return;
    }
    try {
        recognition.start();
        isListening = true;
        voiceBtn.classList.add('listening');
        input.placeholder = '🎤 Listening...';
    } catch (e) {
        // Already started
    }
});

// ---------- TEXT-TO-SPEECH ----------
function speakText(text) {
    if (!state.voiceEnabled) return;
    if (!('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1;
    const voices = speechSynthesis.getVoices();
    if (voices.length) {
        const female = voices.find(v => v.name.includes('Female') || v.name.includes('Google US English'));
        if (female) utterance.voice = female;
    }
    speechSynthesis.speak(utterance);
}

// ---------- WEB SEARCH ----------
async function webSearch(query) {
    if (!state.webSearchKey) {
        return '⚠️ Google Search API key not set. Add it in settings.';
    }
    try {
        const url = `https://www.googleapis.com/customsearch/v1?key=${state.webSearchKey}&q=${encodeURIComponent(query)}&num=5`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Search API error: ${response.status}`);
        const data = await response.json();
        if (!data.items || data.items.length === 0) return 'No search results found.';
        let results = '🔍 **Search Results:**\n\n';
        data.items.forEach((item, i) => {
            results += `${i+1}. **${item.title}**\n${item.snippet || ''}\n${item.link}\n\n`;
        });
        return results;
    } catch (error) {
        return `❌ Search error: ${error.message}`;
    }
}

// ---------- COMMAND HANDLER ----------
async function handleCommands(text) {
    const cmd = text.trim().toLowerCase();

    if (cmd === '/clear') {
        state.conversation = [];
        container.innerHTML = `<div class="msg assistant">🧹 Conversation cleared.<span class="time">Just now</span></div>`;
        saveConversation();
        updateStats();
        return true;
    }

    if (cmd === '/stats') {
        const msg = `📊 **Stats:**
• Messages: ${state.messageCount}
• Facts learned: ${state.facts.length}
• Interests: ${state.interests.join(', ') || 'None'}
• Model: ${state.model}
• Name: ${state.userName || 'Not set'}
• Voice: ${state.voiceEnabled ? '✅ On' : '❌ Off'}
• Saved conversations: ${state.conversations.length}`;
        addMessage('assistant', msg);
        return true;
    }

    if (cmd.startsWith('/name ')) {
        const name = cmd.slice(6).trim();
        if (name) {
            state.userName = name;
            localStorage.setItem('ai_assistant_name', name);
            addMessage('assistant', `✅ Name set to "${name}"! I'll remember that.`);
        
