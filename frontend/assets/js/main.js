/**
 * Alezia AI - Script principal
 * Gestion de l'interface utilisateur
 */

import { aleziaAPI } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // Éléments DOM
    const apiStatusEl = document.getElementById('api-status');
    const llmStatusEl = document.getElementById('llm-status');
    const createCharacterBtn = document.getElementById('create-character');
    const startChatBtn = document.getElementById('start-chat');
    const characterModal = document.getElementById('character-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const characterForm = document.getElementById('character-form');
    const cancelCharacterBtn = document.getElementById('cancel-character');
    const chatContainer = document.getElementById('chat-container');
    const closeChat = document.getElementById('close-chat');
    const userInput = document.getElementById('user-input');
    const sendMessageBtn = document.getElementById('send-message');
    const messagesContainer = document.getElementById('messages-container');
    const recentCharactersContainer = document.getElementById('recent-characters');

    // Variables d'état
    let currentSession = null;
    let currentCharacter = null;
    let characters = [];

    // Initialisation
    init();

    async function init() {
        // Vérification de la connexion à l'API
        await checkAPIConnection();

        // Vérification périodique de la connexion
        setInterval(checkAPIConnection, 30000);

        // Chargement des personnages
        await loadCharacters();

        // Ajout des écouteurs d'événements
        addEventListeners();
    }

    async function checkAPIConnection() {
        const apiConnected = await aleziaAPI.checkConnection();
        updateConnectionStatus(apiStatusEl, apiConnected, 'API connectée', 'API déconnectée');

        if (apiConnected) {
            const llmLoaded = await aleziaAPI.checkLLMStatus();
            updateConnectionStatus(llmStatusEl, llmLoaded, 'Modèle AI chargé', 'Modèle AI non chargé');
            startChatBtn.disabled = !llmLoaded;
        } else {
            updateConnectionStatus(llmStatusEl, false, 'Modèle AI chargé', 'Modèle AI non chargé');
            startChatBtn.disabled = true;
        }
    }

    function updateConnectionStatus(element, isConnected, onlineText, offlineText) {
        if (isConnected) {
            element.classList.remove('offline');
            element.classList.add('online');
            element.innerHTML = `<i class="fas fa-circle"></i> ${onlineText}`;
        } else {
            element.classList.remove('online');
            element.classList.add('offline');
            element.innerHTML = `<i class="fas fa-circle"></i> ${offlineText}`;
        }
    }

    async function loadCharacters() {
        characters = await aleziaAPI.getCharacters();
        renderCharacterList();
    }

    function renderCharacterList() {
        // Vider le conteneur
        recentCharactersContainer.innerHTML = '';

        if (characters.length === 0) {
            // Aucun personnage, afficher un message
            recentCharactersContainer.innerHTML = `
                <div class="character-card placeholder">
                    <div class="character-avatar placeholder"></div>
                    <div class="character-info">
                        <h4>Aucun personnage</h4>
                        <p>Créez votre premier personnage pour commencer</p>
                    </div>
                </div>
            `;
            return;
        }

        // Afficher les personnages
        characters.forEach(character => {
            const characterCard = document.createElement('div');
            characterCard.className = 'character-card';
            characterCard.dataset.id = character.id;

            characterCard.innerHTML = `
                <div class="character-avatar" style="background-image: url('assets/images/placeholder-avatar.jpg')"></div>
                <div class="character-info">
                    <h4>${character.name}</h4>
                    <p>${character.description.substring(0, 50)}${character.description.length > 50 ? '...' : ''}</p>
                </div>
            `;

            characterCard.addEventListener('click', () => selectCharacter(character));
            recentCharactersContainer.appendChild(characterCard);
        });
    }

    function addEventListeners() {
        // Ouvrir la modale de création de personnage
        createCharacterBtn.addEventListener('click', () => {
            characterModal.classList.add('active');
        });

        // Fermer la modale
        closeModalBtn.addEventListener('click', () => {
            characterModal.classList.remove('active');
        });

        // Annuler la création
        cancelCharacterBtn.addEventListener('click', () => {
            characterModal.classList.remove('active');
            characterForm.reset();
        });

        // Soumission du formulaire
        characterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await createCharacter();
        });

        // Démarrer une conversation
        startChatBtn.addEventListener('click', () => {
            if (characters.length > 0) {
                selectCharacter(characters[0]);
            } else {
                characterModal.classList.add('active');
            }
        });

        // Fermer le chat
        closeChat.addEventListener('click', () => {
            chatContainer.classList.add('hidden');
            currentSession = null;
            currentCharacter = null;
        });

        // Envoyer un message
        sendMessageBtn.addEventListener('click', () => sendUserMessage());

        // Envoyer avec Entrée
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        });
    }

    async function createCharacter() {
        const name = document.getElementById('character-name').value;
        const description = document.getElementById('character-description').value;
        const personality = document.getElementById('character-personality').value;
        const backstory = document.getElementById('character-backstory').value;
        const universeId = document.getElementById('character-universe').value;

        // Validation basique
        if (!name || !description || !personality) {
            alert('Veuillez remplir tous les champs obligatoires.');
            return;
        }

        try {
            const newCharacter = await aleziaAPI.createCharacter({
                name,
                description,
                personality,
                backstory: backstory || undefined,
                universe_id: universeId === 'new' ? undefined : parseInt(universeId)
            });

            // Fermer la modale et réinitialiser le formulaire
            characterModal.classList.remove('active');
            characterForm.reset();

            // Recharger les personnages
            await loadCharacters();

            // Sélectionner le nouveau personnage
            selectCharacter(newCharacter);
        } catch (error) {
            alert(`Erreur lors de la création du personnage: ${error.message}`);
        }
    }

    async function selectCharacter(character) {
        currentCharacter = character;

        // Mise à jour de l'interface
        document.getElementById('chat-character-name').textContent = character.name;
        document.getElementById('chat-universe').textContent = character.universe || 'Univers inconnu';

        // Création d'une nouvelle session
        try {
            const session = await aleziaAPI.createSession(character.id);
            currentSession = session;

            // Vider les messages précédents
            messagesContainer.innerHTML = `
                <div class="system-message">
                    <p>Début de la conversation avec ${character.name}. Le personnage est prêt à interagir.</p>
                </div>
            `;

            // Afficher le chat
            chatContainer.classList.remove('hidden');
            userInput.focus();
        } catch (error) {
            alert(`Erreur lors de la création de la session: ${error.message}`);
        }
    }

    async function sendUserMessage() {
        const message = userInput.value.trim();

        if (!message || !currentSession) return;

        // Ajouter le message de l'utilisateur
        addMessageToChat('user', message);

        // Vider le champ de saisie
        userInput.value = '';

        try {
            // Indicateur de chargement
            const loadingEl = document.createElement('div');
            loadingEl.className = 'system-message';
            loadingEl.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Le personnage est en train de répondre...</p>';
            messagesContainer.appendChild(loadingEl);

            // Envoyer le message à l'API
            const response = await aleziaAPI.sendMessage(currentSession.id, message);

            // Supprimer l'indicateur de chargement
            messagesContainer.removeChild(loadingEl);

            // Ajouter la réponse du personnage
            addMessageToChat('character', response.content);

            // Scroll automatique vers le bas
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (error) {
            console.error('Erreur lors de l\'envoi du message:', error);

            // Afficher un message d'erreur
            const errorEl = document.createElement('div');
            errorEl.className = 'system-message';
            errorEl.innerHTML = `<p class="error"><i class="fas fa-exclamation-triangle"></i> Erreur: ${error.message}</p>`;
            messagesContainer.appendChild(errorEl);
        }
    }

    function addMessageToChat(sender, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender}`;

        if (sender === 'user') {
            messageEl.innerHTML = `
                <div class="message-content">
                    ${content}
                </div>
            `;
        } else {
            messageEl.innerHTML = `
                <div class="message-avatar" style="background-image: url('assets/images/placeholder-avatar.jpg')"></div>
                <div class="message-content">
                    ${content}
                </div>
            `;
        }

        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});