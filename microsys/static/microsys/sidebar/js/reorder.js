(function() {
    'use strict';

    const STORAGE_KEY_AUTO = 'sidebar_auto_order';
    const STORAGE_KEY_PREFIX_EXTRA = 'sidebar_extra_';

    let isReorderMode = false;
    let draggedElement = null;
    let dropIndicator = null;

    // Expose restore function globally for immediate FOUC fix
    window.restoreSidebarOrder = restoreOrder;

    document.addEventListener('DOMContentLoaded', () => {
        const sidebar = document.getElementById('sidebar');
        const reorderToggle = document.getElementById('sidebarReorderToggle');
        
        if (!sidebar || !reorderToggle) return;

        // Create drop indicator element
        dropIndicator = document.createElement('div');
        dropIndicator.className = 'drop-indicator';
        dropIndicator.style.display = 'none';

        // Restore is now called immediately via inline script for FOUC prevention
        // But call again here as fallback if inline script didn't run
        if (!window._sidebarOrderRestored) {
            restoreOrder();
        }

        // Toggle reorder mode
        reorderToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            isReorderMode = !isReorderMode;
            reorderToggle.classList.toggle('active', isReorderMode);
            sidebar.classList.toggle('reorder-mode', isReorderMode);
            
            if (isReorderMode) {
                enableDragAndDrop();
            } else {
                disableDragAndDrop();
            }
        });

        // Close reorder mode when clicking outside
        document.addEventListener('click', (e) => {
            if (isReorderMode && !sidebar.contains(e.target)) {
                isReorderMode = false;
                reorderToggle.classList.remove('active');
                sidebar.classList.remove('reorder-mode');
                disableDragAndDrop();
            }
        });
    });

    function enableDragAndDrop() {
        // Auto items in .sidebar-auto-items or direct .list-group children
        const autoContainer = document.getElementById('sidebarAutoItems') || 
                              document.querySelector('.sidebar .list-group');
        if (autoContainer) {
            setupDraggableContainer(autoContainer, STORAGE_KEY_AUTO);
        }

        // Extra group items in accordion bodies
        const accordionBodies = document.querySelectorAll('.sidebar .accordion-body');
        accordionBodies.forEach(body => {
            const groupName = body.dataset.groupName || body.closest('.accordion-item')?.querySelector('.accordion-button span')?.textContent?.trim();
            if (groupName) {
                const key = STORAGE_KEY_PREFIX_EXTRA + slugify(groupName);
                setupDraggableContainer(body, key);
            }
        });
    }

    function disableDragAndDrop() {
        const items = document.querySelectorAll('.sidebar .list-group-item[draggable="true"]');
        items.forEach(item => {
            item.removeAttribute('draggable');
            item.removeEventListener('dragstart', handleDragStart);
            item.removeEventListener('dragend', handleDragEnd);
            item.removeEventListener('dragover', handleDragOver);
            item.removeEventListener('drop', handleDrop);
        });
        
        // Hide drop indicator
        if (dropIndicator) {
            dropIndicator.style.display = 'none';
            if (dropIndicator.parentNode) {
                dropIndicator.parentNode.removeChild(dropIndicator);
            }
        }
    }

    function setupDraggableContainer(container, storageKey) {
        const items = container.querySelectorAll(':scope > .list-group-item');
        
        items.forEach(item => {
            // Skip accordion buttons - they're not reorderable
            if (item.classList.contains('accordion-button')) return;
            
            item.setAttribute('draggable', 'true');
            item.dataset.storageKey = storageKey;
            
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
            item.addEventListener('dragover', handleDragOver);
            item.addEventListener('drop', handleDrop);
        });

        // Add event listeners to container for drag events
        container.addEventListener('dragover', handleContainerDragOver);
        container.addEventListener('drop', handleContainerDrop);
    }

    function handleDragStart(e) {
        draggedElement = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', ''); // Required for Firefox
        
        // Add drop indicator to DOM
        if (dropIndicator && this.parentNode) {
            this.parentNode.appendChild(dropIndicator);
        }
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
        
        // Hide drop indicator
        if (dropIndicator) {
            dropIndicator.style.display = 'none';
        }
        
        // Save new order
        if (draggedElement) {
            saveOrder(draggedElement.parentNode, draggedElement.dataset.storageKey);
        }
        
        draggedElement = null;
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        if (!draggedElement || draggedElement === this) return;
        if (draggedElement.dataset.storageKey !== this.dataset.storageKey) return;
        
        const rect = this.getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        
        // Show drop indicator
        if (dropIndicator) {
            dropIndicator.style.display = 'block';
            if (e.clientY < midY) {
                this.parentNode.insertBefore(dropIndicator, this);
            } else {
                this.parentNode.insertBefore(dropIndicator, this.nextSibling);
            }
        }
    }

    function handleContainerDragOver(e) {
        e.preventDefault();
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!draggedElement || draggedElement === this) return;
        if (draggedElement.dataset.storageKey !== this.dataset.storageKey) return;
        
        const rect = this.getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        
        if (e.clientY < midY) {
            this.parentNode.insertBefore(draggedElement, this);
        } else {
            this.parentNode.insertBefore(draggedElement, this.nextSibling);
        }
    }

    function handleContainerDrop(e) {
        e.preventDefault();
        // Item drops are handled by individual items
    }

    function saveOrder(container, storageKey) {
        if (!container || !storageKey) return;
        
        const items = container.querySelectorAll(':scope > .list-group-item[data-url-name]');
        const order = Array.from(items).map(item => item.dataset.urlName);
        
        try {
            localStorage.setItem(storageKey, JSON.stringify(order));
        } catch (e) {
            console.warn('Could not save sidebar order (localStorage):', e);
        }

        // Save to DB via global API
        if (window.updatePreferences) {
            const currentOrder = window.USER_PREFS?.sidebar_order || {};
            const newSidebarOrder = Object.assign({}, currentOrder);
            newSidebarOrder[storageKey] = order;
            
            window.updatePreferences({ 
                sidebar_order: newSidebarOrder 
            });
            
            // Re-update local USER_PREFS immediately for UI consistency
            if (window.USER_PREFS) {
                window.USER_PREFS.sidebar_order = newSidebarOrder;
            }
        }
    }

    function restoreOrder() {
        // Restore auto items order
        const autoContainer = document.getElementById('sidebarAutoItems') || 
                              document.querySelector('.sidebar .list-group');
        if (autoContainer) {
            restoreContainerOrder(autoContainer, STORAGE_KEY_AUTO);
        }

        // Restore extra group items order
        const accordionBodies = document.querySelectorAll('.sidebar .accordion-body');
        accordionBodies.forEach(body => {
            const groupName = body.dataset.groupName || body.closest('.accordion-item')?.querySelector('.accordion-button span')?.textContent?.trim();
            if (groupName) {
                const key = STORAGE_KEY_PREFIX_EXTRA + slugify(groupName);
                restoreContainerOrder(body, key);
            }
        });
        
        // Mark as restored
        window._sidebarOrderRestored = true;
    }

    function restoreContainerOrder(container, storageKey) {
        let savedOrder;
        try {
            // Try USER_PREFS first
            if (window.USER_PREFS?.sidebar_order?.[storageKey]) {
                savedOrder = window.USER_PREFS.sidebar_order[storageKey];
            } else {
                // Fallback to localStorage
                const saved = localStorage.getItem(storageKey);
                if (saved) savedOrder = JSON.parse(saved);
            }
        } catch (e) {
            return; // Invalid, use default
        }
        
        if (!Array.isArray(savedOrder) || savedOrder.length === 0) return;
        
        const items = container.querySelectorAll(':scope > .list-group-item[data-url-name]');
        const itemMap = new Map();
        items.forEach(item => {
            itemMap.set(item.dataset.urlName, item);
        });
        
        // Reorder based on saved order
        savedOrder.forEach(urlName => {
            const item = itemMap.get(urlName);
            if (item) {
                container.appendChild(item);
                itemMap.delete(urlName);
            }
        });
        
        // Append any remaining items (new items not in saved order)
        itemMap.forEach(item => {
            container.appendChild(item);
        });
    }

    function slugify(text) {
        return text
            .toString()
            .toLowerCase()
            .trim()
            .replace(/\s+/g, '-')
            .replace(/[^\w\-]+/g, '')
            .replace(/\-\-+/g, '-');
    }
})();
