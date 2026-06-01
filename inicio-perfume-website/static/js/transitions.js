// Prevent form submissions from triggering the loading overlay
document.addEventListener('click', function(e) {
    // If the clicked element is inside a form, don't trigger navigation loading
    if (e.target.closest('form')) {
        e.stopPropagation();
        return;
    }
});

// Show loading spinner when navigating
function showLoading() {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Track if we're handling a back/forward navigation
let isBackNavigation = false;

// Handle back/forward navigation - don't show loading spinner
window.addEventListener('pageshow', function(event) {
    if (event.persisted || isBackNavigation) {
        hideLoading();
        isBackNavigation = false;
    }
});

window.addEventListener('popstate', function() {
    isBackNavigation = true;
    // Don't show loading for back/forward navigation
    hideLoading();
});

// Smooth page transitions for navigation links ONLY (not for buttons, search, or back/forward)
document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    
    // Skip if it's inside a form (prevents form submission from triggering loading)
    if (e.target.closest('form')) return;
    
    // Skip if no link
    if (!link) return;
    
    // Skip if has special attributes
    if (link.hasAttribute('data-no-loading')) return;
    if (link.getAttribute('href') === '#') return;
    if (link.getAttribute('href') === 'javascript:void(0)') return;
    if (link.id === 'searchIcon') return;  // Skip search icon
    if (link.classList.contains('no-loading')) return;
    
    const currentDomain = window.location.origin;
    const targetUrl = link.href;
    
    // Skip external links
    if (!targetUrl.startsWith(currentDomain)) return;
    
    // Skip anchor links (same page navigation)
    if (targetUrl.indexOf('#') !== -1 && targetUrl.split('#')[0] === window.location.href.split('#')[0]) return;
    
    e.preventDefault();
    
    showLoading();
    
    setTimeout(() => {
        window.location.href = targetUrl;
    }, 150);
});

// Hide loading on page load
window.addEventListener('load', function() {
    hideLoading();
    document.body.classList.add('page-transition');
});

// Add ripple effect to buttons (excluding search)
document.querySelectorAll('button:not(#searchIcon), .btn:not(#searchIcon), .checkout-btn, .add-to-cart, .story-btn, .view-all-btn, .place-order-btn').forEach(button => {
    button.classList.add('ripple');
});

// Add card hover class to product cards
document.querySelectorAll('.product-card, .product-feature-card').forEach(card => {
    card.classList.add('card-hover');
});

// Stagger animations for grids
document.querySelectorAll('.products-grid, .products-row, .stats-grid, .charts-section').forEach(grid => {
    grid.classList.add('stagger-children');
});

// Smooth scroll for anchor links only
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Add hover animation to nav links (but not too aggressive)
document.querySelectorAll('.nav-links a, .sidebar-menu li').forEach(item => {
    item.addEventListener('mouseenter', function() {
        this.style.transition = 'transform 0.2s ease';
        this.style.transform = 'translateX(3px)';
    });
    item.addEventListener('mouseleave', function() {
        this.style.transform = 'translateX(0)';
    });
});

// Fix for search icon - prevent loading overlay
const searchIcon = document.getElementById('searchIcon');
if (searchIcon) {
    searchIcon.addEventListener('click', function(e) {
        e.stopPropagation();
        // Don't show loading, just let the search modal open
    });
}