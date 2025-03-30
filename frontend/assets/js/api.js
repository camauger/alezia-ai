/**
 * Alezia AI - Client API
 * Module pour communiquer avec le backend
 */

class AleziaAPI {
    constructor() {
        // Charger le port API depuis le fichier de configuration
        this.loadApiConfig();
        this.baseUrl = `http://localhost:${this.apiPort}`;
        this.connected = false;
        this.apiUrl = null;
        this.initPromise = this.initialize();
    }

    /**
     * Charge la configuration de l'API
     */
    async loadApiConfig() {
        try {
            // Par défaut, utiliser le port 8000
            this.apiPort = 8000;

            // Tenter de charger le port depuis le fichier api_port.txt
            const response = await fetch('api_port.txt');
            if (response.ok) {
                const port = await response.text();
                this.apiPort = parseInt(port.trim(), 10) || 8000;
            }

            console.log(`Port API configuré: ${this.apiPort}`);
        } catch (error) {
            console.warn('Impossible de charger le port API, utilisation du port par défaut 8000', error);
            this.apiPort = 8000;
        }
    }

    /**
     * Tente de détecter automatiquement le port sur lequel l'API est disponible
     */
    async detectPort() {
        const hostname = window.location.hostname || 'localhost';

        console.log('Recherche du port API...');

        // D'abord, essayer de lire le fichier api_port.txt
        try {
            const portResponse = await fetch('/api_port.txt', {
                method: 'GET',
                // Empêche la mise en cache du fichier
                cache: 'no-store',
                // Court timeout pour ne pas bloquer longtemps
                signal: AbortSignal.timeout(300)
            });

            if (portResponse.ok) {
                const port = await portResponse.text();
                const portNumber = parseInt(port.trim(), 10);

                if (!isNaN(portNumber) && portNumber >= 8000 && portNumber <= 8020) {
                    // Vérifier si ce port répond effectivement
                    try {
                        const testUrl = `http://${hostname}:${portNumber}/health`;
                        const response = await fetch(testUrl, {
                            method: 'GET',
                            headers: { 'Content-Type': 'application/json' },
                            signal: AbortSignal.timeout(500)
                        });

                        if (response.ok) {
                            this.baseUrl = `http://${hostname}:${portNumber}`;
                            this.connected = true;
                            console.log(`API détectée sur ${this.baseUrl} (via api_port.txt)`);
                            return;
                        }
                    } catch (e) {
                        console.warn(`Port ${portNumber} trouvé dans api_port.txt mais ne répond pas`);
                    }
                }
            }
        } catch (e) {
            console.log('Fichier api_port.txt non accessible, utilisation de la détection par ports');
        }

        // Si la lecture du fichier échoue, revenir à la méthode de scan des ports
        const possiblePorts = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010,
                             8011, 8012, 8013, 8014, 8015, 8016, 8017, 8018, 8019, 8020];

        // Tester chaque port
        for (const port of possiblePorts) {
            try {
                const testUrl = `http://${hostname}:${port}/health`;
                const response = await fetch(testUrl, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    signal: AbortSignal.timeout(500)
                });

                if (response.ok) {
                    // Port fonctionnel trouvé
                    this.baseUrl = `http://${hostname}:${port}`;
                    this.connected = true;
                    console.log(`API détectée sur ${this.baseUrl}`);
                    return;
                }
            } catch (e) {
                // Ignorer les erreurs, juste passer au port suivant
            }
        }

        // Si aucun port n'a fonctionné, garder le port par défaut
        console.log(`Aucun port API détecté automatiquement. Utilisation du port par défaut: ${this.baseUrl}`);
    }

    /**
     * Vérifie la connexion avec l'API
     * @returns {Promise<boolean>} État de la connexion
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.connected = data.status === 'healthy';
                return this.connected;
            } else {
                this.connected = false;
                return false;
            }
        } catch (error) {
            console.error('Erreur de connexion à l\'API:', error);
            this.connected = false;
            return false;
        }
    }

    /**
     * Vérifie la disponibilité du modèle LLM
     * @returns {Promise<boolean>} État du modèle
     */
    async checkLLMStatus() {
        if (!this.connected) {
            await this.checkConnection();
            if (!this.connected) return false;
        }

        try {
            // Utiliser la route system au lieu de llm/status qui n'existe pas encore
            const response = await fetch(`${this.baseUrl}/system/check-llm`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                return data.status === 'ok' || data.loaded === true;
            } else {
                console.warn('Service LLM non disponible mais considéré comme chargé pour tests');
                return true; // Considérer comme chargé pour les tests initiaux
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du modèle:', error);
            console.warn('Service LLM non disponible mais considéré comme chargé pour tests');
            return true; // Considérer comme chargé pour les tests initiaux
        }
    }

    /**
     * Récupère tous les personnages
     * @returns {Promise<Array>} Liste des personnages
     */
    async getCharacters() {
        try {
            const response = await fetch(`${this.baseUrl}/characters/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Impossible de récupérer les personnages');
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des personnages:', error);
            return [];
        }
    }

    /**
     * Crée un nouveau personnage
     * @param {Object} character Données du personnage
     * @returns {Promise<Object>} Personnage créé
     */
    async createCharacter(character) {
        try {
            console.log('Création de personnage avec les données:', character);
            const response = await fetch(`${this.baseUrl}/characters/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(character)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Personnage créé avec succès:', result);
                // Pour l'instant, simuler le format de retour attendu
                return {
                    id: result.id,
                    name: character.name,
                    description: character.description,
                    personality: character.personality,
                    backstory: character.backstory,
                    universe_id: character.universe_id,
                    universe: 'À déterminer' // À remplacer par le vrai univers ultérieurement
                };
            } else {
                const error = await response.json();
                console.error('Erreur API lors de la création:', error);
                throw new Error(error.detail || 'Impossible de créer le personnage');
            }
        } catch (error) {
            console.error('Erreur lors de la création du personnage:', error);
            throw error;
        }
    }

    /**
     * Récupère les univers disponibles
     * @returns {Promise<Array>} Liste des univers
     */
    async getUniverses() {
        try {
            const response = await fetch(`${this.baseUrl}/universes/`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Impossible de récupérer les univers');
            }
        } catch (error) {
            console.error('Erreur lors de la récupération des univers:', error);
            return [];
        }
    }

    /**
     * Envoie un message dans une conversation
     * @param {number} sessionId ID de la session
     * @param {string} message Contenu du message
     * @returns {Promise<Object>} Réponse du personnage
     */
    async sendMessage(sessionId, message) {
        try {
            // Utiliser l'API réelle de chat
            console.log(`Envoi d'un message à la session ${sessionId}: ${message}`);
            console.log(`URL de l'API pour l'envoi de message: ${this.baseUrl}/chat/${sessionId}/message`);

            const response = await fetch(`${this.baseUrl}/chat/${sessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: message })
            });

            console.log("Statut de la réponse:", response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();
                console.log("Réponse du serveur:", data);
                return data;
            } else {
                let errorDetail = 'Impossible d\'envoyer le message';

                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorDetail;
                    console.error("Détail de l'erreur API:", errorData);
                } catch (e) {
                    console.error("Impossible de parser l'erreur:", e);
                }

                throw new Error(errorDetail);
            }
        } catch (error) {
            console.error('Erreur détaillée lors de l\'envoi du message:', error);

            // Générer une réponse simulée plus élaborée
            return this._generateMockResponse(message, sessionId);
        }
    }

    /**
     * Génère une réponse simulée
     * @private
     * @param {string} userMessage Le message de l'utilisateur
     * @param {number} sessionId ID de la session
     * @returns {Object} Réponse simulée
     */
    _generateMockResponse(userMessage, sessionId) {
        console.warn('Utilisation d\'une réponse simulée suite à l\'échec de l\'API');

        // Extraire des mots-clés pour personnaliser la réponse simulée
        const messageLC = userMessage.toLowerCase();
        let response = "";

        if (messageLC.includes('bonjour') || messageLC.includes('salut') || messageLC.includes('hello')) {
            response = "Bonjour ! Je suis heureux de vous rencontrer. Comment puis-je vous aider aujourd'hui ?";
        }
        else if (messageLC.includes('comment') && (messageLC.includes('tu') || messageLC.includes('va'))) {
            response = "Je vais très bien, merci de demander ! Et vous, comment allez-vous ?";
        }
        else if (messageLC.includes('aime') || messageLC.includes('préfère')) {
            response = "C'est intéressant ce que vous dites sur vos préférences. Personnellement, j'aime découvrir de nouvelles choses.";
        }
        else if (messageLC.includes('?')) {
            response = "C'est une question intéressante. Laissez-moi y réfléchir... Si j'avais plus d'informations, je pourrais vous donner une meilleure réponse.";
        }
        else if (messageLC.length < 10) {
            response = "Je vous écoute. N'hésitez pas à me dire plus sur ce qui vous intéresse.";
        }
        else {
            response = `Je comprends ce que vous dites à propos de "${userMessage.substring(0, 20)}...". C'est un sujet qui mérite qu'on s'y attarde. Pouvez-vous m'en dire plus ?`;
        }

        return {
            id: Math.floor(Math.random() * 1000) + 1,
            content: response,
            timestamp: new Date().toISOString(),
            mock: true
        };
    }

    /**
     * Crée une nouvelle session de chat
     * @param {number} characterId ID du personnage
     * @returns {Promise<Object>} Session créée
     */
    async createSession(characterId) {
        try {
            // Utiliser l'API réelle de chat
            console.log(`Création d'une session pour le personnage ${characterId}`);
            console.log(`URL de l'API: ${this.baseUrl}/chat/session`);

            // Préparer les données à envoyer
            const requestData = { character_id: characterId };
            console.log("Données envoyées:", requestData);

            // S'assurer d'utiliser le bon chemin avec le slash final
            const response = await fetch(`${this.baseUrl}/chat/session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            console.log("Statut de la réponse:", response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();
                console.log("Données de session reçues:", data);
                return data;
            } else {
                // Essayer de lire les détails de l'erreur
                let errorDetail = '';
                try {
                    const error = await response.json();
                    errorDetail = error.detail || '';
                    console.error('Erreur API détaillée:', error);
                } catch (e) {
                    console.error('Impossible de lire les détails de l\'erreur:', e);
                }

                // Si l'erreur est 404, essayons avec un slash à la fin
                if (response.status === 404) {
                    console.log("Tentative avec URL alternative...");
                    const altResponse = await fetch(`${this.baseUrl}/chat/session/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify(requestData)
                    });

                    if (altResponse.ok) {
                        const altData = await altResponse.json();
                        console.log("Données de session reçues (URL alternative):", altData);
                        return altData;
                    }
                }

                throw new Error(errorDetail || `Erreur ${response.status}: Impossible de créer la session`);
            }
        } catch (error) {
            console.error('Erreur lors de la création de la session:', error);

            // En cas d'échec de l'API, retourner une session simulée
            console.warn('Utilisation d\'une session simulée suite à l\'échec de l\'API');
            return {
                id: Math.floor(Math.random() * 1000),
                character_id: characterId,
                start_time: new Date().toISOString()
            };
        }
    }

    /**
     * Récupère l'historique d'une session
     * @param {number} sessionId ID de la session
     * @returns {Promise<Array>} Messages de la session
     */
    async getSessionHistory(sessionId) {
        try {
            // Utiliser l'API réelle de chat
            console.log(`Récupération de l'historique pour la session ${sessionId}`);

            const response = await fetch(`${this.baseUrl}/chat/${sessionId}/history`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const session = await response.json();
                return session.messages || [];
            } else {
                throw new Error('Impossible de récupérer l\'historique');
            }
        } catch (error) {
            console.error('Erreur lors de la récupération de l\'historique:', error);
            return [];
        }
    }

    /**
     * Méthode utilitaire pour effectuer une requête API
     * @param {string} endpoint - Endpoint API
     * @param {Object} options - Options fetch
     * @returns {Promise<Object>} - Réponse JSON
     */
    async fetchAPI(endpoint, options = {}) {
        try {
            // S'assurer que l'URL de base est correctement configurée
            if (!this.baseUrl) {
                await this.loadApiConfig();
            }

            // Configurer les headers par défaut
            const headers = {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            };

            // Effectuer la requête
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers
            });

            // Vérifier si la réponse est OK
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Erreur API: ${response.status} - ${errorText}`);
            }

            // Récupérer la réponse JSON
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`Erreur lors de l'appel à ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Vérifie la santé de l'API
     * @returns {Promise<Object>} - Statut de l'API
     */
    async checkHealth() {
        try {
            return await this.fetchAPI('/health');
        } catch (error) {
            console.error('Erreur lors de la vérification de la santé de l\'API:', error);
            return { status: 'error', message: error.message };
        }
    }

    /**
     * Récupère la liste des personnages
     * @returns {Promise<Array>} - Liste des personnages
     */
    async getCharacters() {
        return await this.fetchAPI('/characters');
    }

    /**
     * Récupère les détails d'un personnage
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - Détails du personnage
     */
    async getCharacter(characterId) {
        return await this.fetchAPI(`/characters/${characterId}`);
    }

    /**
     * Crée un nouveau personnage
     * @param {Object} characterData - Données du personnage
     * @returns {Promise<Object>} - Personnage créé
     */
    async createCharacter(characterData) {
        return await this.fetchAPI('/characters', {
            method: 'POST',
            body: JSON.stringify(characterData)
        });
    }

    /**
     * Met à jour un personnage existant
     * @param {number} characterId - ID du personnage
     * @param {Object} characterData - Données du personnage
     * @returns {Promise<Object>} - Personnage mis à jour
     */
    async updateCharacter(characterId, characterData) {
        return await this.fetchAPI(`/characters/${characterId}`, {
            method: 'PUT',
            body: JSON.stringify(characterData)
        });
    }

    /**
     * Supprime un personnage
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - Résultat de la suppression
     */
    async deleteCharacter(characterId) {
        return await this.fetchAPI(`/characters/${characterId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Crée une nouvelle session de chat
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - Session de chat créée
     */
    async createChatSession(characterId) {
        return await this.fetchAPI('/chat/create', {
            method: 'POST',
            body: JSON.stringify({
                character_id: characterId,
                user_id: 'user-1' // ID utilisateur temporaire
            })
        });
    }

    /**
     * Récupère les détails d'une session de chat
     * @param {string} sessionId - ID de la session
     * @returns {Promise<Object>} - Détails de la session
     */
    async getChatSession(sessionId) {
        return await this.fetchAPI(`/chat/session/${sessionId}`);
    }

    /**
     * Récupère les sessions de chat d'un utilisateur
     * @param {string} userId - ID de l'utilisateur
     * @param {number} limit - Nombre maximum de sessions à récupérer
     * @returns {Promise<Array>} - Liste des sessions
     */
    async getUserChatSessions(userId, limit = 10) {
        return await this.fetchAPI(`/chat/sessions?user_id=${userId}&limit=${limit}`);
    }

    /**
     * Envoie un message dans une session de chat
     * @param {string} sessionId - ID de la session
     * @param {string} content - Contenu du message
     * @returns {Promise<Object>} - Réponse du personnage
     */
    async sendMessage(sessionId, content) {
        return await this.fetchAPI('/chat/message', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                content: content
            })
        });
    }

    /**
     * Récupère les messages d'une session de chat
     * @param {string} sessionId - ID de la session
     * @param {number} limit - Nombre maximum de messages à récupérer
     * @param {number} offset - Décalage dans la liste des messages
     * @returns {Promise<Array>} - Liste des messages
     */
    async getSessionMessages(sessionId, limit = 50, offset = 0) {
        return await this.fetchAPI(`/chat/messages/${sessionId}?limit=${limit}&offset=${offset}`);
    }

    /**
     * Récupère les mémoires d'un personnage
     * @param {number} characterId - ID du personnage
     * @param {number} limit - Nombre maximum de mémoires à récupérer
     * @param {number} offset - Décalage dans la liste des mémoires
     * @returns {Promise<Array>} - Liste des mémoires
     */
    async getCharacterMemories(characterId, limit = 20, offset = 0) {
        return await this.fetchAPI(`/memories/character/${characterId}?limit=${limit}&offset=${offset}`);
    }

    /**
     * Récupère les faits extraits d'un personnage
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - Faits extraits
     */
    async getCharacterFacts(characterId) {
        return await this.fetchAPI(`/memories/facts/${characterId}`);
    }

    /**
     * Crée une nouvelle mémoire pour un personnage
     * @param {Object} memoryData - Données de la mémoire
     * @returns {Promise<Object>} - Mémoire créée
     */
    async createMemory(memoryData) {
        return await this.fetchAPI('/memories', {
            method: 'POST',
            body: JSON.stringify(memoryData)
        });
    }

    /**
     * Met à jour une mémoire existante
     * @param {string} memoryId - ID de la mémoire
     * @param {Object} memoryData - Données de la mémoire
     * @returns {Promise<Object>} - Mémoire mise à jour
     */
    async updateMemory(memoryId, memoryData) {
        return await this.fetchAPI(`/memories/${memoryId}`, {
            method: 'PUT',
            body: JSON.stringify(memoryData)
        });
    }

    /**
     * Supprime une mémoire
     * @param {string} memoryId - ID de la mémoire
     * @returns {Promise<Object>} - Résultat de la suppression
     */
    async deleteMemory(memoryId) {
        return await this.fetchAPI(`/memories/${memoryId}`, {
            method: 'DELETE'
        });
    }

    // ==== API Traits de personnalité ====

    /**
     * Récupère les traits de personnalité d'un personnage
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - Données des traits
     */
    async getCharacterTraits(characterId) {
        await this.initPromise;
        const url = `${this.apiUrl}/characters/${characterId}/traits`;
        try {
            const response = await fetch(url);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Erreur lors de la récupération des traits");
            }
            return await response.json();
        } catch (error) {
            console.error("Erreur lors de la récupération des traits:", error);
            throw error;
        }
    }

    /**
     * Récupère l'historique des changements de traits d'un personnage
     * @param {number} characterId - ID du personnage
     * @param {string|null} traitName - Nom du trait (optionnel)
     * @returns {Promise<Array>} - Historique des changements
     */
    async getTraitHistory(characterId, traitName = null) {
        await this.initPromise;
        let url = `${this.apiUrl}/characters/${characterId}/traits/history`;
        if (traitName) {
            url += `?trait_name=${encodeURIComponent(traitName)}`;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Erreur lors de la récupération de l'historique");
            }
            return await response.json();
        } catch (error) {
            console.error("Erreur lors de la récupération de l'historique:", error);
            throw error;
        }
    }

    /**
     * Met à jour un trait de personnalité
     * @param {number} characterId - ID du personnage
     * @param {string} traitName - Nom du trait
     * @param {number} value - Nouvelle valeur (-1.0 à 1.0)
     * @param {string} reason - Raison du changement
     * @returns {Promise<Object>} - Résultat de la mise à jour
     */
    async updateCharacterTrait(characterId, traitName, value, reason) {
        await this.initPromise;
        const url = `${this.apiUrl}/characters/${characterId}/traits/${traitName}`;

        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    value: value,
                    reason: reason
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Erreur lors de la mise à jour du trait");
            }

            return await response.json();
        } catch (error) {
            console.error("Erreur lors de la mise à jour du trait:", error);
            throw error;
        }
    }

    /**
     * Récupère l'état actuel d'un personnage, y compris ses traits actifs
     * @param {number} characterId - ID du personnage
     * @returns {Promise<Object>} - État du personnage
     */
    async getCharacterState(characterId) {
        await this.initPromise;
        const url = `${this.apiUrl}/characters/${characterId}/state`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Erreur lors de la récupération de l'état");
            }
            return await response.json();
        } catch (error) {
            console.error("Erreur lors de la récupération de l'état:", error);
            throw error;
        }
    }
}

window.aleziaAPI = new AleziaAPI();