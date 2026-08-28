<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>KingsBot Ultimate AI</title>
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
            max-height: 800px;
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
            line-height: 1.6;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease;
            font-size: 14px;
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
        .msg code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }
        .msg pre {
            background: #0d1117;
            padding: 10px;
            border-radius: 6px;
            margin: 6px 0;
            overflow-x: auto;
            font-size: 13px;
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
            min-height: 44px;
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
            min-width: 44px;
            justify-content: center;
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
                transform: scale(1);
            }
            50% {
                opacity: 0.6;
                transform: scale(0.95);
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
        .settings-bar .badge.blue {
            color: #1f6feb;
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
        @media (max-width: 600px) {
            .container {
                max-height: 100vh;
                border-radius: 0;
                margin: 0;
            }
            .msg {
                max-width: 92%;
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
            <h1>🤖 KingsBot <span>ULTIMATE</span></h1>
            <div class="stats">
                <span id="statsDisplay">💬 0 msgs · 📚 0 facts</span>
                <span class="online" id="connectionStatus">🟢 Online</span>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <button class="active" data-tab="chat">💬 Chat</button>
            <button data-tab="history">📜 History</button>
        </div>

        <!-- Main Content -->
        <div class="main-content">

            <!-- Chat Tab -->
            <div class="tab-content active" id="tab-chat">
                <div class="messages" id="messageContainer">
                    <div class="msg assistant">
                        👋 Welcome to <strong>KingsBot Ultimate</strong>!<br>
                        🎤 <strong>Voice:</strong> Click the mic button to speak<br>
                        💬 <strong>Chat:</strong> Just type anything<br>
                        🧠 <strong>Memory:</strong> I remember everything!<br>
                        🔍 <strong>Search:</strong> Type /search your question<br>
                        <span class="time">Just now</span>
                    </div>
                </div>
                <div class="input-area">
                    <textarea id="userInput" rows="1" placeholder="Type your message... or click 🎤 to speak"></textarea>
                    <button id="voiceBtn" class="voice-btn" title="Click to speak">🎤</button>
                    <button id="sendBtn">Send</button>
                </div>
            </div>

            <!-- History Tab -->
            <div class="tab-content" id="tab-history">
                <div style="padding: 10px 20px; background: #161b22; display: flex; gap: 10px; flex-wrap: wrap; border-bottom: 1px solid #30363d;">
                    <button id="refreshHistoryBtn" style="padding: 6px 14px; background: #21262d; color: #e6edf3; border: none; border-radius: 6px; cursor: pointer;">🔄 Refresh</button>
                    <button id="clearHistoryBtn" style="padding: 6px 14px; background: #21262d; color: #da3633; border: none; border-radius: 6px; cursor: pointer;">🗑️ Clear All</button>
                    <button id="exportAllBtn" style="padding: 6px 14px; background: #1f6feb; color: #fff; border: none; border-radius: 6px; cursor: pointer;">📦 Export All</button>
                    <span style="color: #8b949e; font-size: 13px; align-self: center;">Click a conversation to load it</span>
                </div>
                <div class="history-list" id="historyList">
                    <div style="color: #484f58; text-align: center; padding: 40px;">No conversations saved yet</div>
                </div>
            </div>

            <!-- Settings -->
            <div class="settings-bar">
                <span class="badge green">✅ FREE AI: Active</span>
                <span class="badge blue">🎤 Voice: Ready</span>
                <span class="badge">🧠 Brain: Smart AI</span>
                <span class="badge">💾 Memory: Active</span>
                <span class="badge">🔍 Search: DuckDuckGo</span>
            </div>

            <div class="cmd-hint">
                <span><kbd>/clear</kbd> Clear</span>
                <span><kbd>/stats</kbd> Stats</span>
                <span><kbd>/name</kbd> Set name</span>
                <span><kbd>/interest</kbd> Add interest</span>
                <span><kbd>/facts</kbd> Show facts</span>
                <span><kbd>/export</kbd> Download</span>
                <span><kbd>/search</kbd> Web search</span>
                <span><kbd>/voice</kbd> Toggle voice</span>
                <span><kbd>/help</kbd> Help</span>
            </div>
        </div>
    </div>

    <script>
        // ============================================================
        // KINGSBOT ULTIMATE - Complete AI Assistant
        // Features: Chat, Voice Input/Output, Memory, History, Search
        // 100% FREE - No Installation!
        // ============================================================

        // ---------- STATE ----------
        const state = {
            conversation: JSON.parse(localStorage.getItem('kingsbot_conversation') || '[]'),
            messageCount: parseInt(localStorage.getItem('kingsbot_message_count') || '0'),
            facts: JSON.parse(localStorage.getItem('kingsbot_facts') || '[]'),
            userName: localStorage.getItem('kingsbot_user_name') || null,
            interests: JSON.parse(localStorage.getItem('kingsbot_interests') || '[]'),
            conversations: JSON.parse(localStorage.getItem('kingsbot_conversations') || '[]'),
            voiceEnabled: localStorage.getItem('kingsbot_voice_enabled') !== 'false',
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

        // ---------- SPEECH RECOGNITION (Voice Input) ----------
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
                    addMessage('assistant', '🎤 Voice error: ' + event.error + '. Please try typing.');
                }
            };

            recognition.onend = function() {
                voiceBtn.classList.remove('listening');
                state.isListening = false;
            };
        }

        voiceBtn.addEventListener('click', function() {
            if (!recognition) {
                addMessage('assistant', '⚠️ Voice recognition not supported in this browser. Please use Chrome or Edge.');
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
                input.placeholder = '🎤 Listening... Speak now!';
            } catch (e) {
                // Already started
            }
        });

        // ---------- TEXT-TO-SPEECH (Voice Output) ----------
        function speakText(text) {
            if (!state.voiceEnabled) return;
            if (!('speechSynthesis' in window)) return;
            
            // Clean text for speaking
            const cleanText = text.replace(/[#*_`]/g, '').replace(/\n/g, ' ').substring(0, 500);
            if (cleanText.length < 10) return;
            
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            utterance.volume = 1;
            
            // Try to find a good voice
            const voices = speechSynthesis.getVoices();
            if (voices.length) {
                const female = voices.find(v => v.name.includes('Female') || v.name.includes('Google US English'));
                if (female) utterance.voice = female;
            }
            speechSynthesis.speak(utterance);
        }

        // Load voices
        if ('speechSynthesis' in window) {
            speechSynthesis.getVoices();
            speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
        }

        // ---------- WEB SEARCH ----------
        async function webSearch(query) {
            try {
                const url =
                    `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`;
                const response = await fetch(url);
                if (!response.ok) return '🔍 Search error. Try: https://www.google.com/search?q=' + encodeURIComponent(query);
                const data = await response.json();
                let results = '🔍 **Search Results:**\n\n';
                if (data.Abstract) {
                    results += `📝 **Summary:** ${data.Abstract}\n\n`;
                    if (data.AbstractURL) results += `🔗 Source: ${data.AbstractURL}\n\n`;
                }
                if (data.RelatedTopics) {
                    results += '📚 **Related Topics:**\n';
                    let count = 0;
                    for (const topic of data.RelatedTopics) {
                        if (count >= 5) break;
                        if (topic.Text) {
                            results += `• ${topic.Text.substring(0, 300)}\n`;
                            if (topic.FirstURL) results += `  🔗 ${topic.FirstURL}\n`;
                            results += '\n';
                            count++;
                        }
                    }
                }
                if (!data.Abstract && !data.RelatedTopics) {
                    results += `No summary available.\n\n🔗 Try Google: https://www.google.com/search?q=${encodeURIComponent(query)}\n`;
                    results += `📖 Try Wikipedia: https://en.wikipedia.org/wiki/${encodeURIComponent(query.replace(/ /g, '_'))}`;
                }
                return results;
            } catch (e) {
                return `🔍 Search error. Try: https://www.google.com/search?q=${encodeURIComponent(query)}`;
            }
        }

        // ---------- SMART AI BRAIN ----------
        async function callAI(userMessage) {
            // Build context from conversation
            const history = state.conversation.slice(-8);
            let context = '';
            for (const msg of history) {
                context += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n`;
            }

            let userInfo = '';
            if (state.userName) userInfo += `User's name is ${state.userName}. `;
            if (state.interests.length) userInfo += `User's interests: ${state.interests.join(', ')}. `;
            if (state.facts.length) userInfo += `Facts about user: ${state.facts.join('; ')}. `;

            // Try Hugging Face API first
            try {
                const prompt = `You are KingsBot, a helpful AI assistant with memory and personalization.

${userInfo}

Previous conversation:
${context}

User: ${userMessage}
Assistant:`;

                const response = await fetch(
                    'https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            inputs: prompt,
                            parameters: { max_length: 400, temperature: 0.8 }
                        }),
                        signal: AbortSignal.timeout(15000)
                    }
                );

                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data) && data.length > 0 && data[0].generated_text) {
                        let result = data[0].generated_text;
                        result = result.replace(prompt, '').trim();
                        if (result && result.length > 3) {
                            return result;
                        }
                    }
                    if (data.generated_text) {
                        let result = data.generated_text;
                        result = result.replace(prompt, '').trim();
                        if (result && result.length > 3) {
                            return result;
                        }
                    }
                }
            } catch (e) {
                // API failed, use smart fallback
            }

            // Smart Fallback Responses
            return generateSmartResponse(userMessage);
        }

        function generateSmartResponse(msg) {
            const lower = msg.toLowerCase();

            // Greetings
            if (lower.match(/^(hi|hello|hey|howdy|greetings)/)) {
                const name = state.userName ? `, ${state.userName}` : '';
                return `👋 Hello${name}! How can I help you today? Feel free to ask me anything!`;
            }

            // How are you
            if (lower.includes('how are you')) {
                return "I'm doing great! 🌟 Thanks for asking. I'm here and ready to help you with anything you need!";
            }

            // Name detection
            if (lower.includes('my name is')) {
                const match = lower.match(/my name is ([a-z]+)/i);
                if (match && match[1]) {
                    const name = match[1].charAt(0).toUpperCase() + match[1].slice(1);
                    state.userName = name;
                    localStorage.setItem('kingsbot_user_name', name);
                    return `✅ Nice to meet you, ${name}! I'll remember that. What would you like to do today?`;
                }
            }

            // Coding
            if (lower.includes('code') || lower.includes('python') || lower.includes('function') || lower.includes('programming')) {
                if (lower.includes('reverse')) {
                    return `Here's a Python function to reverse a string:

\`\`\`python
def reverse_string(text):
    """Reverse a string"""
    return text[::-1]

# Example usage
print(reverse_string("hello"))  # Output: "olleh"
\`\`\`

Want me to explain how it works or show another example?`;
                }
                if (lower.includes('sort') || lower.includes('list')) {
                    return `Here's a Python function to sort a list:

\`\`\`python
def sort_list(items):
    """Sort a list in ascending order"""
    return sorted(items)

# Example usage
print(sort_list([3, 1, 4, 2]))  # Output: [1, 2, 3, 4]
\`\`\`

Would you like to sort in descending order instead?`;
                }
                if (lower.includes('fibonacci')) {
                    return `Here's a Python function for Fibonacci sequence:

\`\`\`python
def fibonacci(n):
    """Generate Fibonacci sequence up to n terms"""
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

# Example usage
print(fibonacci(10))  # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
\`\`\`

Want to try a different algorithm?`;
                }
                return `I can help you with code! Here's a simple Python example:

\`\`\`python
def greet(name):
    """Say hello to someone"""
    return f"Hello, {name}!"

# Example
print(greet("World"))
\`\`\`

What specific code would you like me to write? Just tell me what you need!`;
            }

            // Search
            if (lower.includes('search') || lower.includes('find') || lower.includes('look up')) {
                return `🔍 To search the web, use: \`/search your question here\`

Example: \`/search latest AI news\`

I'll fetch results from DuckDuckGo for you!`;
            }

            // Help
            if (lower.includes('help') || lower.includes('what can you do')) {
                return `📖 **I can help you with:**

💬 **Chat** - Talk about anything
💻 **Coding** - Write code in any language
📚 **Learning** - Explain complex topics
🔍 **Search** - Find information online
🧠 **Memory** - Remember your preferences
🎤 **Voice** - Speak instead of typing

**Quick Commands:**
\`/help\` - Show this
\`/stats\` - Your stats
\`/name YourName\` - Set your name
\`/interest Hobby\` - Add interest
\`/facts\` - What I know about you
\`/search query\` - Web search
\`/clear\` - Clear chat
\`/voice\` - Toggle voice output

What would you like to do? 🚀`;
            }

            // Weather
            if (lower.includes('weather')) {
                return `🌤️ For weather information, use: \`/search weather in your city\`

I'll search the web for you! Example: \`/search weather London\``;
            }

            // Goodbye
            if (lower.includes('bye') || lower.includes('goodbye') || lower.includes('see you')) {
                return `👋 Goodbye! It was great talking to you. Come back anytime you need help! Have a wonderful day! 🌟`;
            }

            // Thanks
            if (lower.includes('thank')) {
                return `😊 You're welcome! I'm always here to help. Is there anything else you'd like to know?`;
            }

            // Facts about user
            if (lower.includes('what do you know about me')) {
                if (state.facts.length === 0 && !state.userName && state.interests.length === 0) {
                    return `📝 I don't know much about you yet. Tell me things like:
- "My name is John"
- "I like coding"
- "I work as a developer"

I'll remember everything! 😊`;
                }
                let response = "📚 **What I know about you:**\n\n";
                if (state.userName) response += `👤 Name: ${state.userName}\n`;
                if (state.interests.length) response += `❤️ Interests: ${state.interests.join(', ')}\n`;
                if (state.facts.length) {
                    response += `\n📝 Facts I've learned:\n`;
                    state.facts.forEach((f, i) => response += `  ${i+1}. ${f}\n`);
                }
                return response;
            }

            // Long messages - give detailed response
            if (msg.length > 30) {
                return `That's a great question! 🤔

I can help you with this. Here's what I can do:

1️⃣ **Explain** - I can break down complex topics
2️⃣ **Code** - I can write code examples
3️⃣ **Search** - Use \`/search ${msg.substring(0, 30)}...\`
4️⃣ **Discuss** - We can explore this together

What specific aspect would you like me to focus on? Just ask and I'll dive deeper! 🚀`;
            }

            // Default responses
            const responses = [
                `Interesting! 🤔 Could you tell me more about that?`,
                `I see! What would you like to know specifically about "${msg}"?`,
                `Great question! 😊 How can I help you with that?`,
                `I'd love to help with that! Can you give me more details?`,
                `That's a good topic! What aspect interests you the most?`
            ];
            return responses[Math.floor(Math.random() * responses.length)];
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
            localStorage.setItem('kingsbot_message_count', state.messageCount.toString());
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
                const msg = `📊 **Your Stats:**
        • 💬 Messages: ${state.messageCount}
        • 📚 Facts learned: ${state.facts.length}
        • ❤️ Interests: ${state.interests.join(', ') || 'None'}
        • 👤 Name: ${state.userName || 'Not set'}
        • 💾 Saved conversations: ${state.conversations.length}
        • 🎤 Voice: ${state.voiceEnabled ? 'On' : 'Off'}
        • 🧠 Brain: Smart AI (FREE)`;
                addMessage('assistant', msg);
                return true;
            }

            if (cmd.startsWith('/name ')) {
                const name = cmd.substring(6).trim();
                if (name) {
                    state.userName = name;
                    localStorage.setItem('kingsbot_user_name', name);
                    addMessage('assistant', `✅ Name set to "${name}"! I'll remember that.`);
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
                if (state.facts.length === 0 && !state.userName && state.interests.length === 0) {
                    addMessage('assistant',
                        '📚 I haven\'t learned much about you yet. Tell me things like:\n- "My name is John"\n- "I like coding"\n- "I work as a developer"\n\nI\'ll remember everything!');
                } else {
                    let response = "📚 **What I know about you:**\n\n";
                    if (state.userName) response += `👤 Name: ${state.userName}\n`;
                    if (state.interests.length) response += `❤️ Interests: ${state.interests.join(', ')}\n`;
                    if (state.facts.length) {
                        response += `\n📝 Facts I've learned:\n`;
                        state.facts.forEach((f, i) => response += `  ${i+1}. ${f}\n`);
                    }
                    addMessage('assistant', response);
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
                    addMessage('assistant', `🔍 Searching for "${query}"...`);
                    webSearch(query).then(result => {
                        addMessage('assistant', result);
                    });
                }
                return true;
            }

            if (cmd === '/voice') {
                state.voiceEnabled = !state.voiceEnabled;
                localStorage.setItem('kingsbot_voice_enabled', state.voiceEnabled);
                addMessage('assistant', `🎤 Voice output ${state.voiceEnabled ? 'enabled' : 'disabled'}`);
                return true;
            }

            if (cmd === '/help') {
                addMessage('assistant', `📖 **KingsBot Commands:**

        💬 **Chat** - Just type anything!
        🎤 **Voice** - Click the mic button
        🔍 **Search** - /search your question
        📚 **Learn** - Tell me about yourself

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
            addMessage('assistant', '💾 All data exported successfully!');
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
                setTimeout(() => speakText(content), 300);
            }
        }

        function addMessageToUI(role, content, timestamp, append) {
            const div = document.createElement('div');
            div.className = `msg ${role}`;
            
            // Format code blocks
            let formattedContent = content;
            if (content.includes('```')) {
                formattedContent = formattedContent.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                    return `<pre><code>${code.trim()}</code></pre>`;
                });
            }
            // Convert newlines to <br>
            formattedContent = formattedContent.replace(/\n/g, '<br>');
            
            div.innerHTML = formattedContent +
                `<span class="time">${timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}</span>`;
            
            if (role === 'assistant') {
                const cleanContent = content.replace(/'/g, "\\'").substring(0, 500);
                div.innerHTML += `
                <div class="actions">
                    <button onclick="speakText('${cleanContent.replace(/'/g, "\\'")}')">🔊 Listen</button>
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
                const response = await callAI(text);
                removeTyping(typingId);
                extractFacts(text, response);
                addMessage('assistant', response);
                saveConversation();
            } catch (err) {
                removeTyping(typingId);
                addMessage('assistant', `❌ Error: ${err.message || 'Something went wrong. Please try again.'}`);
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
        document.getElementById('exportAllBtn').addEventListener('click', exportAllData);

        // ---------- KEYBOARD SHORTCUT ----------
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                handleSend();
            }
        });

        // ---------- START ----------
        input.focus();
        console.log('🚀 KingsBot Ultimate loaded!');
        console.log('🎤 Click the mic button to speak');
        console.log('💬 Just type anything - no commands needed!');
        console.log('🔍 Use /search for web search');
        console.log('📜 Click History tab to see past conversations');
    </script>
</body>
</html>
