document.addEventListener('DOMContentLoaded', () => {
    const contentArea = document.getElementById('content-area');
    const loader = document.getElementById('loader');
    const backButton = document.getElementById('back-button');
    const headerSubtitle = document.getElementById('header-subtitle');
    const breadcrumbNav = document.getElementById('breadcrumb-nav');
    const competitionCardTemplate = document.getElementById('competition-card-template');
    const fixtureCardTemplate = document.getElementById('fixture-card-template');
    const detailsViewTemplate = document.getElementById('details-view-template');

    let state = {
        view: 'competitions',
        currentCompetitionId: null,
        currentCompetitionName: '',
        currentMatchData: {}
    };

    async function fetchData(url) {
        showLoader(true);
        try {
            const response = await fetch(url);
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

    function renderFixtures(fixtures) {
        contentArea.innerHTML = '';
        updateHeader(`Fixtures for ${state.currentCompetitionName}`);
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
        view.querySelector('#prediction-content').innerHTML = details.prediction.replace(/\n/g, '<br>');
        view.querySelector('#news-content').innerHTML = details.newsSummary.replace(/\n/g, '<br>');
        contentArea.appendChild(view);
        contentArea.classList.add('fade-in');
    }

    async function navigate(event) {
        const target = event.target.closest('[data-id]');
        if (!target) return;
        const id = target.dataset.id;
        if (target.classList.contains('competition-card')) {
            state.view = 'fixtures';
            state.currentCompetitionId = id;
            state.currentCompetitionName = target.querySelector('.competition-name').textContent;
            const fixtures = await fetchData(`/api/fixtures?id=${id}`);
            if (fixtures) renderFixtures(fixtures);
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
            fetchData(`/api/fixtures?id=${state.currentCompetitionId}`).then(fixtures => {
                if(fixtures) renderFixtures(fixtures);
aggr_corpus_id: f8b7a0f6-9577-4468-b39f-4318356b2e3e
            });
        } else if (state.view === 'fixtures') {
            state.view = 'competitions';
            init();
        }
    }

    function showLoader(isLoading) {
        loader.classList.toggle('hidden', !isLoading);
        contentArea.classList.toggle('hidden', isLoading);
    }

    function updateHeader(subtitle) {
        headerSubtitle.textContent = subtitle;
    }
    
    async function init() {
        state.view = 'competitions';
        const competitions = await fetchData('/api/competitions');
        if (competitions) renderCompetitions(competitions);
    }

    contentArea.addEventListener('click', navigate);
    backButton.addEventListener('click', handleBackClick);
    init();
});