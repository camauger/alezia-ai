/**
 * Alezia AI - Script principal
 * Gestion de l'interface utilisateur
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Éléments du DOM
    const apiStatus = document.getElementById('api-status');
    const llmStatus = document.getElementById('llm-status');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingApiStatus = document.getElementById('loading-api-status');
    const loadingLlmStatus = document.getElementById('loading-llm-status');
    const recentCharactersContainer = document.getElementById('recent-characters');
    const characterModal = document.getElementById('character-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const characterForm = document.getElementById('character-form');
    const cancelCharacterBtn = document.getElementById('cancel-character');
    const createCharacterBtn = document.getElementById('create-character');
    const startChatBtn = document.getElementById('start-chat');
    const chatContainer = document.getElementById('chat-container');
    const messagesContainer = document.getElementById('messages-container');
    const userInput = document.getElementById('user-input');
    const sendMessageBtn = document.getElementById('send-message');
    const closeChat = document.getElementById('close-chat');

    // Variables globales
    let characters = [];
    let currentCharacter = null;
    let currentSession = null;
    let apiConnected = false;
    let llmLoaded = false;

    // Désactiver l'interface pendant le chargement
    disableInterface();

    // Initialisation
    await init();

    async function init() {
        await checkAPIConnection();
        await loadCharacters();
        addEventListeners();
    }

    function disableInterface() {
        // Afficher l'overlay de chargement
        loadingOverlay.style.display = 'flex';

        // Désactiver les boutons principaux
        startChatBtn.disabled = true;
        createCharacterBtn.disabled = true;
    }

    function enableInterface() {
        // Cacher l'overlay de chargement avec une transition
        loadingOverlay.classList.add('fade-out');
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
            loadingOverlay.classList.remove('fade-out');
        }, 500);

        // Activer les boutons principaux
        startChatBtn.disabled = false;
        createCharacterBtn.disabled = false;
    }

    // Vérification du statut de l'API
    async function checkAPIConnection() {
        try {
            console.log("Vérification de la connexion API...");

            // Mettre à jour l'interface de chargement
            loadingApiStatus.innerHTML = '<i class="fas fa-circle pending"></i> Tentative de connexion à l\'API...';

            // Essayer la connexion avec des tentatives répétées
            let connected = false;
            let attempts = 0;
            const maxAttempts = 10;

            while (!connected && attempts < maxAttempts) {
                try {
                    connected = await aleziaAPI.checkConnection();
                    if (connected) break;
                } catch (error) {
                    console.log(`Tentative ${attempts + 1}/${maxAttempts} échouée: ${error.message}`);
                }

                attempts++;
                // Attendre 1 seconde entre chaque tentative
                await new Promise(resolve => setTimeout(resolve, 1000));
                loadingApiStatus.innerHTML = `<i class="fas fa-circle pending"></i> Tentative ${attempts + 1}/${maxAttempts} de connexion...`;
            }

            apiConnected = connected;

            if (connected) {
                // Mise à jour de l'UI principale
                apiStatus.classList.remove('offline');
                apiStatus.classList.add('online');
                apiStatus.innerHTML = '<i class="fas fa-circle"></i> API connectée';

                // Mise à jour de l'overlay de chargement
                loadingApiStatus.innerHTML = '<i class="fas fa-circle online"></i> API connectée';

                // Vérifier le statut du modèle LLM
                loadingLlmStatus.innerHTML = '<i class="fas fa-circle pending"></i> Vérification du modèle AI...';

                const llmLoaded = await aleziaAPI.checkLLMStatus();

                if (llmLoaded) {
                    llmStatus.classList.remove('offline');
                    llmStatus.classList.add('online');
                    llmStatus.innerHTML = '<i class="fas fa-circle"></i> Modèle AI chargé';
                    loadingLlmStatus.innerHTML = '<i class="fas fa-circle online"></i> Modèle AI chargé';
                } else {
                    llmStatus.innerHTML = '<i class="fas fa-circle"></i> Modèle AI non chargé (mode simulation)';
                    llmStatus.classList.add('warning');
                    loadingLlmStatus.innerHTML = '<i class="fas fa-circle warning"></i> Mode simulation activé';
                }

                // Activer l'interface
                enableInterface();
            } else {
                console.error("API déconnectée après plusieurs tentatives");
                apiStatus.innerHTML = '<i class="fas fa-circle"></i> API déconnectée - Mode offline';
                apiStatus.classList.add('error');

                loadingApiStatus.innerHTML = '<i class="fas fa-circle error"></i> Échec de connexion à l\'API';
                loadingLlmStatus.innerHTML = '<i class="fas fa-circle error"></i> Impossible de vérifier le modèle';

                // Activer quand même l'interface mais avec un message d'avertissement
                setTimeout(() => {
                    alert("L'API n'est pas disponible. L'application fonctionnera en mode limité.");
                    enableInterface();
                }, 1000);
            }
        } catch (error) {
            console.error("Erreur lors de la vérification du statut de l'API:", error);
            loadingApiStatus.innerHTML = '<i class="fas fa-circle error"></i> Erreur de connexion';

            // Activer quand même l'interface en mode limité
            setTimeout(() => {
                alert("Erreur de connexion à l'API. L'application fonctionnera en mode limité.");
                enableInterface();
            }, 1000);
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
        console.log("Sélection du personnage:", character);

        // Mise à jour de l'interface
        document.getElementById('chat-character-name').textContent = character.name;
        document.getElementById('chat-universe').textContent = character.universe || 'Univers inconnu';

        // Création d'une nouvelle session
        try {
            console.log("Création d'une session pour le personnage ID:", character.id);
            const session = await aleziaAPI.createSession(character.id);
            console.log("Session créée:", session);
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
            console.error(`Erreur détaillée lors de la création de la session:`, error);
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

            // Logs de débogage pour le chat
            console.log("Envoi de message - Session ID:", currentSession.id);
            console.log("Envoi de message - Contenu:", message);
            console.log("Envoi de message - URL API:", aleziaAPI.baseUrl);

            // Envoyer le message à l'API
            const response = await aleziaAPI.sendMessage(currentSession.id, message);
            console.log("Réponse reçue:", response);

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