/**
 * Module pour interagir avec l'API de mémoire du système Alezia AI
 */
class MemoryAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl || '';
        this.apiEndpoint = `${this.baseUrl}/memory`;
    }

    /**
     * Récupère les mémoires d'un personnage
     * @param {Number} characterId - ID du personnage
     * @param {Number} limit - Nombre maximum de mémoires à récupérer
     * @returns {Promise<Array>} - Liste des mémoires
     */
    async getCharacterMemories(characterId, limit = 100) {
        try {
            const response = await fetch(`${this.apiEndpoint}/character/${characterId}/memories?limit=${limit}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la récupération des mémoires');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération des mémoires:', error);
            throw error;
        }
    }

    /**
     * Récupère les faits extraits des mémoires d'un personnage
     * @param {Number} characterId - ID du personnage
     * @param {String} subject - Filtrer par sujet (optionnel)
     * @returns {Promise<Array>} - Liste des faits
     */
    async getCharacterFacts(characterId, subject = null) {
        try {
            let url = `${this.apiEndpoint}/character/${characterId}/facts`;
            if (subject) {
                url += `?subject=${encodeURIComponent(subject)}`;
            }

            const response = await fetch(url);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la récupération des faits');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération des faits:', error);
            throw error;
        }
    }

    /**
     * Crée une nouvelle mémoire pour un personnage
     * @param {Number} characterId - ID du personnage
     * @param {Object} memory - Objet mémoire à créer
     * @returns {Promise<Object>} - Résultat de l'opération
     */
    async createMemory(characterId, memory) {
        try {
            const response = await fetch(`${this.apiEndpoint}/character/${characterId}/memories`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ...memory, character_id: characterId })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la création de la mémoire');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la création de la mémoire:', error);
            throw error;
        }
    }

    /**
     * Récupère une mémoire spécifique
     * @param {Number} memoryId - ID de la mémoire
     * @returns {Promise<Object>} - Détails de la mémoire
     */
    async getMemory(memoryId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/memories/${memoryId}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la récupération de la mémoire');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération de la mémoire:', error);
            throw error;
        }
    }

    /**
     * Met à jour l'importance d'une mémoire
     * @param {Number} memoryId - ID de la mémoire
     * @param {Number} importance - Nouvelle valeur d'importance (0-10)
     * @returns {Promise<Object>} - Résultat de l'opération
     */
    async updateMemoryImportance(memoryId, importance) {
        try {
            const response = await fetch(`${this.apiEndpoint}/memories/${memoryId}/importance`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ importance })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la mise à jour de l\'importance');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la mise à jour de l\'importance:', error);
            throw error;
        }
    }

    /**
     * Supprime une mémoire
     * @param {Number} memoryId - ID de la mémoire à supprimer
     * @returns {Promise<Object>} - Résultat de l'opération
     */
    async deleteMemory(memoryId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/memories/${memoryId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la suppression de la mémoire');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la suppression de la mémoire:', error);
            throw error;
        }
    }

    /**
     * Exécute un cycle de maintenance sur les mémoires d'un personnage
     * @param {Number} characterId - ID du personnage
     * @returns {Promise<Object>} - Statistiques de la maintenance
     */
    async runMemoryMaintenance(characterId) {
        try {
            const response = await fetch(`${this.apiEndpoint}/character/${characterId}/maintenance`, {
                method: 'POST'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la maintenance des mémoires');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la maintenance des mémoires:', error);
            throw error;
        }
    }

    /**
     * Récupère les mémoires les plus pertinentes pour une requête
     * @param {Number} characterId - ID du personnage
     * @param {String} query - Texte de la requête
     * @param {Object} options - Options supplémentaires (limit, recency_weight, importance_weight)
     * @returns {Promise<Array>} - Liste des mémoires pertinentes
     */
    async getRelevantMemories(characterId, query, options = {}) {
        try {
            const { limit = 5, recencyWeight = 0.3, importanceWeight = 0.4 } = options;

            const url = new URL(`${this.apiEndpoint}/character/${characterId}/relevant`);
            url.searchParams.append('query', query);
            url.searchParams.append('limit', limit);
            url.searchParams.append('recency_weight', recencyWeight);
            url.searchParams.append('importance_weight', importanceWeight);

            const response = await fetch(url);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erreur lors de la récupération des mémoires pertinentes');
            }

            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération des mémoires pertinentes:', error);
            throw error;
        }
    }
}

// Création d'une instance globale
window.memoryAPI = new MemoryAPI();