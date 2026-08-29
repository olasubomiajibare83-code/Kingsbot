<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KingsBot AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: 100%;
            max-width: 900px;
            height: 100vh;
            max-height: 750px;
            display: flex;
            flex-direction: column;
            background: #161b22;
            border-radius: 16px;
            overflow: hidden;
            margin: 10px;
            border: 1px solid #30363d;
        }
        .header {
            padding: 14px 20px;
            background: #21262d;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }
        .header h1 {
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header h1 span {
            background: #238636;
            font-size: 10px;
            padding: 2px 10px;
            border-radius: 20px;
            font-weight: 400;
        }
        .header .stats {
            font-size: 12px;
            color: #8b949e;
            display: flex;
            gap: 14px;
        }
        .header .stats .online {
            color: #238636;
        }
        .tabs {
            display: flex;
            background: #0d1117;
            border-bottom: 1px solid #30363d;
            padding: 0 16px;
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
            transition: 0.2s;
            font-weight: 500;
        }
        .tabs button:hover {
            color: #e6edf3;
            background: #21262d;
        }
        .tabs button.active {
            color: #e6edf3;
            border-bottom-color: #238636;
        }
        .tab-content {
            display: none;
            flex: 1;
            overflow: hidden;
            flex-direction: column;
        }
        .tab-content.active {
            display: flex;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #0d1117;
        }
        .messages::-webkit-scrollbar {
            width: 5px;
        }
        .messages::-webkit-scrollbar-track {
            background: #161b22;
        }
        .messages::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 10px;
        }
        .msg {
            max-width: 85%;
            padding: 10px 16px;
            border-radius: 12px;
            word-wrap: break-word;
            line-height: 1.6;
            font-size: 14px;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .msg.user {
            align-self: flex-end;
            background: #238636;
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .msg.bot {
            align-self: flex-start;
            background: #21262d;
            border-bottom-left-radius: 4px;
        }
        .msg .time {
            font-size: 9px;
            opacity: 0.5;
            margin-top: 4px;
            display: block;
        }
        .msg .actions {
            margin-top: 6px;
            display: flex;
            gap: 8px;
        }
        .msg .actions button {
            background: transparent;
            border: none;
            color: #8b949e;
            cursor: pointer;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            transition: 0.2s;
        }
        .msg .actions button:hover {
            background: #30363d;
            color: #e6edf3;
        }
        .msg pre {
            background: #0d1117;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 13px;
            margin: 6px 0;
        }
        .msg code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }
        .input-area {
            padding: 10px 16px;
            background: #161b22;
            border-top: 1px solid #30363d;
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .input-area input {
            flex: 1;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #e6edf3;
            font-size: 14px;
            outline: none;
            min-height: 42px;
        }
        .input-area input:focus {
            border-color: #238636;
        }
        .input-area input::placeholder {
            color: #484f58;
        }
        .input-area button {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: #238636;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
            white-space: nowrap;
            height: 42px;
            transition: 0.2s;
        }
        .input-area button:hover {
            background: #2ea043;
        }
        .input-area button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .input-area button.voice {
            background: #1f6feb;
            min-width: 42px;
            padding: 0 12px;
        }
        .input-area button.voice:hover {
            background: #388bfd;
        }
        .input-area button.voice.listening {
            background: #da3633;
            animation: pulse 0.8s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .typing {
            align-self: flex-start;
            color: #8b949e;
            padding: 8px 16px;
            background: #21262d;
            border-radius: 12px;
            font-size: 13px;
            animation: pulse 1.2s infinite;
        }
        .footer {
            padding: 6px 16px;
            background: #161b22;
            border-top: 1px solid #21262d;
            font-size: 10px;
            color: #484f58;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .footer kbd {
            background: #21262d;
            padding: 1px 8px;
            border-radius: 4px;
            color: #8b949e;
            font-size: 10px;
        }
        .badge {
            font-size: 10px;
            color: #238636;
        }
        .history-list {
            padding: 16px 20px;
            overflow-y: auto;
            flex: 1;
        }
        .history-item {
            padding: 10px 14px;
            background: #21262d;
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: 0.2s;
            border: 1px solid #30363d;
        }
        .history-item:hover {
            background: #30363d;
            border-color: #238636;
        }
        .history-item .date {
            font-size: 11px;
            color: #8b949e;
        }
        .history-item .preview {
            font-size: 13px;
            margin-top: 4px;
        }
        .history-item .msg-count {
            font-size: 11px;
            color: #8b949e;
            margin-top: 4px;
        }
        .search-results {
            padding: 10px 16px;
            background: #0d1117;
            border-bottom: 1px solid #30363d;
            max-height: 150px;
            overflow-y: auto;
        }
        .search-results .result {
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
            border: 1px solid transparent;
        }
        .search-results .result:hover {
            background: #21262d;
            border-color: #30363d;
        }
        .search-results .result .snippet {
            color: #8b949e;
            font-size: 12px;
        }
        .tab-actions {
            padding: 10px 16px;
            background: #161b22;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            border-bottom: 1px solid #30363d;
        }
        .tab-actions button {
            padding: 6px 14px;
            background: #21262d;
            color: #e6edf3;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: 0.2s;
        }
        .tab-actions button:hover {
            background: #30363d;
        }
        .tab-actions button.danger {
            color: #da3633;
        }
        .tab-actions button.primary {
            background: #1f6feb;
            color: #fff;
        }
        .tab-actions button.primary:hover {
            background: #388bfd;
        }
        .search-input-area {
            padding: 10px 16px;
            background: #161b22;
            display: flex;
            gap: 10px;
            border-bottom: 1px solid #30363d;
        }
        .search-input-area input {
            flex: 1;
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #e6edf3;
            outline: none;
            font-size: 14px;
        }
        .search-input-area input:focus {
            border-color: #238636;
        }
        .search-input-area button {
            padding: 8px 18px;
            background: #238636;
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .search-input-area button:hover {
            background: #2ea043;
        }
        .search-content {
            flex: 1;
            overflow-y: auto;
            padding: 16px 20px;
        }
        .search-content .empty {
            color: #484f58;
            text-align: center;
            padding: 40px;
        }
        @media (max-width: 600px) {
            .container { max-height: 100vh; border-radius: 0; margin: 0; }
            .msg { max-width: 92%; }
            .header h1 { font-size: 16px; }
            .tabs button { font-size: 12px; padding: 8px 12px; }
            .input-area button { padding: 8px 14px; font-size: 13px; }
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Header -->
    <div class="header">
        <h1>🤖 KingsBot <span>FREE</span></h1>
        <div class="stats">
            <span id="statsDisplay">💬 0 · 📚 0</span>
            <span class="online" id="statusBadge">🟢 Online</span>
        </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button class="active" data-tab="chat">💬 Chat</button>
        <button data-tab="history">📜 History</button>
        <button data-tab="search">🔍 Search</button>
    </div>

    <!-- ===== CHAT TAB ===== -->
    <div class="tab-content active" id="tab-chat">
        <div class="messages" id="messageContainer">
            <div class="msg bot">
                👋 Welcome to <strong>KingsBot</strong>!<br>
                🎤 Click mic to speak · 💬 Type anything<br>
                🔍 Type <kbd>/search</kbd> for web search<br>
                📜 Click <strong>History</strong> to see past chats
                <span class="time">Just now</span>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type your message..." autofocus />
            <button class="voice" id="voiceBtn" title="Click to speak">🎤</button>
            <button id="sendBtn">Send</button>
        </div>
    </div>

    <!-- ===== HISTORY TAB ===== -->
    <div class="tab-content" id="tab-history">
        <div class="tab-actions">
            <button id="refreshHistoryBtn">🔄 Refresh</button>
            <button class="danger" id="clearHistoryBtn">🗑️ Clear All</button>
            <button class="primary" id="exportAllBtn">📦 Export All</button>
            <span style="color: #8b949e; font-size: 13px; align-self: center;">Click to load conversation</span>
        </div>
        <div class="history-list" id="historyList">
            <div style="color: #484f58; text-align: center; padding: 40px;">No conversations saved</div>
        </div>
    </div>

    <!-- ===== SEARCH TAB ===== -->
    <div class="tab-content" id="tab-search">
        <div class="search-input-area">
            <input type="text" id="searchInput" placeholder="Search your conversations..." />
            <button id="searchBtn">🔍 Search</button>
        </div>
        <div class="search-results" id="searchResults"></div>
        <div class="search-content" id="searchContent">
            <div class="empty">Search for keywords in your conversations</div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <span class="badge">✅ Free AI</span>
        <span><kbd>/help</kbd> Commands</span>
        <span><kbd>/search</kbd> Web</span>
        <span><kbd>/clear</kbd> Clear</span>
        <span><kbd>/stats</kbd> Stats</span>
        <span><kbd>/name</kbd> Set name</span>
        <span><kbd>/facts</kbd> My facts</span>
        <span><kbd>/export</kbd> Export</span>
    </div>
</div>

<script>
    // ============================================================
    // KINGSBOT - COMPLETE WORKING VERSION
    // All features: Chat, Voice, Memory, History, Search, Export
    // ============================================================

    // ===== STATE =====
    const state = {
        conversation: JSON.parse(localStorage.getItem('kb_chat') || '[]'),
        messageCount: parseInt(localStorage.getItem('kb_count') || '0'),
        facts: JSON.parse(localStorage.getItem('kb_facts') || '[]'),
        userName: localStorage.getItem('kb_name') || null,
        interests: JSON.parse(localStorage.getItem('kb_interests') || '[]'),
        conversations: JSON.parse(localStorage.getItem('kb_all_chats') || '[]'),
        currentConvId: localStorage.getItem('kb_current_id') || Date.now().toString(),
        processing: false,
        isListening: false,
        voiceEnabled: true
    };

    // ===== DOM REFS =====
    const container = document.getElementById('messageContainer');
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const statsDisplay = document.getElementById('statsDisplay');

    // ===== INIT =====
    if (state.conversation.length > 0) {
        container.innerHTML = '';
        state.conversation.forEach(msg => addMessageUI(msg.role, msg.content, msg.time));
    }
    updateStats();

    // ===== VOICE INPUT =====
    let recognition = null;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.lang = 'en-US';
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onresult = function(e) {
            let transcript = '';
            for (let i = e.resultIndex; i < e.results.length; i++) {
                transcript += e.results[i][0].transcript;
                if (e.results[i].isFinal) {
                    input.value = transcript;
                    voiceBtn.classList.remove('listening');
                    state.isListening = false;
                    handleSend();
                }
            }
            if (!e.results[e.results.length - 1].isFinal) {
                input.value = transcript + '...';
            }
        };

        recognition.onerror = function() {
            voiceBtn.classList.remove('listening');
            state.isListening = false;
            input.placeholder = 'Type your message...';
        };

        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
            state.isListening = false;
            input.placeholder = 'Type your message...';
        };
    }

    voiceBtn.addEventListener('click', function() {
        if (!recognition) {
            addMessage('bot', '⚠️ Voice not supported. Please type.');
            return;
        }
        if (state.isListening) {
            recognition.stop();
            voiceBtn.classList.remove('listening');
            state.isListening = false;
            input.placeholder = 'Type your message...';
            return;
        }
        try {
            recognition.start();
            state.isListening = true;
            voiceBtn.classList.add('listening');
            input.placeholder = '🎤 Listening...';
        } catch (e) {
            // Already started
        }
    });

    // ===== TEXT TO SPEECH =====
    function speakText(text) {
        if (!state.voiceEnabled) return;
        if (!('speechSynthesis' in window)) return;
        const clean = text.replace(/[#*_`]/g, '').replace(/\n/g, ' ').substring(0, 400);
        if (clean.length < 10) return;
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        speechSynthesis.speak(utterance);
    }

    // ===== WEB SEARCH =====
    async function webSearch(query) {
        try {
            const url = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
            const res = await fetch(url);
            if (!res.ok) {
                return `🔍 Search error. Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}`;
            }
            const data = await res.json();
            let result = '🔍 **Search Results:**\n\n';
            if (data.Abstract) {
                result += `📝 ${data.Abstract}\n\n`;
                if (data.AbstractURL) result += `🔗 ${data.AbstractURL}\n\n`;
            }
            if (data.RelatedTopics) {
                let count = 0;
                for (const topic of data.RelatedTopics) {
                    if (count >= 5) break;
                    if (topic.Text) {
                        result += `• ${topic.Text.substring(0, 250)}\n`;
                        if (topic.FirstURL) result += `  🔗 ${topic.FirstURL}\n`;
                        result += '\n';
                        count++;
                    }
                }
            }
            if (!data.Abstract && !data.RelatedTopics) {
                result += `No summary found.\n\n🔗 Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}\n`;
                result += `📖 Try Wikipedia: https://en.wikipedia.org/wiki/${encodeURIComponent(query.replace(/ /g, '_'))}`;
            }
            return result;
        } catch (e) {
            return `🔍 Search error. Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}`;
        }
    }

    // ===== SMART AI =====
    async function getAIResponse(message) {
        const history = state.conversation.slice(-4);
        let context = '';
        for (const msg of history) {
            context += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n`;
        }

        try {
            const prompt = `You are KingsBot, a helpful AI assistant.\n\nPrevious conversation:\n${context}\nUser: ${message}\nAssistant:`;
            const response = await fetch(
                'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        inputs: prompt,
                        parameters: { max_length: 350, temperature: 0.8 }
                    }),
                    signal: AbortSignal.timeout(12000)
                }
            );
            if (response.ok) {
                const data = await response.json();
                if (Array.isArray(data) && data.length > 0 && data[0].generated_text) {
                    let result = data[0].generated_text;
                    result = result.replace(prompt, '').trim();
                    if (result && result.length > 3) return result;
                }
            }
        } catch (e) {
            // Fall through to fallback
        }

        return getFallback(message);
    }

    function getFallback(msg) {
        const lower = msg.toLowerCase();

        if (lower.match(/^(hi|hello|hey|howdy|greetings)/)) {
            const name = state.userName ? `, ${state.userName}` : '';
            return `Hello${name}! 👋 How can I help you today?`;
        }
        if (lower.includes('how are you')) {
            return "I'm doing great! Thanks for asking. 😊 How can I assist you?";
        }
        if (lower.includes('my name is')) {
            const match = lower.match(/my name is ([a-z]+)/i);
            if (match && match[1]) {
                const name = match[1].charAt(0).toUpperCase() + match[1].slice(1);
                state.userName = name;
                localStorage.setItem('kb_name', name);
                return `Nice to meet you, ${name}! 👍 I'll remember your name. What would you like to do?`;
            }
        }
        if (lower.includes('code') || lower.includes('python') || lower.includes('function')) {
            return `Here's a Python example:

\`\`\`python
def greet(name):
    \"\"\"Say hello to someone\"\"\"
    return f"Hello, {name}!"

# Usage
print(greet("World"))
\`\`\`

What specific code would you like me to write?`;
        }
        if (lower.includes('help') || lower.includes('what can you do')) {
            return `📖 **I can help with:**

💬 Chat about anything
💻 Write code in any language
📚 Explain complex topics
🔍 Search the web: /search query
🧠 Remember your name and interests

**Commands:**
/help - Show this
/clear - Clear chat
/stats - Your stats
/name YourName - Set name
/interest Hobby - Add interest
/facts - What I know about you
/search query - Web search
/export - Download all data

What would you like to do? 🚀`;
        }
        if (lower.includes('bye') || lower.includes('goodbye')) {
            return "👋 Goodbye! Come back anytime you need help. Have a great day!";
        }
        if (lower.includes('thank')) {
            return "You're welcome! 😊 Is there anything else I can help with?";
        }
        if (lower.includes('weather')) {
            return `🌤️ For weather, use: /search weather in your city

Example: /search weather London`;
        }

        return `That's interesting! 🤔 Could you tell me more about "${msg.substring(0, 50)}..."? I'd love to help!`;
    }

    // ===== COMMANDS =====
    function handleCommand(text) {
        const cmd = text.trim().toLowerCase();

        if (cmd === '/clear') {
            state.conversation = [];
            state.messageCount = 0;
            container.innerHTML = `<div class="msg bot">🧹 Conversation cleared.<span class="time">Just now</span></div>`;
            updateStats();
            localStorage.setItem('kb_chat', JSON.stringify([]));
            localStorage.setItem('kb_count', '0');
            return true;
        }

        if (cmd === '/stats') {
            const msg = `📊 **Your Stats:**
• 💬 Messages: ${state.messageCount}
• 📚 Facts learned: ${state.facts.length}
• ❤️ Interests: ${state.interests.join(', ') || 'None'}
• 👤 Name: ${state.userName || 'Not set'}
• 💾 Saved conversations: ${state.conversations.length}
• 🎤 Voice: ${state.voiceEnabled ? 'On' : 'Off'}`;
            addMessage('bot', msg);
            return true;
        }

        if (cmd.startsWith('/name ')) {
            const name = cmd.substring(6).trim();
            if (name) {
                state.userName = name;
                localStorage.setItem('kb_name', name);
                addMessage('bot', `✅ Name set to "${name}"! I'll remember that.`);
            }
            return true;
        }

        if (cmd.startsWith('/interest ')) {
            const interest = cmd.substring(10).trim();
            if (interest && !state.interests.includes(interest)) {
                state.interests.push(interest);
                localStorage.setItem('kb_interests', JSON.stringify(state.interests));
                addMessage('bot', `✅ Added "${interest}" to your interests!`);
            }
            return true;
        }

        if (cmd === '/facts') {
            if (state.facts.length === 0 && !state.userName && state.interests.length === 0) {
                addMessage('bot', '📚 I don\'t know much about you yet. Tell me things like:\n- "My name is John"\n- "I like coding"\n- "I work as a developer"\n\nI\'ll remember everything! 😊');
            } else {
                let msg = '📚 **What I know about you:**\n\n';
                if (state.userName) msg += `👤 Name: ${state.userName}\n`;
                if (state.interests.length) msg += `❤️ Interests: ${state.interests.join(', ')}\n`;
                if (state.facts.length) {
                    msg += `\n📝 Facts I've learned:\n`;
                    state.facts.forEach((f, i) => msg += `  ${i+1}. ${f}\n`);
                }
                addMessage('bot', msg);
            }
            return true;
        }

        if (cmd === '/export') {
            exportAllData();
            return true;
        }

        if (cmd.startsWith('/search ')) {
            const query = cmd.substring(8).trim();
            if (query) {
                addMessage('bot', `🔍 Searching for "${query}"...`);
                webSearch(query).then(result => addMessage('bot', result));
            }
            return true;
        }

        if (cmd === '/voice') {
            state.voiceEnabled = !state.voiceEnabled;
            addMessage('bot', `🎤 Voice output ${state.voiceEnabled ? 'enabled' : 'disabled'}`);
            return true;
        }

        if (cmd === '/help') {
            addMessage('bot', `📖 **KingsBot Commands:**

💬 **Chat** - Just type anything!
🎤 **Voice** - Click the mic button
🔍 **Search** - /search your question

**Commands:**
/clear - Clear chat
/stats - Show your stats
/name YourName - Set your name
/interest Hobby - Add interest
/facts - Show what I know about you
/export - Download all data
/search query - Web search
/voice - Toggle voice output
/help - Show this help

**Tips:**
• Just type naturally like talking to a friend
• Ask me to write code
• Tell me about yourself - I'll remember!
• Use /search to find information`);
            return true;
        }

        return false;
    }

    // ===== SAVE / LOAD =====
    function saveConversation() {
        if (state.conversation.length > 0) {
            const convData = {
                id: state.currentConvId,
                date: new Date().toISOString(),
                messages: JSON.parse(JSON.stringify(state.conversation)),
                messageCount: state.conversation.length,
                preview: state.conversation[0].content.substring(0, 60) || 'Empty'
            };
            const existing = state.conversations.find(c => c.id === state.currentConvId);
            if (existing) {
                const idx = state.conversations.indexOf(existing);
                state.conversations[idx] = convData;
            } else {
                state.conversations.unshift(convData);
            }
            if (state.conversations.length > 50) {
                state.conversations = state.conversations.slice(0, 50);
            }
            localStorage.setItem('kb_all_chats', JSON.stringify(state.conversations));
        }
        localStorage.setItem('kb_chat', JSON.stringify(state.conversation));
        localStorage.setItem('kb_count', state.messageCount.toString());
        localStorage.setItem('kb_current_id', state.currentConvId);
    }

    function loadConversation(convId) {
        const conv = state.conversations.find(c => c.id === convId);
        if (!conv) return;
        state.currentConvId = convId;
        state.conversation = JSON.parse(JSON.stringify(conv.messages));
        state.messageCount = conv.messages.length;
        localStorage.setItem('kb_chat', JSON.stringify(state.conversation));
        localStorage.setItem('kb_count', state.messageCount.toString());
        localStorage.setItem('kb_current_id', state.currentConvId);
        container.innerHTML = '';
        state.conversation.forEach(msg => addMessageUI(msg.role, msg.content, msg.time));
        updateStats();
        // Switch to chat tab
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.getElementById('tab-chat').classList.add('active');
        document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
        document.querySelector('[data-tab="chat"]').classList.add('active');
    }

    function exportAllData() {
        const data = {
            exportDate: new Date().toISOString(),
            userName: state.userName,
            interests: state.interests,
            facts: state.facts,
            conversations: state.conversations,
            currentConversation: state.conversation,
            messageCount: state.messageCount
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kingsbot_export_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        addMessage('bot', '💾 All data exported successfully!');
    }

    // ===== ADD MESSAGE =====
    function addMessage(role, content) {
        const time = new Date().toLocaleTimeString();
        addMessageUI(role, content, time);
        state.conversation.push({ role, content, time });
        state.messageCount++;
        localStorage.setItem('kb_chat', JSON.stringify(state.conversation));
        localStorage.setItem('kb_count', state.messageCount.toString());
        updateStats();
        saveConversation();
        if (role === 'bot' && content.length > 20) {
            speakText(content);
        }
    }

    function addMessageUI(role, content, time) {
        const div = document.createElement('div');
        div.className = `msg ${role}`;
        let formatted = content;
        // Format code blocks
        if (content.includes('```')) {
            formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
                return `<pre><code>${code.trim()}</code></pre>`;
            });
        }
        formatted = formatted.replace(/\n/g, '<br>');
        div.innerHTML = formatted + `<span class="time">${time}</span>`;
        if (role === 'bot') {
            const clean = content.substring(0, 300).replace(/'/g, "\\'");
            div.innerHTML += `
                <div class="actions">
                    <button onclick="speakText('${clean.replace(/'/g, "\\'")}')">🔊 Listen</button>
                    <button onclick="navigator.clipboard.writeText('${clean.replace(/'/g, "\\'")}')">📋 Copy</button>
                </div>
            `;
        }
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'typing';
        div.id = 'typingIndicator';
        div.textContent = '🤔 Thinking...';
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function removeTyping() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    function updateStats() {
        statsDisplay.textContent = `💬 ${state.messageCount} · 📚 ${state.facts.length}`;
    }

    // ===== EXTRACT FACTS =====
    function extractFacts(userMsg, aiMsg) {
        const combined = userMsg + ' ' + aiMsg;
        const patterns = [
            /my name is ([^\.]+)/i,
            /i (?:am|'m) ([^\.]+)/i,
            /i like ([^\.]+)/i,
            /i work as ([^\.]+)/i,
            /i live in ([^\.]+)/i,
            /i have ([^\.]+)/i,
            /i (?:love|enjoy) ([^\.]+)/i,
            /my favorite ([^\.]+)/i
        ];
        const newFacts = [];
        for (const pattern of patterns) {
            const match = combined.match(pattern);
            if (match && match[1]) {
                const fact = match[1].trim();
                if (fact.length > 3 && !state.facts.includes(fact) && !state.facts.some(f => f.includes(fact) || fact
                        .includes(f))) {
                    newFacts.push(fact);
                }
            }
        }
        if (newFacts.length) {
            state.facts.push(...newFacts);
            localStorage.setItem('kb_facts', JSON.stringify(state.facts));
        }
    }

    // ===== SEND =====
    async function handleSend() {
        const text = input.value.trim();
        if (!text || state.processing) return;

        if (handleCommand(text)) {
            input.value = '';
            return;
        }

        addMessage('user', text);
        input.value = '';

        showTyping();
        state.processing = true;
        sendBtn.disabled = true;
        voiceBtn.disabled = true;

        try {
            const response = await getAIResponse(text);
            removeTyping();
            extractFacts(text, response);
            addMessage('bot', response);
        } catch (err) {
            removeTyping();
            addMessage('bot', '❌ Error. Please try again.');
        }

        state.processing = false;
        sendBtn.disabled = false;
        voiceBtn.disabled = false;
        input.focus();
    }

    // ===== HISTORY =====
    function renderHistory() {
        const list = document.getElementById('historyList');
        if (state.conversations.length === 0) {
            list.innerHTML = '<div style="color: #484f58; text-align: center; padding: 40px;">No conversations saved</div>';
            return;
        }
        list.innerHTML = '';
        state.conversations.forEach(function(conv) {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <div class="date">📅 ${new Date(conv.date).toLocaleString()}</div>
                <div class="preview">${conv.preview || 'Conversation'}</div>
                <div class="msg-count">💬 ${conv.messageCount || 0} messages</div>
            `;
            div.onclick = function() { loadConversation(conv.id); };
            list.appendChild(div);
        });
    }

    // ===== SEARCH =====
    function searchConversations(query) {
        const resultsDiv = document.getElementById('searchResults');
        const contentDiv = document.getElementById('searchContent');

        if (!query || query.length < 2) {
            resultsDiv.innerHTML = '<div style="color: #484f58; padding: 10px;">Type at least 2 characters</div>';
            contentDiv.innerHTML = '<div class="empty">Search for keywords in your conversations</div>';
            return;
        }

        const results = [];
        state.conversations.forEach(function(conv) {
            conv.messages.forEach(function(msg) {
                if (msg.content.toLowerCase().includes(query.toLowerCase())) {
                    results.push({
                        convId: conv.id,
                        date: conv.date,
                        preview: msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : ''),
                        role: msg.role
                    });
                }
            });
        });

        // Also search current conversation
        state.conversation.forEach(function(msg) {
            if (msg.content.toLowerCase().includes(query.toLowerCase())) {
                if (!results.some(function(r) { return r.convId === state.currentConvId && r.preview === msg.content
                        .substring(0, 200); })) {
                    results.push({
                        convId: state.currentConvId,
                        date: msg.time || new Date().toISOString(),
                        preview: msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : ''),
                        role: msg.role
                    });
                }
            }
        });

        if (results.length === 0) {
            resultsDiv.innerHTML = '<div style="color: #484f58; padding: 10px;">No results found</div>';
            contentDiv.innerHTML = '<div class="empty">No matching messages found</div>';
            return;
        }

        resultsDiv.innerHTML = `<div style="color: #8b949e; font-size: 12px; padding: 4px 0;">${results.length} results found</div>`;
        results.slice(0, 20).forEach(function(result) {
            const div = document.createElement('div');
            div.className = 'result';
            div.innerHTML = `
                <div><strong>${result.role === 'user' ? '👤 You' : '🤖 KingsBot'}</strong></div>
                <div class="snippet">${result.preview}</div>
                <div style="font-size: 10px; color: #484f58;">${new Date(result.date).toLocaleString()}</div>
            `;
            div.onclick = function() {
                loadConversation(result.convId);
                document.querySelectorAll('.tab-content').forEach(function(el) { el.classList.remove('active'); });
                document.getElementById('tab-chat').classList.add('active');
                document.querySelectorAll('.tabs button').forEach(function(el) { el.classList.remove('active'); });
                document.querySelector('[data-tab="chat"]').classList.add('active');
            };
            resultsDiv.appendChild(div);
        });
        contentDiv.innerHTML = '<div style="color: #8b949e; padding: 10px;">Click a result to load the conversation</div>';
    }

    // ===== EVENT LISTENERS =====
    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });

    // Tab switching
    document.querySelectorAll('.tabs button').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tabs button').forEach(function(b) { b.classList.remove('active'); });
            btn.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(function(el) { el.classList.remove('active'); });
            document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
            if (btn.dataset.tab === 'history') renderHistory();
        });
    });

    // History buttons
    document.getElementById('refreshHistoryBtn').addEventListener('click', renderHistory);
    document.getElementById('clearHistoryBtn').addEventListener('click', function() {
        if (confirm('Delete all saved conversations?')) {
            state.conversations = [];
            localStorage.setItem('kb_all_chats', JSON.stringify(state.conversations));
            renderHistory();
            addMessage('bot', '🗑️ All history cleared.');
        }
    });
    document.getElementById('exportAllBtn').addEventListener('click', exportAllData);

    // Search
    document.getElementById('searchBtn').addEventListener('click', function() {
        const query = document.getElementById('searchInput').value.trim();
        searchConversations(query);
    });
    document.getElementById('searchInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('searchBtn').click();
        }
    });

    // ===== START =====
    input.focus();
    console.log('✅ KingsBot loaded successfully!');
    console.log('📜 Click History tab for past chats');
    console.log('🔍 Click Search tab to find messages');
    console.log('🎤 Click mic button to speak');
    console.log('💡 Type /help for all commands');
</script>
</body>
</html>
