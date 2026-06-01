// Search functionality
let searchProducts = [];

// Prevent search icon from triggering page transitions
document.addEventListener('DOMContentLoaded', function() {
    const searchIcon = document.getElementById('searchIcon');
    if (searchIcon) {
        searchIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            openSearchModal();
        });
    }
});

function loadSearchProducts() {
    fetch('/api/search_products')
        .then(response => response.json())
        .then(data => {
            searchProducts = data;
        })
        .catch(error => console.error('Error loading products:', error));
}

function openSearchModal() {
    const overlay = document.getElementById('searchOverlay');
    const backdrop = document.getElementById('searchBackdrop');
    if (overlay && backdrop) {
        overlay.classList.add('active');
        backdrop.classList.add('active');
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.focus();
        }
    }
}

function closeSearchModal() {
    const overlay = document.getElementById('searchOverlay');
    const backdrop = document.getElementById('searchBackdrop');
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('searchResults');
    if (overlay) overlay.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
    if (searchInput) searchInput.value = '';
    if (resultsDiv) resultsDiv.innerHTML = '';
}

function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('searchResults');
    
    if (!searchInput || !resultsDiv) return;
    
    const query = searchInput.value.toLowerCase();
    
    if (query.length < 2) {
        resultsDiv.innerHTML = '';
        return;
    }
    
    const results = searchProducts.filter(product => 
        product.name.toLowerCase().includes(query) || 
        (product.description && product.description.toLowerCase().includes(query))
    );
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="no-results">No products found</div>';
        return;
    }
    
    resultsDiv.innerHTML = results.map(product => `
        <div class="search-result-item" onclick="window.location.href='/perfume/${product.id}'">
            <div class="search-result-image">
                <img src="/static/images/${product.image_url || product.name.toLowerCase().replace(/ /g, '-') + '.png'}" alt="${product.name}" onerror="this.src='https://via.placeholder.com/60x60/B9B59F/060644?text='">
            </div>
            <div class="search-result-info">
                <h4>${escapeHtml(product.name)}</h4>
                <p>${product.description ? escapeHtml(product.description.substring(0, 60)) + '...' : 'Premium fragrance'}</p>
            </div>
        </div>
    `).join('');
}

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const searchIcon = document.getElementById('searchIcon');
    const closeBtn = document.getElementById('closeSearch');
    const backdrop = document.getElementById('searchBackdrop');
    const searchInput = document.getElementById('searchInput');
    
    if (searchIcon) {
        searchIcon.addEventListener('click', openSearchModal);
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', closeSearchModal);
    }
    if (backdrop) {
        backdrop.addEventListener('click', closeSearchModal);
    }
    if (searchInput) {
        searchInput.addEventListener('input', performSearch);
    }
    
    // Load products on page load
    loadSearchProducts();
});