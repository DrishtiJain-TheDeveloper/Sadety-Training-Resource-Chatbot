// --- START OF FILE script.js ---

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    // Get the initial message passed from Flask template
    const initialBotMessage = chatMessages.getAttribute('data-initial-message') || "Hello! How can I help you with safety training today?";

    // Format the current time for message timestamps
    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    // Add a single message to the chat window
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `message-${sender}`);

        // --- Keep your existing markdown/link processing ---
        let messageText = message;
        messageText = messageText.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        messageText = messageText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        messageText = messageText.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        messageText = messageText.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        // Basic list handling (might need refinement depending on markdown complexity)
        messageText = messageText.replace(/^\s*[\*\-]\s+(.+)$/gm, '<li>$1</li>'); // Covers * and - lists
        messageText = messageText.replace(/(<li>.*?<\/li>)/g, '<ul>$1</ul>'); // Wrap LIs in UL
        messageText = messageText.replace(/<\/ul>\s*<ul>/g, ''); // Combine adjacent ULs
        messageText = messageText.replace(/^\s*(\d+)\.\s+(.+)$/gm, '<li>$2</li>'); // Numbered lists
        messageText = messageText.replace(/(<li>.*?<\/li>)/g, '<ol>$1</ol>'); // Wrap LIs in OL
        messageText = messageText.replace(/<\/ol>\s*<ol>/g, ''); // Combine adjacent OLs
        messageText = messageText.replace(/\n/g, '<br>'); // Newlines
        // --- End markdown/link processing ---

        messageElement.innerHTML = messageText;

        const timeElement = document.createElement('div');
        timeElement.classList.add('message-time');
        timeElement.textContent = formatTime();

        messageElement.appendChild(timeElement);
        chatMessages.appendChild(messageElement);

        // Scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Display loading indicator
    function showLoading() {
        const loadingElement = document.createElement('div');
        loadingElement.classList.add('message', 'message-bot', 'loading-message');
        loadingElement.innerHTML = `<div class="loading-indicator"></div><span class="ms-2">Thinking...</span>`;
        chatMessages.appendChild(loadingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Remove loading indicator
    function hideLoading() {
        const loadingElement = document.querySelector('.loading-message');
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    // Initialize the chat - Just display the first message
    function initializeChat() {
        // Clear any potential placeholders
        chatMessages.innerHTML = '';
        // Add the initial message provided by the server or default
        addMessage(initialBotMessage, 'bot');
        // No fetch needed here, chat starts with user input
    }

    // Send a message (no history involved)
    function sendMessage(message) {
        if (!message.trim()) return;

        userInput.disabled = true;
        addMessage(message, 'user'); // Display user message
        showLoading();

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                 // Try to parse error json if possible
                return response.json().then(err => { throw new Error(err.message || 'Network response was not ok') });
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            // Directly add the single bot response
            addMessage(data.message, 'bot');

            userInput.disabled = false;
            userInput.value = '';
            userInput.focus();
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            addMessage(`Error: ${error.message || "Could not connect to the server. Please try again."}`, 'bot');
            userInput.disabled = false; // Re-enable input on error
        });
    }

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        sendMessage(message); // Directly send message
    });

    // Handle suggestion button clicks
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const suggestionText = this.getAttribute('data-suggestion');
            userInput.value = suggestionText; // Fill input
            sendMessage(suggestionText); // Send suggestion as message
        });
    });

    // Initialize the chat display on page load
    initializeChat();

    // Focus the input field
    userInput.focus();
});
// --- END OF FILE script.js ---
