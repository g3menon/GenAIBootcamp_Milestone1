const API_URL = '/api'; // Changed to relative path for Vercel 

let chatHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    loadSuggestions();

    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

async function loadSuggestions() {
    try {
        const res = await fetch(`${API_URL}/suggestions`);
        const suggestions = await res.json();
        const container = document.getElementById('suggestions');

        suggestions.forEach(suggest => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-chip';
            btn.textContent = suggest;
            btn.onclick = () => {
                document.getElementById('user-input').value = suggest;
                sendMessage();
            };
            container.appendChild(btn);
        });
    } catch (e) {
        console.error("Failed to load suggestions", e);
    }
}

async function sendMessage() {
    const inputField = document.getElementById('user-input');
    const message = inputField.value.trim();
    if (!message) return;

    // Hide suggestions on first message
    document.getElementById('suggestions').style.display = 'none';

    appendMessage('user', message);
    chatHistory.push({ role: 'user', content: message });

    inputField.value = '';

    // Disable inputs
    inputField.disabled = true;
    document.getElementById('send-btn').disabled = true;

    appendMessage('bot', 'Thinking...', true);

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message, chat_history: chatHistory })
        });

        const data = await response.json();
        removeThinking();

        const botResponse = data.response || "Something went wrong.";
        appendMessage('bot', botResponse);
        chatHistory.push({ role: 'assistant', content: botResponse });

    } catch (error) {
        console.error(error);
        removeThinking();
        appendMessage('bot', 'Sorry, I am having trouble connecting to the server.');
    } finally {
        inputField.disabled = false;
        document.getElementById('send-btn').disabled = false;
        inputField.focus();
    }
}

function parseMarkdownLinks(text) {
    // Basic parser for markdown links to HTML tags, allowing optional spaces before '('
    return text.replace(/\[([^\]]+)\]\s*\(([^)]+)\)/g, '<a href="$2" target="_blank" class="source-link">$1</a>');
}

function appendMessage(sender, text, isThinking = false) {
    const container = document.getElementById('chat-messages');

    const msgElement = document.createElement('div');
    msgElement.className = `message ${sender}-message`;

    if (isThinking) {
        msgElement.id = "thinking-message";
        msgElement.innerHTML = text;
    } else {
        const formattedText = parseMarkdownLinks(text.replace(/\ng/, '<br>').replace(/\n/g, '<br>'));
        msgElement.innerHTML = formattedText;

        if (sender === 'bot') {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';

            const copyBtn = document.createElement('button');
            copyBtn.className = 'action-btn copy-btn';
            copyBtn.innerHTML = '<span class="material-icons" style="font-size: 18px;">content_copy</span>';
            copyBtn.title = 'Copy to clipboard';
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(text);
                copyBtn.innerHTML = '<span class="material-icons" style="font-size: 18px; color: #10b981;">done</span>';
                setTimeout(() => {
                    copyBtn.innerHTML = '<span class="material-icons" style="font-size: 18px;">content_copy</span>';
                }, 2000);
            };

            const thumbUpBtn = document.createElement('button');
            thumbUpBtn.className = 'action-btn thumb-btn';
            thumbUpBtn.innerHTML = '<span class="material-icons" style="font-size: 18px;">thumb_up</span>';
            thumbUpBtn.title = 'Helpful';
            thumbUpBtn.onclick = () => { thumbUpBtn.style.color = '#10b981'; };

            const thumbDownBtn = document.createElement('button');
            thumbDownBtn.className = 'action-btn thumb-btn';
            thumbDownBtn.innerHTML = '<span class="material-icons" style="font-size: 18px;">thumb_down</span>';
            thumbDownBtn.title = 'Not helpful';
            thumbDownBtn.onclick = () => { thumbDownBtn.style.color = '#ef4444'; };

            actionsDiv.appendChild(copyBtn);
            actionsDiv.appendChild(thumbUpBtn);
            actionsDiv.appendChild(thumbDownBtn);

            msgElement.appendChild(actionsDiv);

            // Add icon for bot
            const iconImg = document.createElement('img');
            iconImg.className = 'bot-icon';
            iconImg.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"%3E%3Crect width="24" height="24" fill="%23004C8F" rx="2"/%3E%3Crect x="8" y="0" width="8" height="24" fill="%23FFFFFF"/%3E%3Crect x="0" y="8" width="24" height="8" fill="%23FFFFFF"/%3E%3Crect x="8" y="8" width="8" height="8" fill="%23ED232A"/%3E%3C/svg%3E';
            iconImg.alt = 'HDFC';
            msgElement.prepend(iconImg);
        }
    }

    container.appendChild(msgElement);
    container.scrollTop = container.scrollHeight;
}

function removeThinking() {
    const thinking = document.getElementById('thinking-message');
    if (thinking) {
        thinking.remove();
    }
}
