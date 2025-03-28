/**
 * Service API pour communiquer avec le backend
 */

// Configuration de base
const API_URL = 'http://localhost:8000';

/**
 * Service pour les appels API
 */
class ApiService {
    /**
     * Effectue une requête API
     * @param {string} endpoint - Point d'API
     * @param {string} method - Méthode HTTP
     * @param {object} body - Corps de la requête
     * @returns {Promise<any>} - Réponse de l'API
     */
    async request(endpoint, method = 'GET', body = null) {
        const url = `${API_URL}${endpoint}`;

        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            // Vérifier si la réponse est au format JSON
            const contentType = response.headers.get('content-type');

            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();

                if (!response.ok) {
                    // En cas d'erreur avec un message d'erreur du serveur
                    throw new Error(data.detail || `Erreur API: ${response.status}`);
                }

                return data;
            } else {
                // En cas de réponse non-JSON
                if (!response.ok) {
                    throw new Error(`Erreur API: ${response.status}`);
                }

                return await response.text();
            }
        } catch (error) {
            console.error(`Erreur API (${url}):`, error);
            throw error;
        }
    }

    // API Personnages

    /**
     * Récupère tous les personnages
     * @returns {Promise<Array>} - Liste des personnages
     */
    async getCharacters() {
        return this.request('/characters');
    }

    /**
     * Récupère un personnage par son ID
     * @param {number} id - ID du personnage
     * @returns {Promise<object>} - Données du personnage
     */
    async getCharacter(id) {
        return this.request(`/characters/${id}`);
    }

    /**
     * Crée un nouveau personnage
     * @param {object} character - Données du personnage
     * @returns {Promise<object>} - Résultat de la création
     */
    async createCharacter(character) {
        return this.request('/characters', 'POST', character);
    }

    /**
     * Supprime un personnage
     * @param {number} id - ID du personnage
     * @returns {Promise<object>} - Résultat de la suppression
     */
    async deleteCharacter(id) {
        return this.request(`/characters/${id}`, 'DELETE');
    }

    // API Système

    /**
     * Vérifie l'état de la base de données
     * @returns {Promise<object>} - État de la base de données
     */
    async checkDatabase() {
        return this.request('/system/check-database');
    }

    /**
     * Vérifie l'état du service LLM
     * @returns {Promise<object>} - État du service LLM
     */
    async checkLLM() {
        return this.request('/system/check-llm');
    }
}

// Exporter une instance unique du service
export const apiService = new ApiService();