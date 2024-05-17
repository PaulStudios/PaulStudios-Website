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
            if (message === '') return;

            addMessage('You', message, 'user-message');

            const data1 = {msg1:message}
            const botResponse = ""
            $.post(url, data1, (data, status) => {
                const botResponse = data.response;
                addMessage('JarvisAI', botResponse, 'bot-message');
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
            $.getJSON('/jarvisai/chat/history', function(data) {
                data.forEach(chat => {
                    const chatItem = $('<div>').addClass('list-group-item chat-history-item').text(`${chat.timestamp} - ${chat.message}`);
                    chatItem.click(() => loadChat(chat.id));
                    chatHistory.append(chatItem);
                });
            });
        }

        function loadChat(chatId) {
            $.getJSON(`/jarvisai/chat/history/${chatId}`, function(data) {
                chatLog.empty();
                data.messages.forEach(msg => {
                    addMessage(msg.sender, msg.message);
                });
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
    };
    });
});