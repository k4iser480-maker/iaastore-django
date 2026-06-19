/**
 * Chatbot Helper — Widget de chat flotante
 * IAA Store
 */
(function () {
    'use strict';

    // --- State ---
    let isOpen = false;
    let hasGreeted = false;

    // --- DOM refs (set after DOMContentLoaded) ---
    let toggle, chatWindow, messagesArea, input, sendBtn, badge;

    // --- CSRF token from cookie ---
    function getCookie(name) {
        let val = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const c = cookies[i].trim();
                if (c.substring(0, name.length + 1) === (name + '=')) {
                    val = decodeURIComponent(c.substring(name.length + 1));
                    break;
                }
            }
        }
        return val;
    }

    // --- Simple markdown: **bold** ---
    function renderMarkdown(text) {
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    // --- Add message bubble ---
    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = 'helper-msg ' + type;
        div.innerHTML = renderMarkdown(text);
        messagesArea.appendChild(div);
        scrollToBottom();
    }

    // --- Add buttons ---
    function addButtons(buttons) {
        const container = document.createElement('div');
        container.className = 'helper-buttons';
        buttons.forEach(function (btn) {
            const el = document.createElement('button');
            el.className = 'helper-btn';
            el.textContent = btn.label;
            el.addEventListener('click', function () {
                // Remove buttons after click
                container.remove();
                // Show user "click" as message
                addMessage(btn.label, 'user');
                sendToServer(null, btn.value);
            });
            container.appendChild(el);
        });
        messagesArea.appendChild(container);
        scrollToBottom();
    }

    // --- Typing indicator ---
    function showTyping() {
        const div = document.createElement('div');
        div.className = 'helper-typing';
        div.id = 'helper-typing-indicator';
        div.innerHTML = '<div class="helper-typing-dot"></div>' +
            '<div class="helper-typing-dot"></div>' +
            '<div class="helper-typing-dot"></div>';
        messagesArea.appendChild(div);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('helper-typing-indicator');
        if (el) el.remove();
    }

    // --- Scroll ---
    function scrollToBottom() {
        setTimeout(function () {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }, 50);
    }

    // --- Send to server ---
    function sendToServer(message, button) {
        showTyping();
        const body = {};
        if (button) body.button = button;
        else body.message = message;

        fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(body),
        })
        .then(function (res) {
            if (res.status === 429) {
                hideTyping();
                addMessage('⏳ Has enviado muchos mensajes. Espera un momento.', 'bot');
                return null;
            }
            return res.json();
        })
        .then(function (data) {
            hideTyping();
            if (!data) return;

            // Render messages with delay
            const msgs = data.messages || [];
            let delay = 0;
            msgs.forEach(function (msg, i) {
                setTimeout(function () {
                    addMessage(msg.text, 'bot');
                }, delay);
                delay += Math.min(msg.text.length * 8, 600);
            });

            // Render buttons after all messages
            if (data.buttons && data.buttons.length > 0) {
                setTimeout(function () {
                    addButtons(data.buttons);
                }, delay + 100);
            }
        })
        .catch(function (err) {
            hideTyping();
            addMessage('Lo siento, ocurrió un error. Intenta de nuevo.', 'bot');
            console.error('Helper chat error:', err);
        });
    }

    // --- Send user message ---
    function sendUserMessage() {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        addMessage(text, 'user');
        sendToServer(text, null);
    }

    // --- Toggle chat ---
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.classList.add('open');
            toggle.classList.add('open');
            badge.style.display = 'none';
            input.focus();
            // Auto-greet on first open
            if (!hasGreeted) {
                hasGreeted = true;
                sendToServer(null, 'inicio');
            }
        } else {
            chatWindow.classList.remove('open');
            toggle.classList.remove('open');
            setTimeout(() => {
                messagesArea.innerHTML = '';
                hasGreeted = false;
            }, 300); // Wait for close animation
        }
    }

    // --- Init ---
    document.addEventListener('DOMContentLoaded', function () {
        toggle = document.getElementById('helper-chat-toggle');
        chatWindow = document.getElementById('helper-chat-window');
        messagesArea = document.getElementById('helper-chat-messages');
        input = document.getElementById('helper-chat-input');
        sendBtn = document.getElementById('helper-chat-send');
        badge = document.getElementById('helper-badge');

        if (!toggle || !chatWindow) return;

        toggle.addEventListener('click', toggleChat);

        document.getElementById('helper-chat-close').addEventListener('click', function () {
            isOpen = false;
            chatWindow.classList.remove('open');
            toggle.classList.remove('open');
            setTimeout(() => {
                messagesArea.innerHTML = '';
                hasGreeted = false;
            }, 300);
        });

        sendBtn.addEventListener('click', sendUserMessage);

        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        });
    });
})();
