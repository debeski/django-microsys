// API Helper - Exposed Globally
window.updatePreferences = function(data) {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    if (!csrfToken) {
        console.error("CSRF token not found, cannot save preferences.");
        return;
    }

    fetch('/sys/api/preferences/update/', {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (!response.ok) {
            console.error("Failed to save preferences:", response.statusText);
        } else {
            // Optimistic update of the global object
            if (window.USER_PREFS) {
                Object.assign(window.USER_PREFS, data);
            }
        }
    }).catch(error => {
        console.error("Error updating preferences:", error);
    });
};

document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");


    // 1. Sidebar Collapse State
    // Initial state from injected USER_PREFS or fallback to dataset/session logic
    // Note: base sidebar class might be set by server-render, but we enforce JS preference here
    let isCollapsed = window.USER_PREFS?.sidebar_collapsed;
    if (isCollapsed === undefined && sidebar) {
        // Fallback to old behavior if no pref set yet
        isCollapsed = sidebar.dataset.sessionCollapsed === "true";
    } else if (isCollapsed === undefined) {
        isCollapsed = false; // Default if sidebar missing
    }

    // Function to handle sidebar collapsing based on window size
    function adjustSidebarForWindowSize() {
        if (!sidebar) return; // Exit if sidebar doesn't exist (e.g., login page)
        
        const screenWidth = window.innerWidth;

        if (screenWidth < 1100) {
            // Always collapse sidebar on small screens
            sidebar.classList.add("collapsed");
            initializeTooltips();
        } else {
            // Large screens: respect user preference
            sidebar.style.top = '';
            sidebar.style.height = '';

            if (isCollapsed) {
                sidebar.classList.add("collapsed");
                initializeTooltips();
            } else {
                sidebar.classList.remove("collapsed");
                deinitializeTooltips();
            }
        }
    }

    // Apply initial state
    adjustSidebarForWindowSize();

    // Listen for window resize
    window.addEventListener("resize", adjustSidebarForWindowSize);

    // Toggle sidebar
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("collapsed");
            isCollapsed = sidebar.classList.contains("collapsed");

            if (isCollapsed) {
                initializeTooltips();
            } else {
                deinitializeTooltips();
            }

            // Save preference
            window.updatePreferences({ sidebar_collapsed: isCollapsed });
            
            // Update local state copy
            if (window.USER_PREFS) window.USER_PREFS.sidebar_collapsed = isCollapsed;
        });
    }

    // 2. Accordion Persistence
    const accordions = document.querySelectorAll('.sidebar .accordion-collapse');
    
    // Load saved state
    const openAccordions = window.USER_PREFS?.open_accordions || [];
    openAccordions.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            // Remove 'collapse' class to show, or use Bootstrap API
            el.classList.add('show');
            // Update button state
            const btn = document.querySelector(`[data-bs-target="#${id}"]`);
            if (btn) {
                btn.classList.remove('collapsed');
                btn.setAttribute('aria-expanded', 'true');
            }
        }
    });

    // Save state on change
    accordions.forEach(acc => {
        acc.addEventListener('shown.bs.collapse', saveAccordionState);
        acc.addEventListener('hidden.bs.collapse', saveAccordionState);
    });

    function saveAccordionState() {
        const openItems = Array.from(document.querySelectorAll('.sidebar .accordion-collapse.show'))
            .map(el => el.id)
            .filter(id => id); // Filter out empty IDs
        
        window.updatePreferences({ open_accordions: openItems });
        if (window.USER_PREFS) window.USER_PREFS.open_accordions = openItems;
    }
});

// Close sidebar when clicking outside (only for small screens)
document.addEventListener("click", function (event) {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const screenWidth = window.innerWidth;
    
    if (sidebar && sidebarToggle && screenWidth < 1100 && !sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
        if (!sidebar.classList.contains("collapsed")) {
            sidebar.classList.add("collapsed");
            initializeTooltips();
        }
    }
});

function initializeTooltips() {
    const sidebarItems = document.querySelectorAll(".sidebar.collapsed .list-group-item, .sidebar.collapsed .accordion-button");
    sidebarItems.forEach(item => {
        if (item._tooltip) {
            item._tooltip.dispose();
        }
        item._tooltip = new bootstrap.Tooltip(item, {
            title: item.querySelector("span").textContent,
            placement: "right",
            customClass: "tooltip-custom",
            trigger: 'hover' // Explicitly disable click/focus triggers
        });
    });
}

function deinitializeTooltips() {
    const sidebarItems = document.querySelectorAll(".sidebar .list-group-item, .sidebar .accordion-button");
    sidebarItems.forEach(item => {
        if (item._tooltip) {
            item._tooltip.dispose();
            item._tooltip = null;
        }
    });
}
