// script.js (The Masterpiece Magic)

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

    // --- State Management: Keep track of where the user is ---
    let state = {
        view: 'competitions', // Can be 'competitions', 'fixtures', or 'details'
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

    // --- Rendering Functions: Build the HTML content ---
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
            card.dataset.id = fixture.id;
            // Store data needed for the details view
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
        updateHeader('AI-Powered Match Analysis');
        
        const view = detailsViewTemplate.content.cloneNode(true).children[0];
        view.querySelector('#details-home-logo').src = state.currentMatchData.homeTeamLogo;
        view.querySelector('#details-home-name').textContent = state.currentMatchData.homeTeamName;
        view.querySelector('#details-away-logo').src = state.currentMatchData.awayTeamLogo;
        view.querySelector('#details-away-name').textContent = state.currentMatchData.awayTeamName;

        // Use innerHTML to render bold/italic tags from AI if any
        view.querySelector('#prediction-content').innerHTML = details.prediction.replace(/\n/g, '<br>');
        view.querySelector('#news-content').innerHTML = details.newsSummary.replace(/\n/g, '<br>');

        contentArea.appendChild(view);
        contentArea.classList.add('fade-in');
    }

    // --- Navigation and Event Handling ---
    async function navigate(event) {
        const target = event.target.closest('[data-id]');
        if (!target) return;

        const id = target.dataset.id;
        if (target.classList.contains('competition-card')) {
            state.view = 'fixtures';
            state.currentCompetitionId = id;
            const competitionName = target.querySelector('.competition-name').textContent;
            const fixtures = await fetchData(`/api/fixtures?id=${id}`);
            if (fixtures) renderFixtures(fixtures, competitionName);
        } else if (target.classList.contains('fixture-card')) {
            state.view = 'details';
            state.currentMatchData = target.dataset;
            const details = await fetchData(`/api/details?id=${id}`);
            if (details) renderDetails(details);
        }
    }

    function handleBackClick() {
        if (state.view === 'details') {
            state.view = 'fixtures';
            // Re-fetch fixtures for the current competition
            const card = document.querySelector(`[data-id="${state.currentCompetitionId}"]`);
            const competitionName = "Previous Competition"; // Placeholder
            fetchData(`/api/fixtures?id=${state.currentCompetitionId}`).then(fixtures => {
                if(fixtures) renderFixtures(fixtures, competitionName);
            });
        } else if (state.view === 'fixtures') {
            state.view = 'competitions';
            init(); // Go back to the main competition list
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
    contentArea.addEventListener('click', navigate);
    backButton.addEventListener('click', handleBackClick);

    // --- Start the App ---
    init();
});