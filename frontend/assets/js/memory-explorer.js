/**
 * Module pour l'exploration et la visualisation des mémoires d'un personnage
 */
class MemoryExplorer {
    constructor() {
        this.currentCharacterId = null;
        this.memories = [];
        this.facts = [];
        this.filters = {
            importance: 0,
            type: 'all',
            search: ''
        };
    }

    /**
     * Initialise l'explorateur de mémoires pour un personnage
     * @param {Number} characterId - ID du personnage
     * @param {HTMLElement} container - Conteneur pour afficher l'explorateur
     */
    async initialize(characterId, container) {
        this.currentCharacterId = characterId;
        this.container = container;

        // Créer l'interface
        this._createInterface();

        // Charger les données initiales
        await this.loadData();
    }

    /**
     * Charge les mémoires et les faits du personnage
     */
    async loadData() {
        try {
            if (!this.currentCharacterId) return;

            // Afficher un indicateur de chargement
            this.memoryContainer.innerHTML = '<div class="loading">Chargement des mémoires...</div>';
            this.factContainer.innerHTML = '<div class="loading">Chargement des faits...</div>';

            // Charger les mémoires et les faits en parallèle
            const [memories, facts] = await Promise.all([
                memoryAPI.getCharacterMemories(this.currentCharacterId),
                memoryAPI.getCharacterFacts(this.currentCharacterId)
            ]);

            this.memories = memories;
            this.facts = facts;

            // Afficher les données
            this._renderMemories();
            this._renderFacts();
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
            this.memoryContainer.innerHTML = '<div class="error">Erreur lors du chargement des mémoires</div>';
            this.factContainer.innerHTML = '<div class="error">Erreur lors du chargement des faits</div>';
        }
    }

    /**
     * Crée l'interface utilisateur de l'explorateur
     */
    _createInterface() {
        // Créer la structure de base
        this.container.innerHTML = `
            <div class="memory-explorer">
                <div class="explorer-header">
                    <h2>Explorateur de mémoires</h2>
                    <div class="explorer-controls">
                        <div class="search-box">
                            <input type="text" id="memory-search" placeholder="Rechercher..." />
                            <button id="search-button">🔍</button>
                        </div>
                        <div class="filter-controls">
                            <label>
                                Importance min:
                                <input type="range" id="importance-filter" min="0" max="10" step="0.5" value="0" />
                                <span id="importance-value">0</span>
                            </label>
                            <select id="type-filter">
                                <option value="all">Tous les types</option>
                                <option value="conversation">Conversation</option>
                                <option value="event">Événement</option>
                                <option value="observation">Observation</option>
                                <option value="reflection">Réflexion</option>
                            </select>
                            <button id="refresh-button">↻</button>
                            <button id="maintenance-button">🔧</button>
                        </div>
                    </div>
                </div>
                <div class="explorer-content">
                    <div class="memories-container">
                        <h3>Mémoires <span id="memory-count"></span></h3>
                        <div id="memories-list" class="list-container"></div>
                    </div>
                    <div class="facts-container">
                        <h3>Faits extraits <span id="fact-count"></span></h3>
                        <div id="facts-list" class="list-container"></div>
                    </div>
                </div>
            </div>
        `;

        // Récupérer les références aux éléments
        this.memoryContainer = this.container.querySelector('#memories-list');
        this.factContainer = this.container.querySelector('#facts-list');
        this.searchInput = this.container.querySelector('#memory-search');
        this.importanceFilter = this.container.querySelector('#importance-filter');
        this.importanceValue = this.container.querySelector('#importance-value');
        this.typeFilter = this.container.querySelector('#type-filter');
        this.refreshButton = this.container.querySelector('#refresh-button');
        this.maintenanceButton = this.container.querySelector('#maintenance-button');
        this.memoryCount = this.container.querySelector('#memory-count');
        this.factCount = this.container.querySelector('#fact-count');

        // Ajouter les écouteurs d'événements
        this._setupEventListeners();
    }

    /**
     * Configure les écouteurs d'événements pour l'interface utilisateur
     */
    _setupEventListeners() {
        // Filtrage par recherche
        this.searchInput.addEventListener('input', () => {
            this.filters.search = this.searchInput.value.toLowerCase();
            this._renderMemories();
        });

        // Filtrage par importance
        this.importanceFilter.addEventListener('input', () => {
            this.filters.importance = parseFloat(this.importanceFilter.value);
            this.importanceValue.textContent = this.filters.importance;
            this._renderMemories();
        });

        // Filtrage par type
        this.typeFilter.addEventListener('change', () => {
            this.filters.type = this.typeFilter.value;
            this._renderMemories();
        });

        // Bouton de rafraîchissement
        this.refreshButton.addEventListener('click', () => {
            this.loadData();
        });

        // Bouton de maintenance
        this.maintenanceButton.addEventListener('click', async () => {
            try {
                this.maintenanceButton.disabled = true;
                this.maintenanceButton.textContent = '⏳';

                const result = await memoryAPI.runMemoryMaintenance(this.currentCharacterId);

                alert(`Maintenance terminée:\n- ${result.statistics.decayed_memories} mémoires dégradées\n- ${result.statistics.consolidated_memories} mémoires consolidées`);

                // Recharger les données
                await this.loadData();
            } catch (error) {
                console.error('Erreur lors de la maintenance:', error);
                alert('Erreur lors de la maintenance');
            } finally {
                this.maintenanceButton.disabled = false;
                this.maintenanceButton.textContent = '🔧';
            }
        });
    }

    /**
     * Affiche les mémoires filtrées dans l'interface
     */
    _renderMemories() {
        if (!this.memories.length) {
            this.memoryContainer.innerHTML = '<div class="empty">Aucune mémoire trouvée</div>';
            this.memoryCount.textContent = '(0)';
            return;
        }

        // Filtrer les mémoires
        const filteredMemories = this.memories.filter(memory => {
            // Filtre par importance
            if (memory.importance < this.filters.importance) {
                return false;
            }

            // Filtre par type
            if (this.filters.type !== 'all' && memory.memory_type !== this.filters.type) {
                return false;
            }

            // Filtre par recherche
            if (this.filters.search && !memory.content.toLowerCase().includes(this.filters.search)) {
                return false;
            }

            return true;
        });

        // Mettre à jour le compteur
        this.memoryCount.textContent = `(${filteredMemories.length}/${this.memories.length})`;

        if (!filteredMemories.length) {
            this.memoryContainer.innerHTML = '<div class="empty">Aucune mémoire ne correspond aux filtres</div>';
            return;
        }

        // Trier par date (plus récente d'abord) et importance
        filteredMemories.sort((a, b) => {
            if (b.importance !== a.importance) {
                return b.importance - a.importance;
            }
            return new Date(b.created_at) - new Date(a.created_at);
        });

        // Générer le HTML
        const html = filteredMemories.map(memory => {
            const date = new Date(memory.created_at).toLocaleString();
            const importanceClass = this._getImportanceClass(memory.importance);

            return `
                <div class="memory-item ${importanceClass}" data-id="${memory.id}">
                    <div class="memory-header">
                        <span class="memory-type">${memory.memory_type}</span>
                        <span class="memory-date">${date}</span>
                        <span class="memory-importance" title="Importance: ${memory.importance.toFixed(1)}">
                            ${this._getImportanceStars(memory.importance)}
                        </span>
                    </div>
                    <div class="memory-content">${this._formatContent(memory.content)}</div>
                    <div class="memory-actions">
                        <button class="edit-importance" data-id="${memory.id}">Ajuster importance</button>
                        <button class="delete-memory" data-id="${memory.id}">Supprimer</button>
                    </div>
                </div>
            `;
        }).join('');

        this.memoryContainer.innerHTML = html;

        // Ajouter les gestionnaires d'événements pour les boutons
        this.memoryContainer.querySelectorAll('.edit-importance').forEach(button => {
            button.addEventListener('click', async (e) => {
                const memoryId = parseInt(e.target.dataset.id);
                const memory = this.memories.find(m => m.id === memoryId);

                const newImportance = parseFloat(prompt(`Nouvelle importance (0-10):`, memory.importance));

                if (isNaN(newImportance) || newImportance < 0 || newImportance > 10) {
                    alert('Importance invalide. Veuillez saisir une valeur entre 0 et 10.');
                    return;
                }

                try {
                    await memoryAPI.updateMemoryImportance(memoryId, newImportance);

                    // Mettre à jour la mémoire localement
                    memory.importance = newImportance;
                    this._renderMemories();
                } catch (error) {
                    console.error('Erreur lors de la mise à jour de l\'importance:', error);
                    alert('Erreur lors de la mise à jour');
                }
            });
        });

        this.memoryContainer.querySelectorAll('.delete-memory').forEach(button => {
            button.addEventListener('click', async (e) => {
                const memoryId = parseInt(e.target.dataset.id);

                if (!confirm('Êtes-vous sûr de vouloir supprimer cette mémoire ?')) {
                    return;
                }

                try {
                    await memoryAPI.deleteMemory(memoryId);

                    // Supprimer la mémoire localement
                    const index = this.memories.findIndex(m => m.id === memoryId);
                    if (index !== -1) {
                        this.memories.splice(index, 1);
                    }

                    this._renderMemories();

                    // Rafraîchir les faits car ils peuvent avoir été affectés
                    const facts = await memoryAPI.getCharacterFacts(this.currentCharacterId);
                    this.facts = facts;
                    this._renderFacts();
                } catch (error) {
                    console.error('Erreur lors de la suppression:', error);
                    alert('Erreur lors de la suppression');
                }
            });
        });
    }

    /**
     * Affiche les faits extraits dans l'interface
     */
    _renderFacts() {
        if (!this.facts.length) {
            this.factContainer.innerHTML = '<div class="empty">Aucun fait extrait</div>';
            this.factCount.textContent = '(0)';
            return;
        }

        // Mettre à jour le compteur
        this.factCount.textContent = `(${this.facts.length})`;

        // Organiser les faits par sujet
        const factsBySubject = {};

        this.facts.forEach(fact => {
            if (!factsBySubject[fact.subject]) {
                factsBySubject[fact.subject] = [];
            }
            factsBySubject[fact.subject].push(fact);
        });

        // Générer le HTML
        let html = '';

        for (const subject in factsBySubject) {
            const facts = factsBySubject[subject];

            html += `
                <div class="subject-group">
                    <h4 class="subject-header">${subject}</h4>
                    <div class="facts-list">
            `;

            facts.forEach(fact => {
                const confidenceClass = this._getConfidenceClass(fact.confidence);
                const confidenceStars = this._getConfidenceStars(fact.confidence);

                html += `
                    <div class="fact-item ${confidenceClass}" data-id="${fact.id}">
                        <div class="fact-relation">
                            <span class="fact-predicate">${fact.predicate}</span>
                            <span class="fact-object">${fact.object}</span>
                            <span class="fact-confidence" title="Confiance: ${(fact.confidence * 100).toFixed(0)}%">
                                ${confidenceStars}
                            </span>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        this.factContainer.innerHTML = html;
    }

    /**
     * Formate le contenu textuel avec mise en évidence des termes recherchés
     */
    _formatContent(content) {
        if (!this.filters.search) {
            return content;
        }

        const regex = new RegExp(`(${this.filters.search})`, 'gi');
        return content.replace(regex, '<mark>$1</mark>');
    }

    /**
     * Retourne la classe CSS en fonction de l'importance
     */
    _getImportanceClass(importance) {
        if (importance >= 8) return 'high-importance';
        if (importance >= 5) return 'medium-importance';
        if (importance >= 2) return 'low-importance';
        return 'very-low-importance';
    }

    /**
     * Retourne des étoiles représentant l'importance
     */
    _getImportanceStars(importance) {
        const fullStars = Math.floor(importance / 2);
        const halfStar = importance % 2 >= 1;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);

        return '★'.repeat(fullStars) + (halfStar ? '⯪' : '') + '☆'.repeat(emptyStars);
    }

    /**
     * Retourne la classe CSS en fonction du niveau de confiance
     */
    _getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'high-confidence';
        if (confidence >= 0.5) return 'medium-confidence';
        return 'low-confidence';
    }

    /**
     * Retourne des étoiles représentant le niveau de confiance
     */
    _getConfidenceStars(confidence) {
        const stars = Math.ceil(confidence * 5);
        return '★'.repeat(stars) + '☆'.repeat(5 - stars);
    }
}

// Création d'une instance globale
window.memoryExplorer = new MemoryExplorer();