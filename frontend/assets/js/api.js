/**
 * Alezia AI - Client API
 * Module pour communiquer avec le backend
 */

class AleziaAPI {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.connected = false;
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
            const response = await fetch(`${this.baseUrl}/llm/status`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                return data.loaded === true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du modèle:', error);
            return false;
        }
    }

    /**
     * Récupère tous les personnages
     * @returns {Promise<Array>} Liste des personnages
     */
    async getCharacters() {
        try {
            const response = await fetch(`${this.baseUrl}/characters`, {
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
            const response = await fetch(`${this.baseUrl}/characters`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(character)
            });

            if (response.ok) {
                return await response.json();
            } else {
                const error = await response.json();
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
            const response = await fetch(`${this.baseUrl}/universes`, {
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
            const response = await fetch(`${this.baseUrl}/chat/${sessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: message })
            });

            if (response.ok) {
                return await response.json();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Impossible d\'envoyer le message');
            }
        } catch (error) {
            console.error('Erreur lors de l\'envoi du message:', error);
            throw error;
        }
    }

    /**
     * Crée une nouvelle session de chat
     * @param {number} characterId ID du personnage
     * @returns {Promise<Object>} Session créée
     */
    async createSession(characterId) {
        try {
            const response = await fetch(`${this.baseUrl}/chat/session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ character_id: characterId })
            });

            if (response.ok) {
                return await response.json();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Impossible de créer la session');
            }
        } catch (error) {
            console.error('Erreur lors de la création de la session:', error);
            throw error;
        }
    }

    /**
     * Récupère l'historique d'une session
     * @param {number} sessionId ID de la session
     * @returns {Promise<Array>} Messages de la session
     */
    async getSessionHistory(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/chat/${sessionId}/history`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                return await response.json();
            } else {
                throw new Error('Impossible de récupérer l\'historique');
            }
        } catch (error) {
            console.error('Erreur lors de la récupération de l\'historique:', error);
            return [];
        }
    }
}

// Exporter une instance globale
window.aleziaAPI = new AleziaAPI();