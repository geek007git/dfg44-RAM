document.addEventListener('DOMContentLoaded', () => {
    const commissionsContainer = document.getElementById('commissions-container');

    const fetchCommissions = async () => {
        try {
            const response = await fetch('/api/commissions');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const commissions = await response.json();
            renderCommissions(commissions);
        } catch (error) {
            console.error('Error fetching data:', error);
            commissionsContainer.innerHTML = `<div class="loading-state">Failed to load commissions. Please try again later.</div>`;
        }
    };

    const renderCommissions = (commissions) => {
        if (!commissions || commissions.length === 0) {
            commissionsContainer.innerHTML = '<div class="loading-state">No commissions available at the moment.</div>';
            return;
        }

        commissionsContainer.innerHTML = '';

        commissions.forEach(commission => {
            const card = document.createElement('div');
            card.classList.add('commission-card');

            // Format Description (Handling line breaks if any)
            const formattedDescription = commission.description.replace(/\n/g, '<br/>');

            // Link to the detail page
            const detailUrl = `/commission/${commission.id}`;

            card.innerHTML = `
                <div class="card-header">
                    <div class="title-section">
                        <span class="category-tag">${commission.category}</span>
                        <h2 class="card-title">${commission.title}</h2>
                    </div>
                    <div class="company-logo">LS.</div>
                </div>
                <div class="card-body">
                    <p class="description">${formattedDescription}</p>
                </div>
                <div class="card-footer">
                    <span class="posted-date">Posted Today</span>
                    <a href="${detailUrl}" class="apply-btn">Apply Now</a>
                </div>
            `;

            // Make the whole card clickable for better UX
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking the button directly (to avoid double event, though href handles it)
                if (e.target.tagName !== 'A') {
                    window.location.href = detailUrl;
                }
            });
            card.style.cursor = 'pointer';

            commissionsContainer.appendChild(card);
        });
    };

    fetchCommissions();
});
