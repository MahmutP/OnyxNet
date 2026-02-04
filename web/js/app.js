document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Fully Loaded");

    // --- Configuration & State ---

    // Generate UUID
    function uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    const myId = uuidv4();
    let socket;
    let connected = false;

    // GUI Elements
    const statusEl = document.getElementById('connection-status');
    const myIdEl = document.getElementById('my-id');
    const appTitleEl = document.getElementById('app-title');
    const chatBox = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');

    // Validation
    if (!chatBox || !chatForm || !messageInput) {
        console.error("CRITICAL: Required DOM elements missing!", { chatBox, chatForm, messageInput });
        return;
    }

    // Set Initial GUI State
    myIdEl.innerText = myId.substring(0, 8);
    if (typeof ONYX_VERSION !== 'undefined' && appTitleEl) {
        appTitleEl.innerText = "ONYXNET " + ONYX_VERSION;
    }

    // --- Crypto & Networking ---

    // Initialize Crypto then Connect
    (async function init() {
        try {
            await OnyxCrypto.generateKeys();
            connect();
        } catch (e) {
            console.error("Crypto Init Failed:", e);
            addMessage("SYSTEM", "Crypto Initialization Failed!", true);
        }
    })();

    function connect() {
        const wsHost = window.location.hostname || "localhost";
        const wsUrl = `ws://${wsHost}:8889`;

        console.log("Connecting to WebSocket:", wsUrl);
        socket = new WebSocket(wsUrl);

        socket.onopen = async function () {
            console.log("WebSocket Open");
            connected = true;
            statusEl.innerText = "Connected";
            statusEl.className = "text-success";
            addMessage("SYSTEM", "Connected to OnyxNet Relay.", true);

            // Handshake
            const payload = {
                type: "handshake",
                sender_id: myId,
                pubkey: OnyxCrypto.publicKeyPem
            };
            socket.send(JSON.stringify(payload));
        };

        socket.onmessage = async function (event) {
            try {
                const data = JSON.parse(event.data);
                // console.log("RX:", data); 

                if (data.type === "handshake") {
                    await handleHandshake(data);
                } else if (data.type === "msg") {
                    await handleMessage(data);
                }
            } catch (e) {
                console.error("Message Error:", e);
            }
        };

        socket.onclose = function () {
            console.log("WebSocket Closed");
            connected = false;
            statusEl.innerText = "Disconnected";
            statusEl.className = "text-danger";
            addMessage("SYSTEM", "Connection Lost.", true);
        };

        socket.onerror = function (error) {
            console.error("WebSocket Error:", error);
        };
    }

    // --- Handlers ---

    /**
     * Handles incoming handshake data from a new peer.
     * @param {Object} data - The handshake payload containing sender_id and pubkey.
     */
    async function handleHandshake(data) {
        if (data.sender_id === myId) return;

        if (!OnyxCrypto.peerPublicKeys[data.sender_id]) {
            addMessage("SYSTEM", `New Peer: ${data.sender_id.substring(0, 8)}`, true);
            await OnyxCrypto.importPeerKey(data.sender_id, data.pubkey);

            // Reply
            const payload = {
                type: "handshake",
                sender_id: myId,
                pubkey: OnyxCrypto.publicKeyPem
            };
            socket.send(JSON.stringify(payload));
        }
    }

    /**
     * Handles incoming encrypted messages.
     * @param {Object} data - The message payload containing sender_id and encrypted payload.
     */
    async function handleMessage(data) {
        if (data.sender_id === myId) return;

        try {
            const plaintext = await OnyxCrypto.decryptMessage(data.payload, myId);
            addMessage(data.sender_id.substring(0, 8), plaintext);
        } catch (e) {
            console.warn("Decrypt error:", e);
            addMessage("SYSTEM", `Unreadable message from ${data.sender_id.substring(0, 8)}`);
        }
    }

    // --- UI Logic ---

    /**
     * Appends a message to the chat window.
     * @param {string} sender - The display name/ID of the sender.
     * @param {string} text - The message content.
     * @param {boolean} [isSystem=false] - Whether this is a system notification.
     */
    function addMessage(sender, text, isSystem = false) {
        const div = document.createElement('div');
        div.className = "message";

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        let senderHtml = `<span class="sender">&lt;${sender}&gt;</span>`;
        let msgClass = "";

        if (isSystem) {
            senderHtml = `<span class="system-msg">[${sender}]</span>`;
            msgClass = "system-msg";
        } else if (sender === "Me") {
            msgClass = "my-msg";
        }

        div.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${senderHtml} <span class="${msgClass}">${text}</span>`;

        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Autocomplete Handler
    messageInput.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            e.preventDefault(); // Prevent focus change

            const currentText = this.value;
            const commands = ['/clear', '/help', '/quit', '/exit'];

            // Only autocomplete if starts with /
            if (currentText.startsWith('/')) {
                const matches = commands.filter(cmd => cmd.startsWith(currentText));
                if (matches.length === 1) {
                    this.value = matches[0] + ' ';
                }
            }
        }
    });

    chatForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const text = messageInput.value.trim();

        if (!text) return;

        if (!connected) {
            addMessage("SYSTEM", "Cannot send: Not connected to server.", true);
            return;
        }

        // --- COMMANDS ---

        /**
         * Command: /clear
         * Description: Clears all messages from the chat window.
         * Arguments: None
         */
        if (text === '/clear') {
            chatBox.innerHTML = '';
            messageInput.value = '';
            return;
        }

        /**
         * Command: /help
         * Description: Opens the help modal popup.
         * Arguments: None
         */
        if (text === '/help') {
            const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
            helpModal.show();
            messageInput.value = '';
            return;
        }

        /**
         * Command: /quit or /exit
         * Description: Closes the WebSocket connection.
         * Arguments: None
         */
        if (text === '/quit' || text === '/exit') {
            if (socket) {
                socket.close();
            }
            addMessage("SYSTEM", "Session ended. Attempting to close tab...", true);

            // Try to close window
            try {
                window.open('', '_self', '');
                window.close();
            } catch (e) {
                console.log("Could not close window automatically.");
            }

            // Fallback UI
            document.body.innerHTML = `
                <div class="d-flex align-items-center justify-content-center vh-100 bg-black text-success">
                    <div class="text-center">
                        <h1 class="display-1 fw-bold">TERMINATED</h1>
                        <p class="lead">Session Ended. You may close this tab.</p>
                    </div>
                </div>
            `;
            return;
        }

        try {
            // Check peers for E2EE
            if (Object.keys(OnyxCrypto.peerPublicKeys).length === 0) {
                // Even if no peers, we might want to see 'waiting' in logs, or just send to relay?
                // Relay broadcasts. If no one has keys, no one decrypts.
                // But wait, encryptMessage fails if no keys? 
                // crypto.js implementation:
                // loops through peerPublicKeys. If empty, encryptedKeys is empty.
                // Returns payload with empty keys dict.
                addMessage("SYSTEM", "Warning: No peers connected. Message sent but no one can decrypt.", true);
            }

            const payloadData = await OnyxCrypto.encryptMessage(text);
            const msgPayload = {
                type: "msg",
                sender_id: myId,
                payload: payloadData
            };

            socket.send(JSON.stringify(msgPayload));
            addMessage("Me", text);
            messageInput.value = '';

        } catch (e) {
            console.error("Send Failed:", e);
            addMessage("ERROR", "Send Failed: " + e.message, true);
        }
    });

});
