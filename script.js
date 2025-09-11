// script.js

// --- DOM Elements ---
// Getting references to the important parts of our HTML
const contentArea = document.getElementById('content-area');
const loader = document.getElementById('loader');
const backButton = document.getElementById('back-button');
const headerSubtitle = document.getElementById('header-subtitle');

// --- Templates ---
// Getting references to our hidden HTML blueprints
const competitionCardTemplate = document.getElementById('competition-card-template');
const fixtureCardTemplate = document.getElementById('fixture-card-template');
const detailsViewTemplate = document.getElementById('details-view-template');

// --- State Management ---
// A simple way to remember the current match for the details view
let currentMatchData = {};

// --- API Fetching Logic ---
// Generic function to fetch data from our Python backend
async function fetchData(url) {
    showLoader(true);
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        contentArea.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        return null;
    } finally {
        showLoader(false);
    }
}

// --- Rendering Functions ---
// These functions build the HTML from the data

function renderCompetitions(competitions) {
    contentArea.innerHTML = ''; // Clear previous content
    headerSubtitle.textContent = 'Select a competition to see upcoming fixtures.';
    backButton.classList.add('hidden');

    competitions.forEach(comp => {
        // We only show competitions that have an emblem
        if (!comp.emblem) return;

        const card = competitionCardTemplate.content.cloneNode(true).children[0];
        card.querySelector('.competition-logo').src = comp.emblem;
        card.querySelector('.competition-name').textContent = comp.name;
        card.querySelector('.competition-country').textContent = comp.area.name;
        card.dataset.id = comp.id; // Store the ID for the click event
        contentArea.appendChild(card);
    });
    contentArea.classList.add('fade-in');
}

function renderFixtures(fixtures) {
    contentArea.innerHTML = '';
    headerSubtitle.textContent = 'Select a fixture to see details and predictions.';
    backButton.classList.remove('hidden');

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
        // Store the fixture data for the details view
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

    // Populate the header with data we saved earlier
    view.querySelector('#details-home-logo').src = currentMatchData.homeTeamLogo;
    view.querySelector('#details-home-name').textContent = currentMatchData.homeTeamName;
    view.querySelector('#details-away-logo').src = currentMatchData.awayTeamLogo;
    view.querySelector('#details-away-name').textContent = currentMatchData.awayTeamName;

    // Populate the AI prediction and News
    view.querySelector('#prediction-content').textContent = details.prediction;
    
    const newsContent = view.querySelector('#news-content');
    if (details.news && details.news.length > 0) {
        details.news.forEach(item => {
            const link = document.createElement('a');
            link.href = item.url;
            link.textContent = item.title;
            link.target = '_blank'; // Open in a new tab
            newsContent.appendChild(link);
        });
    } else {
        newsContent.textContent = 'No recent news found.';
    }

    contentArea.appendChild(view);
    contentArea.classList.add('fade-in');
}

// --- Event Handling ---
// This function handles all clicks

async function handleCardClick(event) {
    const card = event.target.closest('.card');
    if (!card) return;

    if (card.classList.contains('competition-card')) {
        const competitionId = card.dataset.id;
        const fixtures = await fetchData(`/api/fixtures?id=${competitionId}`);
        if (fixtures) {
            renderFixtures(fixtures);
        }
    } else if (card.classList.contains('fixture-card')) {
        const matchId = card.dataset.id;
        // Save the team names and logos for the details view
        currentMatchData = card.dataset;
        const details = await fetchData(`/api/details?id=${matchId}`);
        if (details) {
            renderDetails(details);
        }
    }
}

// --- Utility Functions ---
function showLoader(isLoading) {
    if (isLoading) {
        contentArea.innerHTML = ''; // Clear content when loading starts
        loader.classList.remove('hidden');
    } else {
        loader.classList.add('hidden');
    }
}

// --- Initial Load ---
// This is what starts the whole app
async function init() {
    const competitions = await fetchData('/api/competitions');
    if (competitions) {
        renderCompetitions(competitions);
    }
}

// --- Event Listeners ---
// Listen for clicks on the main content area and the back button
contentArea.addEventListener('click', handleCardClick);
backButton.addEventListener('click', init);

// Start the app when the page loads
document.addEventListener('DOMContentLoaded', init);