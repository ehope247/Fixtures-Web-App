// script.js (Final Version for the Statistical Model)

document.addEventListener('DOMContentLoaded', () => {
    // --- Get references to all the important HTML elements ---
    const contentArea = document.getElementById('content-area');
    const loader = document.getElementById('loader');
    const backButton = document.getElementById('back-button');
    const headerSubtitle = document.getElementById('header-subtitle');
    const breadcrumbNav = document.getElementById('breadcrumb-nav');

    // --- Get references to the HTML templates ---
    const competitionCardTemplate = document.getElementById('competition-card-template');
    const fixtureCardTemplate = document.getElementById('fixture-card-template');
    const detailsViewTemplate = document.getElementById('details-view-template');

    // --- State Management ---
    let state = {
        view: 'competitions',
        currentCompetitionId: null,
        currentMatchData: {}
    };

    // --- API Fetching ---
    async function fetchData(url, options = {}) {
        showLoader(true);
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            contentArea.innerHTML = `<p class="error-message">Error: ${error.message}</p>`;
            return null;
        } finally {
            showLoader(false);
        }
    }

    // --- Rendering Functions ---
    function renderCompetitions(competitions) {
        contentArea.innerHTML = '';
        updateHeader('Select a Competition to Begin');
        breadcrumbNav.classList.add('hidden');
        competitions.forEach(comp => {
            if (!comp.emblem) return;
            const card = competitionCardTemplate.content.cloneNode(true).children[0];
            card.querySelector('.competition-logo').src = comp.emblem;
            card.querySelector('.competition-name').textContent = comp.name;
            card.querySelector('.competition-country').textContent = comp.area.name;
            card.dataset.id = comp.id;
            contentArea.appendChild(card);
        });
        contentArea.classList.add('fade-in');
    }

    function renderFixtures(fixtures, competitionName) {
        contentArea.innerHTML = '';
        updateHeader(`Fixtures for ${competitionName}`);
        breadcrumbNav.classList.remove('hidden');
        if (fixtures.length === 0) {
            contentArea.innerHTML = '<p class="info-message">No scheduled fixtures found for the next 3 days.</p>';
            return;
        }
        fixtures.forEach(fixture => {
            const card = fixtureCardTemplate.content.cloneNode(true).children[0];
            card.querySelector('.home-team .team-logo').src = fixture.homeTeam.crest;
            card.querySelector('.home-team .team-name').textContent = fixture.homeTeam.shortName;
            card.querySelector('.match-time').textContent = fixture.utcDate.split('T')[1].slice(0, 5);
            card.querySelector('.away-team .team-logo').src = fixture.awayTeam.crest;
            card.querySelector('.away-team .team-name').textContent = fixture.awayTeam.shortName;
            
            // --- CRITICAL CHANGE ---
            // We now store the team IDs, not just the names and logos
            card.dataset.homeTeamId = fixture.homeTeam.id;
            card.dataset.awayTeamId = fixture.awayTeam.id;
            card.dataset.homeTeamName = fixture.homeTeam.name;
            card.dataset.homeTeamLogo = fixture.homeTeam.crest;
            card.dataset.awayTeamName = fixture.awayTeam.name;
            card.dataset.awayTeamLogo = fixture.awayTeam.crest;

            contentArea.appendChild(card);
        });
        contentArea.classList.add('fade-in');
    }

    function renderDetails(details) {
        contentArea.innerHTML = '';
        updateHeader('Statistical Match Prediction');
        const view = detailsViewTemplate.content.cloneNode(true).children[0];
        view.querySelector('#details-home-logo').src = state.currentMatchData.homeTeamLogo;
        view.querySelector('#details-home-name').textContent = state.currentMatchData.homeTeamName;
        view.querySelector('#details-away-logo').src = state.currentMatchData.awayTeamLogo;
        view.querySelector('#details-away-name').textContent = state.currentMatchData.awayTeamName;

        // Display the direct prediction from our new model
        view.querySelector('#prediction-content').textContent = details.prediction;

        contentArea.appendChild(view);
        contentArea.classList.add('fade-in');
    }

    // --- Event Handling ---
    async function handleCardClick(event) {
        const card = event.target.closest('.card');
        if (!card) return;

        if (card.classList.contains('competition-card')) {
            const competitionId = card.dataset.id;
            state.view = 'fixtures';
            state.currentCompetitionId = competitionId;
            const competitionName = card.querySelector('.competition-name').textContent;
            const fixtures = await fetchData(`/api/fixtures?id=${competitionId}`);
            if (fixtures) renderFixtures(fixtures, competitionName);

        } else if (card.classList.contains('fixture-card')) {
            // --- CRITICAL CHANGE ---
            // We now send the team IDs to our new API endpoint
            const homeId = card.dataset.homeTeamId;
            const awayId = card.dataset.awayTeamId;
            state.view = 'details';
            state.currentMatchData = card.dataset;
            const details = await fetchData(`/api/details?home_id=${homeId}&away_id=${awayId}`);
            if (details) renderDetails(details);
        }
    }

    function handleBackClick() {
        if (state.view === 'details') {
            state.view = 'fixtures';
            const competitionName = "Previous Competition";
            fetchData(`/api/fixtures?id=${state.currentCompetitionId}`).then(fixtures => {
                if (fixtures) renderFixtures(fixtures, competitionName);
            });
        } else if (state.view === 'fixtures') {
            state.view = 'competitions';
            init();
        }
    }
    
    // --- Utility Functions ---
    function showLoader(isLoading) {
        loader.classList.toggle('hidden', !isLoading);
        contentArea.classList.toggle('hidden', isLoading);
    }
    function updateHeader(subtitle) {
        headerSubtitle.textContent = subtitle;
    }
    
    // --- Initializer ---
    async function init() {
        state.view = 'competitions';
        const competitions = await fetchData('/api/competitions');
        if (competitions) renderCompetitions(competitions);
    }

    // --- Attach Event Listeners ---
    contentArea.addEventListener('click', handleCardClick);
    backButton.addEventListener('click', handleBackClick);
    init();
});