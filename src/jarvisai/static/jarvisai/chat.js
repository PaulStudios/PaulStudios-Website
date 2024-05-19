var url = ""
var i = 1

document.getElementById("send_button").addEventListener("click", function() {
    url = this.getAttribute("data-url");
});

document.addEventListener("DOMContentLoaded", () => {
    $(document).ready(function() {
        const messageInput = $('#message_input');
        const sendButton = $('#send_button');
        const chatLog = $('#chat_log');
        const chatHistory = $('#chat_history');

        sendButton.click(sendMessage);
        messageInput.keypress(function(e) {
            if (e.which === 13) {
                sendMessage();
            }
        });

        // Fetch chat history on page load
        fetchChatHistory();

        function sendMessage() {
            const message = messageInput.val().trim();
            messageInput.val("")
            if (message === '') return;

            addMessage(username, message, 'user-message');

            const data1 = {msg1:message}
            const botResponse = ""
            $.post(url, data1, (data, status) => {
                const botResponse = data.response;
                addMessage('JarvisAI', botResponse, 'bot-message');
                fetchChatHistory();
            });
            messageInput.value = '';
        }

        function addMessage(sender, message, className) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', className);

        // Create a span for the sender's name
        const senderElement = document.createElement('span');
        senderElement.classList.add('sender-name');
        senderElement.textContent = `${sender}: `;

        // Create a span for the message content
        const messageContentElement = document.createElement('span');
        // Replace newline characters with <br> for multi-line messages
        messageContentElement.innerHTML = message.replace(/\n/g, '<br>');

        // Append sender and message content to the message element
        messageElement.appendChild(senderElement);
        messageElement.appendChild(messageContentElement);

        // Append the message element to the chat box
        chatLog.append(messageElement);

        // Scroll to the bottom of the chat box
        chatLog.scrollTop = chatLog.scrollHeight;
    }

        function fetchChatHistory() {
        chatHistory.empty();
        $.getJSON('/jarvisai/chat/history', function(data) {
            data.forEach(chat => {
                const chatItem = $('<div>').addClass('list-group-item chat-history-item')
                    .html(`<div><strong>User:</strong> ${chat.user_message}</div><div><strong>Bot:</strong> ${chat.bot_response}</div><div><small>${chat.timestamp}</small></div>`);
                chatItem.click(() => loadChat(chat.id));
                chatHistory.append(chatItem);
            });
        });
    }

    function loadChat(chatId) {
        $.getJSON(`/jarvisai/chat/history/${chatId}`, function(data) {
            chatLog.empty();
            console.log(data.messages)
            msgs = data.messages
            addMessage(msgs[0].sender, msgs[0].message, 'user-message', );
            addMessage(msgs[1].sender, msgs[1].message, 'bot-message', );
        });
    }

        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        if (i === 1) {
            message = "Welcome to JarvisAI v0.5.1.\n You can chat with Jarvis and he will respond just like a human."
            addMessage("PaulStudios", message, 'bot-message');;
            i = 0
        }
    });
});