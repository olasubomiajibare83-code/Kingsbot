<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>KingsBot Assistant AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
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
            gap: 12px;
            flex-wrap: wrap;
        }
        .header .stats .online {
            color: #238636;
        }
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
        .tabs button:hover {
            color: #e6edf3;
            background: #21262d;
        }
        .tabs button.active {
            color: #e6edf3;
            border-bottom-color: #238636;
        }
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .tab-content {
            display: none;
            flex: 1;
            overflow: hidden;
        }
        .tab-content.active {
            display: flex;
            flex-direction: column;
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
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 12px;
            line-height: 1.5;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(6px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .msg.user {
            align-self: flex-end;
            background: #238636;
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .msg.assistant {
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
            font-size: 11px;
            margin-top: 6px;
            display: flex;
            gap: 10px;
        }
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
        .msg .actions button:hover {
            background: #30363d;
            color: #e6edf3;
        }
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
        .input-area textarea:focus {
            border-color: #238636;
        }
        .input-area textarea::placeholder {
            color: #484f58;
        }
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
        .input-area button:hover {
            background: #2ea043;
        }
        .input-area button:active {
            transform: scale(0.96);
        }
        .input-area button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .input-area button.voice-btn {
            background: #1f6feb;
        }
        .input-area button.voice-btn:hover {
            background: #388bfd;
        }
        .input-area button.voice-btn.listening {
            background: #da3633;
            animation: pulse 0.8s infinite;
        }
        @keyframes pulse {
            0%,
            100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        .settings-bar {
            padding: 10px 20px;
            background: #161b22;
            border-top: 1px solid #30363d;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .settings-bar .badge {
            font-size: 11px;
            color: #8b949e;
        }
        .settings-bar .badge.green {
            color: #238636;
        }
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
        .typing {
            align-self: flex-start;
            color: #8b949e;
            font-size: 13px;
            padding: 8px 16px;
            background: #21262d;
            border-radius: 12px;
            animation: pulse 1.2s ease-in-out infinite;
        }
        .search-results {
            padding: 10px 20px;
            background: #0d1117;
            border-bottom: 1px solid #30363d;
            max-height: 150px;
            overflow-y: auto;
        }
        .search-results .result {
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
        }
        .search-results .result:hover {
            background: #21262d;
        }
        .search-results .result .snippet {
            color: #8b949e;
            font-size: 12px;
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
        }
        .history-item:hover {
            background: #30363d;
        }
        .history-item .date {
            font-size: 11px;
            color: #8b949e;
        }
        .history-item .preview {
            font-size: 13px;
            color: #e6edf3;
            margin-top: 4px;
        }
        .history-item .msg-count {
            font-size: 11px;
            color: #8b949e;
        }
        .free-badge {
            background: #238636;
            color: white;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 11px;
            display: inline-block;
        }
        @media (max-width: 600px) {
            .container {
                max-height: 100vh;
                border-radius: 0;
                margin: 0;
            }
            .msg {
                max-width: 92%;
            }
            .settings-bar {
                flex-direction: column;
                align-items: stretch;
            }
            .input-area {
                flex-wrap: wrap;
            }
            .header h1 {
                font-size: 16px;
            }
            .tabs button {
                font-size: 12px;
                padding: 8px 12px;
            }
        }
    </style>
</head>
<body>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 KingsBot <span>FREE</span></h1>
            <div class="stats">
                <span id="statsDisplay">💬 0 msgs · 📚 0 facts</span>
                <span class="online" id="connectionStatus">🟢 Online</span>
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
                        👋 Welcome to <strong>KingsBot</strong>! I'm 100% FREE with memory, voice, and web search!
                        <span class="time">Just now</span>
                    </div>
                </div>
                <div class="input-area">
                    <textarea id="userInput" rows="1" placeholder="Type your message... Use /help for commands"></textarea>
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
                <span class="badge green">✅ FREE AI: Active</span>
                <span class="badge">🎯 No API Key Required</span>
                <span class="badge">🧠 Brain: Hugging Face</span>
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
                <span><kbd>/help</kbd> Show all</span>
            </div>
        </div>
    </div>

    <script>
        // ============================================================
        // KINGSBOT - COMPLETE HTML VERSION (No Installation!)
        // All features: Memory, Voice, Search, History, Export
        // ============================================================

        // ---------- STATE ----------
        const state = {
            conversation: JSON.parse(localStorage.getItem('kingsbot_conversation') || '[]'),
            messageCount: parseInt(localStorage.getItem('kingsbot_message_count') || '0'),
            facts: JSON.parse(localStorage.getItem('kingsbot_facts') || '[]'),
            userName: localStorage.getItem('kingsbot_user_name') || null,
            interests: JSON.parse(localStorage.getItem('kingsbot_interests') || '[]'),
            conversations: JSON.parse(localStorage.getItem('kingsbot_conversations') || '[]'),
            voiceEnabled: localStorage.getItem('kingsbot_voice_enabled') === 'true',
            currentConvId: localStorage.getItem('kingsbot_current_conv_id') || Date.now().toString(),
            isListening: false,
            processing: false
        };

        // ---------- DOM REFS ----------
        const container = document.getElementById('messageContainer');
        const input = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const voiceBtn = document.getElementById('voiceBtn');
        const statsDisplay = document.getElementById('statsDisplay');

        // ---------- INIT ----------
        if (state.conversation.length > 0) {
            container.innerHTML = '';
            state.conversation.forEach(msg => addMessageToUI(msg.role, msg.content, msg.timestamp, false));
        }
        updateStats();

        // ---------- SPEECH RECOGNITION ----------
        let recognition = null;
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
                        state.isListening = false;
                        setTimeout(handleSend, 300);
                    }
                }
                if (!event.results[event.results.length - 1].isFinal) {
                    input.value = transcript + '...';
                }
            };

            recognition.onerror = function(event) {
                voiceBtn.classList.remove('listening');
                state.isListening = false;
                if (event.error !== 'no-speech') {
                    addMessage('assistant', '🎤 Voice error: ' + event.error);
                }
            };

            recognition.onend = function() {
                voiceBtn.classList.remove('listening');
                state.isListening = false;
            };
        }

        voiceBtn.addEventListener('click', function() {
            if (!recognition) {
                addMessage('assistant', '⚠️ Voice recognition not supported. Try Chrome.');
                return;
            }
            if (state.isListening) {
                recognition.stop();
                voiceBtn.classList.remove('listening');
                state.isListening = false;
                return;
            }
            try {
                recognition.start();
                state.isListening = true;
                voiceBtn.classList.add('listening');
                input.placeholder = '🎤 Listening...';
            } catch (e) {}
        });

        // ---------- TEXT-TO-SPEECH ----------
        function speakText(text) {
            if (!state.voiceEnabled) return;
            if (!('speechSynthesis' in window)) return;
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1;
            speechSynthesis.speak(utterance);
        }

        // ---------- WEB SEARCH (FREE - DuckDuckGo) ----------
        async function webSearch(query) {
            try {
                const url =
                `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
                const response = await fetch(url);
                if (!response.ok) return '🔍 Search error. Try Google directly.';
                const data = await response.json();
                let results = '🔍 **Web Search Results:**\n\n';
                if (data.Abstract) {
                    results += `**Summary:** ${data.Abstract}\n\n`;
                    if (data.AbstractURL) results += `Source: ${data.AbstractURL}\n\n`;
                }
                if (data.RelatedTopics) {
                    results += '**Related Topics:**\n';
                    let count = 0;
                    for (const topic of data.RelatedTopics) {
                        if (count >= 5) break;
                        if (topic.Text) {
                            results += `- ${topic.Text.substring(0, 300)}\n`;
                            if (topic.FirstURL) results += `  Link: ${topic.FirstURL}\n`;
                            results += '\n';
                            count++;
                        }
                    }
                }
                if (!data.Abstract && !data.RelatedTopics) {
                    results += `No summary found. Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}`;
                }
                return results;
            } catch (e) {
                return `🔍 Search error. Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}`;
            }
        }

        // ---------- FREE AI BRAIN (Hugging Face + Fallback) ----------
        async function callFreeAI(userMessage) {
            // Build context
            const history = state.conversation.slice(-6);
            let context = '';
            for (const msg of history) {
                context += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n`;
            }

            let userInfo = '';
            if (state.userName) userInfo += `User's name is ${state.userName}. `;
            if (state.interests.length) userInfo += `User's interests: ${state.interests.join(', ')}. `;
            if (state.facts.length) userInfo += `Facts about user: ${state.facts.join('; ')}. `;

            const prompt =
                `You are KingsBot, a helpful AI assistant with memory and personalization.\n\n${userInfo}\nPrevious conversation:\n${context}\nUser: ${userMessage}\nAssistant:`;

            try {
                const response = await fetch(
                    'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            inputs: prompt,
                            parameters: { max_length: 500, temperature: 0.7 }
                        }),
                        timeout: 30000
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data) && data.length > 0 && data[0].generated_text) {
                        let result = data[0].generated_text;
                        return result.replace(prompt, '').trim() || 'I\'m here to help! What would you like to know?';
                    }
                    if (data.generated_text) {
                        let result = data.generated_text;
                        return result.replace(prompt, '').trim() || 'I\'m here to help! What would you like to know?';
                    }
                }
                return generateFallback(userMessage);
            } catch (e) {
                return generateFallback(userMessage);
            }
        }

        function generateFallback(msg) {
            const lower = msg.toLowerCase();
            if (lower.includes('hello') || lower.includes('hi') || lower.includes('hey')) {
                return 'Hello! How can I help you today?';
            }
            if (lower.includes('how are you')) {
                return "I'm doing great! Thanks for asking. How can I assist you?";
            }
            if (lower.includes('name')) {
                const name = state.userName || 'you';
                return `Your name is ${name}! I'll remember that.`;
            }
            if (lower.includes('help')) {
                return `I can help you with:
            - General questions and answers
            - Coding and programming
            - Writing and editing
            - Learning new topics
            - Remembering your preferences
            - Web search using /search command

            Try typing /help for all commands!`;
            }
            if (lower.includes('code') || lower.includes('programming') || lower.includes('function')) {
                return `I can help you code in Python, JavaScript, HTML, CSS, and more!
            Just ask me to write or explain code. For example:
            "Write a Python function to reverse a string"
            "Explain this JavaScript code"`;
            }
            if (lower.includes('search')) {
                return 'Use /search followed by your query to search the web! Example: /search latest AI news';
            }
            if (lower.includes('bye') || lower.includes('goodbye')) {
                return 'Goodbye! Come back anytime you need help. Have a great day!';
            }
            if (lower.includes('python')) {
                return `Here's a helpful Python tip!

            \`\`\`python
            # Example: Simple function
            def greet(name):
                return f"Hello, {name}!"

            # Usage
            print(greet("World"))
            \`\`\`

            Want me to write something specific?`;
            }
            return `That's a great question! Let me think about it...

            I'm KingsBot, your AI assistant. I have:
            - Memory of our conversations
            - Ability to learn facts about you
            - Web search capability (/search)
            - Conversation history

            If you want a more detailed answer, try:
            1. Breaking down your question
            2. Using /search to find information
            3. Asking for code examples
            4. Explaining what you need help with

            What specific aspect would you like me to elaborate on?`;
        }

        // ---------- CORE FUNCTIONS ----------
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
                localStorage.setItem('kingsbot_conversations', JSON.stringify(state.conversations));
            }
            localStorage.setItem('kingsbot_conversation', JSON.stringify(state.conversation));
            localStorage.setItem('kingsbot_current_conv_id', state.currentConvId);
        }

        function loadConversation(convId) {
            const conv = state.conversations.find(c => c.id === convId);
            if (!conv) return;
            state.currentConvId = convId;
            state.conversation = JSON.parse(JSON.stringify(conv.messages));
            state.messageCount = conv.messages.length;
            localStorage.setItem('kingsbot_conversation', JSON.stringify(state.conversation));
            localStorage.setItem('kingsbot_message_count', state.messageCount.toString());
            localStorage.setItem('kingsbot_current_conv_id', state.currentConvId);
            container.innerHTML = '';
            state.conversation.forEach(msg => addMessageToUI(msg.role, msg.content, msg.timestamp, false));
            updateStats();
            // Switch to chat tab
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-chat').classList.add('active');
            document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
            document.querySelector('[data-tab="chat"]').classList.add('active');
        }

        function extractFacts(userMsg, aiResponse) {
            const combined = userMsg + ' ' + aiResponse;
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
                const matches = combined.match(pattern);
                if (matches && matches[1]) {
                    const fact = matches[1].trim();
                    if (fact.length > 3 && !state.facts.includes(fact) && !state.facts.some(f => f.includes(fact) || fact
                            .includes(f))) {
                        newFacts.push(fact);
                    }
                }
            }
            if (newFacts.length) {
                state.facts.push(...newFacts);
                localStorage.setItem('kingsbot_facts', JSON.stringify(state.facts));
            }
        }

        function handleCommand(text) {
            const cmd = text.trim().toLowerCase();

            if (cmd === '/clear') {
                state.conversation = [];
                state.messageCount = 0;
                container.innerHTML = `<div class="msg assistant">🧹 Conversation cleared.<span class="time">Just now</span></div>`;
                updateStats();
                saveConversation();
                return true;
            }

            if (cmd === '/stats') {
                const msg = `📊 **Stats:**
        • Messages: ${state.messageCount}
        • Facts learned: ${state.facts.length}
        • Interests: ${state.interests.join(', ') || 'None'}
        • Name: ${state.userName || 'Not set'}
        • Saved conversations: ${state.conversations.length}
        • Brain: Hugging Face (FREE)`;
                addMessage('assistant', msg);
                return true;
            }

            if (cmd.startsWith('/name ')) {
                const name = cmd.substring(6).trim();
                if (name) {
                    state.userName = name;
                    localStorage.setItem('kingsbot_user_name', name);
                    addMessage('assistant', `✅ Name set to "${name}"!`);
                }
                return true;
            }

            if (cmd.startsWith('/interest ')) {
                const interest = cmd.substring(10).trim();
                if (interest && !state.interests.includes(interest)) {
                    state.interests.push(interest);
                    localStorage.setItem('kingsbot_interests', JSON.stringify(state.interests));
                    addMessage('assistant', `✅ Added "${interest}" to your interests!`);
                }
                return true;
            }

            if (cmd === '/facts') {
                if (state.facts.length === 0) {
                    addMessage('assistant', '📚 No facts learned yet. Share things about yourself!');
                } else {
                    const list = state.facts.map((f, i) => `${i+1}. ${f}`).join('\n');
                    addMessage('assistant', `📚 **Facts I've learned about you:**\n${list}`);
                }
                return true;
            }

            if (cmd === '/export') {
                exportChat();
                return true;
            }

            if (cmd === '/voice') {
                state.voiceEnabled = !state.voiceEnabled;
                localStorage.setItem('kingsbot_voice_enabled', state.voiceEnabled);
                addMessage('assistant', `🎤 Voice ${state.voiceEnabled ? 'enabled' : 'disabled'}`);
                return true;
            }

            if (cmd.startsWith('/search ')) {
                const query = cmd.substring(8).trim();
                if (query) {
                    addMessage('assistant', `🔍 Searching for "${query}"...`);
                    webSearch(query).then(result => {
                        addMessage('assistant', result);
                    });
                }
                return true;
            }

            if (cmd === '/help') {
                addMessage('assistant', `📖 **Commands:**
        /clear - Clear chat
        /stats - Show stats
        /name YourName - Set your name
        /interest Hobby - Add interest
        /facts - Show learned facts
        /export - Download chat JSON
        /search query - Web search (FREE!)
        /voice - Toggle voice output
        /help - Show this help`);
                return true;
            }

            return false;
        }

        function exportChat() {
            const data = {
                exportDate: new Date().toISOString(),
                userName: state.userName,
                interests: state.interests,
                facts: state.facts,
                conversations: state.conversations,
                currentConversation: state.conversation
            };
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `kingsbot_export_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            addMessage('assistant', '💾 Chat exported successfully!');
        }

        // ---------- UI HELPERS ----------
        function addMessage(role, content) {
            addMessageToUI(role, content, new Date().toISOString(), true);
            state.conversation.push({ role, content, timestamp: new Date().toISOString() });
            state.messageCount++;
            localStorage.setItem('kingsbot_message_count', state.messageCount.toString());
            if (state.conversation.length > 300) {
                state.conversation = state.conversation.slice(-250);
            }
            updateStats();
            saveConversation();
            if (role === 'assistant' && state.voiceEnabled) {
                const cleanText = content.replace(/[#*_`]/g, '').substring(0, 500);
                speakText(cleanText);
            }
        }

        function addMessageToUI(role, content, timestamp, append) {
            const div = document.createElement('div');
            div.className = `msg ${role}`;
            div.innerHTML = content.replace(/\n/g, '<br>') +
                `<span class="time">${timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}</span>`;
            if (role === 'assistant') {
                const cleanContent = content.replace(/'/g, "\\'").substring(0, 300);
                div.innerHTML += `
                <div class="actions">
                    <button onclick="speakText('${cleanContent}')">🔊 Listen</button>
                    <button onclick="navigator.clipboard.writeText('${cleanContent.replace(/'/g, "\\'")}')">📋 Copy</button>
                </div>
            `;
            }
            if (append) {
                container.appendChild(div);
            } else {
                container.insertBefore(div, container.firstChild);
            }
            container.scrollTop = container.scrollHeight;
        }

        function showTyping() {
            const id = 'typing-' + Date.now();
            const div = document.createElement('div');
            div.className = 'typing';
            div.id = id;
            div.textContent = '🤔 Thinking...';
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            return id;
        }

        function removeTyping(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }

        function updateStats() {
            statsDisplay.textContent = `💬 ${state.messageCount} msgs · 📚 ${state.facts.length} facts`;
        }

        // ---------- HANDLE SEND ----------
        async function handleSend() {
            const text = input.value.trim();
            if (!text) return;
            if (state.processing) return;

            // Handle commands
            if (handleCommand(text)) {
                input.value = '';
                input.style.height = 'auto';
                return;
            }

            // Add user message
            addMessage('user', text);
            input.value = '';
            input.style.height = 'auto';

            // Show typing
            const typingId = showTyping();
            state.processing = true;
            sendBtn.disabled = true;
            voiceBtn.disabled = true;

            try {
                const response = await callFreeAI(text);
                removeTyping(typingId);
                extractFacts(text, response);
                addMessage('assistant', response);
                saveConversation();
            } catch (err) {
                removeTyping(typingId);
                addMessage('assistant', `❌ Error: ${err.message || 'Something went wrong'}`);
            }

            state.processing = false;
            sendBtn.disabled = false;
            voiceBtn.disabled = false;
            input.focus();
        }

        // ---------- EVENT LISTENERS ----------
        sendBtn.addEventListener('click', handleSend);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 100) + 'px';
        });

        // Tab switching
        document.querySelectorAll('.tabs button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
                if (btn.dataset.tab === 'history') renderHistory();
            });
        });

        // History
        function renderHistory() {
            const list = document.getElementById('historyList');
            if (state.conversations.length === 0) {
                list.innerHTML = '<div style="color: #484f58; text-align: center; padding: 40px;">No conversations saved yet</div>';
                return;
            }
            list.innerHTML = '';
            state.conversations.forEach(conv => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                <div class="date">📅 ${new Date(conv.date).toLocaleString()}</div>
                <div class="preview">${conv.preview || 'Conversation'}</div>
                <div class="msg-count">💬 ${conv.messageCount || conv.messages?.length || 0} messages</div>
            `;
                div.onclick = () => loadConversation(conv.id);
                list.appendChild(div);
            });
        }

        document.getElementById('refreshHistoryBtn').addEventListener('click', renderHistory);
        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            if (confirm('Delete all saved conversations?')) {
                state.conversations = [];
                localStorage.setItem('kingsbot_conversations', JSON.stringify(state.conversations));
                renderHistory();
                addMessage('assistant', '🗑️ All conversation history cleared.');
            }
        });

        // Search
        document.getElementById('searchBtn').addEventListener('click', () => {
            const query = document.getElementById('searchInput').value.trim();
            searchConversations(query);
        });
        document.getElementById('searchInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('searchBtn').click();
            }
        });

        function searchConversations(query) {
            const resultsDiv = document.getElementById('searchResults');
            const contentDiv = document.getElementById('searchContent');

            if (!query || query.length < 2) {
                resultsDiv.innerHTML = '<div style="color: #484f58; padding: 10px;">Type at least 2 characters to search</div>';
                contentDiv.innerHTML =
                '<div style="color: #484f58; text-align: center; padding: 40px;">Search for keywords in your conversations</div>';
                return;
            }

            const results = [];
            state.conversations.forEach(conv => {
                conv.messages.forEach(msg => {
                    if (msg.content.toLowerCase().includes(query.toLowerCase())) {
                        results.push({
                            convId: conv.id,
                            date: conv.date,
                            preview: msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : ''),
                            full: msg.content,
                            role: msg.role
                        });
                    }
                });
            });

            state.conversation.forEach(msg => {
                if (msg.content.toLowerCase().includes(query.toLowerCase())) {
                    if (!results.some(r => r.full === msg.content && r.convId === state.currentConvId)) {
                        results.push({
                            convId: state.currentConvId,
                            date: msg.timestamp || new Date().toISOString(),
                            preview: msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : ''),
                            full: msg.content,
                            role: msg.role
                        });
                    }
                }
            });

            if (results.length === 0) {
                resultsDiv.innerHTML = '<div style="color: #484f58; padding: 10px;">No results found</div>';
                contentDiv.innerHTML = '<div style="color: #484f58; text-align: center; padding: 40px;">No matching messages found</div>';
                return;
            }

            resultsDiv.innerHTML =
                `<div style="color: #8b949e; font-size: 12px; padding: 4px 0;">${results.length} results found</div>`;
            results.slice(0, 20).forEach(result => {
                const div = document.createElement('div');
                div.className = 'result';
                div.innerHTML = `
                <div><strong>${result.role === 'user' ? '👤 You' : '🤖 KingsBot'}</strong></div>
                <div class="snippet">${result.preview}</div>
                <div style="font-size: 10px; color: #484f58;">${new Date(result.date).toLocaleString()}</div>
            `;
                div.onclick = () => {
                    loadConversation(result.convId);
                    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                    document.getElementById('tab-chat').classList.add('active');
                    document.querySelectorAll('.tabs button').forEach(el => el.classList.remove('active'));
                    document.querySelector('[data-tab="chat"]').classList.add('active');
                };
                resultsDiv.appendChild(div);
            });
            contentDiv.innerHTML = '<div style="color: #8b949e; padding: 10px;">Click a result to load the conversation</div>';
        }

        // ---------- KEYBOARD SHORTCUT ----------
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                handleSend();
            }
        });

        // ---------- LOAD VOICES ----------
        if ('speechSynthesis' in window) {
            speechSynthesis.getVoices();
            speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
        }

        // ---------- START ----------
        input.focus();
        // Load latest conversation if exists
        if (state.conversations.length > 0 && state.conversation.length === 0) {
            // Don't auto-load to keep fresh start
        }

        console.log('🚀 KingsBot loaded! 100% FREE, no installation needed!');
        console.log('💡 Commands: /help for all commands');
        console.log('🎤 Voice: Click the mic button to speak');
        console.log('🔍 Web Search: /search query');
        console.log('📜 History: Click the History tab');
    </script>
</body>
</html>
