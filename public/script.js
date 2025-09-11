// script.js (Final Version)
const contentArea = document.getElementById('content-area');
const loader = document.getElementById('loader');
const backButton = document.getElementById('back-button');
const headerSubtitle = document.getElementById('header-subtitle');
const competitionCardTemplate = document.getElementById('competition-card-template');
const fixtureCardTemplate = document.getElementById('fixture-card-template');
const detailsViewTemplate = document.getElementById('details-view-template');
let currentMatchData = {};

async function fetchData(url) {
    showLoader(true);
    try {
        const response = await fetch(url);
        if (!response.ok) { throw new Error(`HTTP error! status: ${response.status}`); }
        return await response.json();
    } catch (error) {
        contentArea.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        return null;
    } finally {
        showLoader(false);
    }
}
function renderCompetitions(competitions) {
    contentArea.innerHTML = '';
    headerSubtitle.textContent = 'Select a competition to see upcoming fixtures.';
    backButton.style.display = 'none';
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
    headerSubtitle.textContent = 'Select a fixture to see details and predictions.';
    backButton.style.display = 'block';
    if (fixtures.length === 0) {
        contentArea.innerHTML = '<p>No scheduled fixtures found for the next 3 days.</p>';
        return;
    }
    fixtures.forEach(fixture => {
        const card = fixtureCardTemplate.content.cloneNode(true).children[0];
        card.querySelector('.team-logo:first-of-type').src = fixture.homeTeam.crest;
        card.querySelector('.team-name:first-of-type').textContent = fixture.homeTeam.shortName;
        card.querySelector('.match-time').textContent = fixture.utcDate.split('T')[1].slice(0, 5);
        card.querySelector('.team-logo:last-of-type').src = fixture.awayTeam.crest;
        card.querySelector('.team-name:last-of-type').textContent = fixture.awayTeam.shortName;
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
    headerSubtitle.textContent = 'AI-Powered Match Analysis';
    const view = detailsViewTemplate.content.cloneNode(true).children[0];
    view.querySelector('#details-home-logo').src = currentMatchData.homeTeamLogo;
    view.querySelector('#details-home-name').textContent = currentMatchData.homeTeamName;
    view.querySelector('#details-away-logo').src = currentMatchData.awayTeamLogo;
    view.querySelector('#details-away-name').textContent = currentMatchData.awayTeamName;
    view.querySelector('#prediction-content').textContent = details.prediction;
    const newsContent = view.querySelector('#news-content');
    if (details.news && details.news.length > 0) {
        details.news.forEach(item => {
            const link = document.createElement('a');
            link.href = item.url; link.textContent = item.title; link.target = '_blank';
            newsContent.appendChild(link);
        });
    } else {
        newsContent.textContent = 'No recent news found.';
    }
    contentArea.appendChild(view);
    contentArea.classList.add('fade-in');
}
async function handleCardClick(event) {
    const card = event.target.closest('.card');
    if (!card) return;
    if (card.classList.contains('competition-card')) {
        const competitionId = card.dataset.id;
        const fixtures = await fetchData(`/api/fixtures?id=${competitionId}`);
        if (fixtures) { renderFixtures(fixtures); }
    } else if (card.classList.contains('fixture-card')) {
        const matchId = card.dataset.id;
        currentMatchData = card.dataset;
        const details = await fetchData(`/api/details?id=${matchId}`);
        if (details) { renderDetails(details); }
    }
}
function showLoader(isLoading) {
    if (isLoading) {
        contentArea.innerHTML = '';
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}
async function init() {
    const competitions = await fetchData('/api/competitions');
    if (competitions) { renderCompetitions(competitions); }
}
contentArea.addEventListener('click', handleCardClick);
backButton.addEventListener('click', init);
document.addEventListener('DOMContentLoaded', init);