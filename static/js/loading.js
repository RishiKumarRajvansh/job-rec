// Global loading indicator functions
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');

function showLoading(message = 'Loading...') {
    loadingMessage.textContent = message;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// Add loading indicators for various actions
document.addEventListener('DOMContentLoaded', function() {
    // Job search form
    const searchForm = document.getElementById('job-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            showLoading('Finding relevant jobs...');
        });
    }

    // Resume upload form
    const resumeForm = document.getElementById('resume-upload-form');
    if (resumeForm) {
        resumeForm.addEventListener('submit', function() {
            showLoading('Analyzing resume...');
        });
    }

    // Job scraping
    const scrapeButton = document.getElementById('scrape-jobs');
    if (scrapeButton) {
        scrapeButton.addEventListener('click', function() {
            showLoading('Gathering latest job postings...');
            // Hide loading when scraping is done
            fetch('/run_scraper_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: document.getElementById('query').value || 'All',
                    location: document.getElementById('location').value || 'All'
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error running scraper: ' + data.error);
                }
            })
            .catch(error => {
                hideLoading();
                alert('Error: ' + error);
            });
        });
    }

    // Show loading on form submits
    document.addEventListener('submit', function(e) {
        const form = e.target;
        // Don't show loading for forms with data-no-loading attribute
        if (!form.hasAttribute('data-no-loading')) {
            showLoading('Processing your request...');
        }
    });

    // Show loading when refreshing jobs
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="refresh-jobs"]')) {
            showLoading('Refreshing job listings...');
        } else if (e.target.matches('[data-action="refresh-courses"]')) {
            showLoading('Refreshing course recommendations...');
        }
    });
});
