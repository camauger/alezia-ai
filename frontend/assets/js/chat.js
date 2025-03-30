/**
 * Gestion des conversations avec les personnages
 */

// Dépendances
let aleziaAPI; // Sera initialisé après le chargement de la page

// Variables globales
let currentCharacter = null;
let currentSession = null;
let isProcessingMessage = false;
let messageQueue = [];

// Initialisation du module
document.addEventListener('DOMContentLoaded', () => {
    aleziaAPI = window.aleziaAPI;

    // Références aux éléments DOM
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const startNewChatButton = document.getElementById('start-new-chat');
    const characterSelector = document.getElementById('character-selector');
    const loadingIndicator = document.getElementById('loading-indicator');
    const apiStatusIndicator = document.getElementById('api-status');

    // Vérifier la connexion à l'API
    checkApiConnection();

    // Configuration des événements
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (startNewChatButton) {
        startNewChatButton.addEventListener('click', startNewChat);
    }

    if (characterSelector) {
        characterSelector.addEventListener('change', handleCharacterChange);
        loadCharacters();
    }

    // Mise à jour périodique du statut de l'API
    setInterval(checkApiConnection, 15000);
});

/**
 * Vérifie la connexion à l'API
 */
async function checkApiConnection() {
    const apiStatusIndicator = document.getElementById('api-status');
    if (!apiStatusIndicator) return;

    try {
        const status = await aleziaAPI.checkHealth();
        if (status.status === 'ok') {
            apiStatusIndicator.textContent = 'Connecté';
            apiStatusIndicator.className = 'status-connected';

            // Activer les contrôles
            enableChatControls();
        } else {
            apiStatusIndicator.textContent = 'Connexion limitée';
            apiStatusIndicator.className = 'status-warning';

            // Partiellement activer les contrôles
            enableChatControls(true);
        }
    } catch (error) {
        console.error('Erreur de connexion à l\'API:', error);
        apiStatusIndicator.textContent = 'Déconnecté';
        apiStatusIndicator.className = 'status-disconnected';

        // Désactiver les contrôles
        disableChatControls();
    }
}

/**
 * Active les contrôles de chat
 * @param {boolean} limited - Si true, active en mode limité
 */
function enableChatControls(limited = false) {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const characterSelector = document.getElementById('character-selector');
    const startNewChatButton = document.getElementById('start-new-chat');

    if (messageInput) messageInput.disabled = false;
    if (sendButton) sendButton.disabled = false;
    if (characterSelector) characterSelector.disabled = false;
    if (startNewChatButton) startNewChatButton.disabled = false;

    if (limited) {
        // Ajouter une classe pour indiquer le mode limité
        document.getElementById('chat-container')?.classList.add('limited-mode');
    } else {
        document.getElementById('chat-container')?.classList.remove('limited-mode');
    }
}

/**
 * Désactive les contrôles de chat
 */
function disableChatControls() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const characterSelector = document.getElementById('character-selector');
    const startNewChatButton = document.getElementById('start-new-chat');

    if (messageInput) messageInput.disabled = true;
    if (sendButton) sendButton.disabled = true;
    if (characterSelector) characterSelector.disabled = true;
    if (startNewChatButton) startNewChatButton.disabled = true;

    document.getElementById('chat-container')?.classList.add('disconnected-mode');
}

/**
 * Charge la liste des personnages depuis l'API
 */
async function loadCharacters() {
    const characterSelector = document.getElementById('character-selector');
    if (!characterSelector) return;

    try {
        // Récupérer la liste des personnages
        const characters = await aleziaAPI.getCharacters();

        // Vider le sélecteur actuel
        characterSelector.innerHTML = '<option value="">Sélectionnez un personnage...</option>';

        // Ajouter les personnages au sélecteur
        if (characters && Array.isArray(characters)) {
            characters.forEach(character => {
                const option = document.createElement('option');
                option.value = character.id;
                option.textContent = character.name;
                characterSelector.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erreur lors du chargement des personnages:', error);
        showError('Impossible de charger les personnages. Veuillez réessayer plus tard.');
    }
}

/**
 * Gère le changement de personnage sélectionné
 */
async function handleCharacterChange() {
    const characterSelector = document.getElementById('character-selector');
    if (!characterSelector) return;

    const characterId = characterSelector.value;
    if (!characterId) {
        currentCharacter = null;
        clearChat();
        return;
    }

    try {
        // Afficher l'indicateur de chargement
        showLoadingIndicator();

        // Récupérer les détails du personnage
        currentCharacter = await aleziaAPI.getCharacter(characterId);

        // Démarrer une nouvelle conversation
        await startNewChat();

        // Masquer l'indicateur de chargement
        hideLoadingIndicator();
    } catch (error) {
        console.error('Erreur lors du changement de personnage:', error);
        showError('Impossible de charger les détails du personnage.');
        hideLoadingIndicator();
    }
}

/**
 * Démarre une nouvelle session de chat
 */
async function startNewChat() {
    if (!currentCharacter) {
        showError('Veuillez d\'abord sélectionner un personnage.');
        return;
    }

    try {
        // Afficher l'indicateur de chargement
        showLoadingIndicator();

        // Créer une nouvelle session
        currentSession = await aleziaAPI.createChatSession(currentCharacter.id);

        // Réinitialiser l'interface
        clearChat();

        // Ajouter un message de bienvenue
        addSystemMessage(`Conversation démarrée avec ${currentCharacter.name}.`);

        // Générer un message de bienvenue du personnage
        const welcomeResponse = await aleziaAPI.sendMessage(
            currentSession.id,
            "Bonjour, pouvez-vous vous présenter?"
        );

        // Ajouter le message de bienvenue du personnage
        addCharacterMessage(welcomeResponse.content);

        // Masquer l'indicateur de chargement
        hideLoadingIndicator();
    } catch (error) {
        console.error('Erreur lors du démarrage d\'une nouvelle conversation:', error);
        showError('Impossible de démarrer une nouvelle conversation.');
        hideLoadingIndicator();
    }
}

/**
 * Envoie un message au personnage
 */
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    if (!messageInput) return;

    const message = messageInput.value.trim();
    if (!message) return;

    if (!currentSession) {
        showError('Vous devez d\'abord démarrer une conversation.');
        return;
    }

    if (isProcessingMessage) {
        // Si un message est déjà en cours de traitement, ajouter à la file d'attente
        messageQueue.push(message);
        messageInput.value = '';
        return;
    }

    try {
        // Définir l'état de traitement
        isProcessingMessage = true;

        // Ajouter le message de l'utilisateur à l'interface
        addUserMessage(message);

        // Vider le champ de saisie
        messageInput.value = '';

        // Afficher l'indicateur d'attente
        showTypingIndicator();

        // Envoyer le message à l'API
        const response = await aleziaAPI.sendMessage(currentSession.id, message);

        // Masquer l'indicateur d'attente
        hideTypingIndicator();

        // Ajouter la réponse du personnage à l'interface
        addCharacterMessage(response.content);

        // Réinitialiser l'état de traitement
        isProcessingMessage = false;

        // Traiter le message suivant dans la file d'attente s'il y en a un
        if (messageQueue.length > 0) {
            const nextMessage = messageQueue.shift();
            setTimeout(() => {
                messageInput.value = nextMessage;
                sendMessage();
            }, 100);
        }
    } catch (error) {
        console.error('Erreur lors de l\'envoi du message:', error);
        showError('Impossible d\'envoyer le message. Veuillez réessayer.');
        hideTypingIndicator();
        isProcessingMessage = false;
    }
}

/**
 * Ajoute un message de l'utilisateur à l'interface
 * @param {string} message - Contenu du message
 */
function addUserMessage(message) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';

    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    contentElement.textContent = message;

    messageElement.appendChild(contentElement);
    chatContainer.appendChild(messageElement);

    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Ajoute un message du personnage à l'interface
 * @param {string} message - Contenu du message
 */
function addCharacterMessage(message) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = 'message character-message';

    const avatarElement = document.createElement('div');
    avatarElement.className = 'message-avatar';

    // Ajouter l'image du personnage si disponible
    if (currentCharacter && currentCharacter.avatar_url) {
        const imgElement = document.createElement('img');
        imgElement.src = currentCharacter.avatar_url;
        imgElement.alt = currentCharacter.name;
        avatarElement.appendChild(imgElement);
    } else {
        // Avatar par défaut
        avatarElement.innerHTML = '<i class="fas fa-user"></i>';
    }

    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';

    // Formatter le message (convertir les sauts de ligne en HTML)
    contentElement.innerHTML = message.replace(/\n/g, '<br>');

    messageElement.appendChild(avatarElement);
    messageElement.appendChild(contentElement);
    chatContainer.appendChild(messageElement);

    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Ajoute un message système à l'interface
 * @param {string} message - Contenu du message
 */
function addSystemMessage(message) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const messageElement = document.createElement('div');
    messageElement.className = 'message system-message';
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);

    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Affiche une erreur dans l'interface
 * @param {string} message - Message d'erreur
 */
function showError(message) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const errorElement = document.createElement('div');
    errorElement.className = 'message error-message';
    errorElement.textContent = message;
    chatContainer.appendChild(errorElement);

    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Vide le contenu du chat
 */
function clearChat() {
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }
}

/**
 * Affiche l'indicateur de chargement
 */
function showLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
}

/**
 * Masque l'indicateur de chargement
 */
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

/**
 * Affiche l'indicateur de saisie du personnage
 */
function showTypingIndicator() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    // Vérifier si un indicateur existe déjà
    if (document.getElementById('typing-indicator')) return;

    const indicatorElement = document.createElement('div');
    indicatorElement.id = 'typing-indicator';
    indicatorElement.className = 'message character-message typing';

    const avatarElement = document.createElement('div');
    avatarElement.className = 'message-avatar';

    // Ajouter l'image du personnage si disponible
    if (currentCharacter && currentCharacter.avatar_url) {
        const imgElement = document.createElement('img');
        imgElement.src = currentCharacter.avatar_url;
        imgElement.alt = currentCharacter.name;
        avatarElement.appendChild(imgElement);
    } else {
        // Avatar par défaut
        avatarElement.innerHTML = '<i class="fas fa-user"></i>';
    }

    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    contentElement.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

    indicatorElement.appendChild(avatarElement);
    indicatorElement.appendChild(contentElement);
    chatContainer.appendChild(indicatorElement);

    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Masque l'indicateur de saisie du personnage
 */
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}