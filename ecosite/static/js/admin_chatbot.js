(function () {
    'use strict';

    let isOpen = false;
    let hasGreeted = false;

    let toggle, chatWindow, messagesArea, input, sendBtn;

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

    function renderMarkdown(text) {
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = 'helper-msg ' + type;
        div.innerHTML = renderMarkdown(text);
        messagesArea.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(function () {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }, 50);
    }

    function addButtons(buttons) {
        const container = document.createElement('div');
        container.className = 'helper-buttons';
        // Add styling for container if needed or rely on flex-wrap
        container.style.display = 'flex';
        container.style.flexWrap = 'wrap';
        container.style.gap = '6px';
        container.style.padding = '4px 0';

        buttons.forEach(function (btn) {
            const el = document.createElement('button');
            el.className = 'helper-context-btn'; // reuse existing class
            el.textContent = btn.label;
            el.addEventListener('click', function () {
                container.remove();
                addMessage(btn.label, 'user');
                sendToServer(btn.value);
            });
            container.appendChild(el);
        });
        messagesArea.appendChild(container);
        scrollToBottom();
    }

    function sendToServer(message) {
        const body = { 
            message: message, 
            path: window.location.pathname 
        };

        fetch('/accounts/panel/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(body),
        })
        .then(function (res) {
            if (res.status === 401) {
                addMessage('No estás autorizado para usar el chat.', 'bot');
                return null;
            }
            return res.json();
        })
        .then(function (data) {
            if (!data) return;
            const msgs = data.messages || [];
            msgs.forEach(function (msg) {
                addMessage(msg.text, 'bot');
            });
            if (data.buttons && data.buttons.length > 0) {
                setTimeout(function () {
                    addButtons(data.buttons);
                }, 100);
            }
        })
        .catch(function (err) {
            addMessage('Error al conectar con Helper.', 'bot');
            console.error(err);
        });
    }

    function sendUserMessage() {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        addMessage(text, 'user');
        sendToServer(text);
    }

    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.classList.add('open');
            toggle.classList.add('open');
            input.focus();
            if (!hasGreeted) {
                hasGreeted = true;
                sendToServer('inicio');
            }
        } else {
            chatWindow.classList.remove('open');
            toggle.classList.remove('open');
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        toggle = document.getElementById('helper-chat-toggle');
        chatWindow = document.getElementById('helper-chat-window');
        messagesArea = document.getElementById('helper-chat-messages');
        input = document.getElementById('helper-chat-input');
        sendBtn = document.getElementById('helper-chat-send');

        if (!toggle || !chatWindow) return;

        toggle.addEventListener('click', toggleChat);

        document.getElementById('helper-chat-close').addEventListener('click', function () {
            isOpen = false;
            chatWindow.classList.remove('open');
            toggle.classList.remove('open');
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
