// Loading indicator functions
function showLoading(id) {
    document.getElementById(id).style.display = 'block';
}

function hideLoading(id) {
    document.getElementById(id).style.display = 'none';
}

// Add loading indicators for various actions
document.addEventListener('DOMContentLoaded', function() {
    // Job search form
    const searchForm = document.getElementById('job-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            showLoading('search-loading');
        });
    }

    // Resume upload form
    const resumeForm = document.getElementById('resume-upload-form');
    if (resumeForm) {
        resumeForm.addEventListener('submit', function() {
            showLoading('resume-loading');
        });
    }

    // Job scraping
    const scrapeButton = document.getElementById('scrape-jobs');
    if (scrapeButton) {
        scrapeButton.addEventListener('click', function() {
            showLoading('scrape-loading');
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
                hideLoading('scrape-loading');
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error running scraper: ' + data.error);
                }
            })
            .catch(error => {
                hideLoading('scrape-loading');
                alert('Error: ' + error);
            });
        });
    }
});
