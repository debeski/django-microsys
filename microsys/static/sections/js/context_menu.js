/**
 * Context Menu for Subsection Management
 * Provides right-click (desktop) and long-press (mobile) context menu
 */

(function() {
    'use strict';
    
    // Guard against multiple executions
    if (window.subsectionContextMenuInitialized) return;
    window.subsectionContextMenuInitialized = true;
    
    const LONG_PRESS_DURATION = 500; // ms
    let pressTimer = null;
    let currentTarget = null;
    let contextMenu = null;
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        console.log('Subsection Context Menu Initialized');
        contextMenu = document.getElementById('subsectionContextMenu');
        
        // Inline Add Button Logic (Event Delegation)
        document.body.addEventListener('click', function(e) {
            const btn = e.target.closest('.add-subsection-btn');
            if (btn) {
                handleInlineAdd(e, btn);
            }
        });

        if (!contextMenu) return;
        
        // Bind events to existing subsection checkboxes
        bindCheckboxEvents(document.querySelectorAll('.subsection-checkbox-label'));
        
        // Close menu on click outside
        document.addEventListener('click', hideMenu);
        document.addEventListener('scroll', hideMenu);
        
        // Bind menu actions
        const editBtn = contextMenu.querySelector('[data-action="edit"]');
        const deleteBtn = contextMenu.querySelector('[data-action="delete"]');
        
        if (editBtn) editBtn.addEventListener('click', handleEdit);
        if (deleteBtn) deleteBtn.addEventListener('click', handleDelete);
    }
    
    function bindCheckboxEvents(elements) {
        elements.forEach(label => {
            // Remove existing listeners to avoid duplicates if re-binding
            label.removeEventListener('contextmenu', handleContextMenu);
            label.removeEventListener('touchstart', handleTouchStart);
            label.removeEventListener('touchend', handleTouchEnd);
            label.removeEventListener('touchcancel', handleTouchEnd);
            label.removeEventListener('touchmove', handleTouchEnd);

            // Right-click (desktop)
            label.addEventListener('contextmenu', handleContextMenu);
            
            // Long-press (mobile)
            label.addEventListener('touchstart', handleTouchStart, { passive: false });
            label.addEventListener('touchend', handleTouchEnd);
            label.addEventListener('touchcancel', handleTouchEnd);
            label.addEventListener('touchmove', handleTouchEnd);
        });
    }
    
    // ... Context Menu Handlers (handleContextMenu, handleTouchStart, etc.) ...
    function handleContextMenu(e) {
        e.preventDefault();
        e.stopPropagation();
        currentTarget = e.currentTarget;
        showMenu(e.clientX, e.clientY);
    }
    
    function handleTouchStart(e) {
        currentTarget = e.currentTarget;
        currentTarget.classList.add('checkbox-pressing');
        
        pressTimer = setTimeout(() => {
            if (navigator.vibrate) navigator.vibrate(50);
            const touch = e.touches[0];
            showMenu(touch.clientX, touch.clientY);
            e.preventDefault();
        }, LONG_PRESS_DURATION);
    }
    
    function handleTouchEnd() {
        if (pressTimer) {
            clearTimeout(pressTimer);
            pressTimer = null;
        }
        if (currentTarget) {
            currentTarget.classList.remove('checkbox-pressing');
        }
    }
    
    function showMenu(x, y) {
        if (!contextMenu) return;
        
        // Position menu
        contextMenu.style.left = x + 'px';
        contextMenu.style.top = y + 'px';
        contextMenu.classList.add('show');
        
        // Adjust if menu goes off-screen
        const rect = contextMenu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            contextMenu.style.left = (window.innerWidth - rect.width - 10) + 'px';
        }
        if (rect.bottom > window.innerHeight) {
            contextMenu.style.top = (window.innerHeight - rect.height - 10) + 'px';
        }
    }
    
    function hideMenu() {
        if (contextMenu) {
            contextMenu.classList.remove('show');
        }
    }

    // Inline Add Logic
    function handleInlineAdd(e, btn) {
        if (!btn) return;
        
        const container = btn.closest('.d-flex');
        const csrfToken = btn.dataset.csrf; // Get token
        const fieldName = btn.dataset.fieldName || 'sub_affiliates';
        const addUrl = btn.dataset.addUrl;
        const parentModel = btn.dataset.parentModel;
        const parentId = btn.dataset.parentId;
        const parentField = btn.dataset.parentField;
        const childModel = btn.dataset.childModel;
        
        // Create input element
        const inputWrapper = document.createElement('div');
        // ... (rest of creation logic)
        inputWrapper.className = 'position-relative d-inline-block';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control textinput h-100';
        input.placeholder = 'اسم القسم الجديد';
        input.style.width = '150px';
        input.dir = 'rtl';
        
        inputWrapper.appendChild(input);
        container.insertBefore(inputWrapper, btn);
        
        input.focus();
        
        // Handle input events
        input.addEventListener('keydown', function(ev) {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                saveNewSubsection(input, parentModel, childModel, csrfToken, fieldName, addUrl, parentId, parentField);
            } else if (ev.key === 'Escape') {
                inputWrapper.remove();
            }
        });
        
        input.addEventListener('blur', function() {
            if (input.value.trim()) {
                saveNewSubsection(input, parentModel, childModel, csrfToken, fieldName, addUrl, parentId, parentField);
            } else {
                inputWrapper.remove();
            }
        });
    }

    function saveNewSubsection(input, parentModel, childModel, csrfToken, fieldName, addUrl, parentId, parentField) {
        if (input.dataset.saving) return; // Prevent double submission
        
        const name = input.value.trim();
        if (!name) return;
        
        input.dataset.saving = 'true';
        input.disabled = true;
        
        // AJAX request
        const formData = new FormData();
        formData.append('name', name);
        formData.append('csrfmiddlewaretoken', csrfToken); // Use passed token
        
        const queryParts = [`model=${childModel}`, `parent=${parentModel}`];
        if (parentId) queryParts.push(`parent_id=${parentId}`);
        if (parentField) queryParts.push(`parent_field=${parentField}`);
        const query = `?${queryParts.join('&')}`;
        fetch(`${addUrl}${query}`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Replace input with checkbox
                const wrapper = input.parentElement;
                if (!wrapper.parentNode) return; // Prevent error if already processed
                const container = wrapper.parentElement;
                const emptyMsg = container.querySelector('.subsection-empty');
                if (emptyMsg) emptyMsg.remove();
                
                const checkboxId = `id_${fieldName}_new_${data.id}`;
                
                const checkboxHTML = `
                    <input type="checkbox" 
                           name="${fieldName}" 
                           value="${data.id}" 
                           class="btn-check" 
                           id="${checkboxId}" 
                           checked>
                    <label class="btn btn-outline-secondary subsection-checkbox-label" 
                           for="${checkboxId}" 
                           style="font-size: 1.1rem;"
                           data-sub-id="${data.id}"
                           data-sub-name="${name}"
                           data-locked="false">
                      ${name}
                    </label>
                `;
                
                // Insert new HTML
                wrapper.outerHTML = checkboxHTML;
                
                // Bind events to new label
                const newLabel = container.querySelector(`label[for="${checkboxId}"]`);
                if (newLabel) bindCheckboxEvents([newLabel]);
                
            } else {
                alert('خطأ: ' + (data.error || 'تعذر الحفظ'));
                input.disabled = false;
                delete input.dataset.saving;
                input.focus();
            }
        })
        .catch(err => {
            console.error(err);
            alert('حدث خطأ في الاتصال: ' + err.message);
            input.disabled = false;
            delete input.dataset.saving;
            input.focus();
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // ... Existing Edit/Delete Handlers ...
    function handleEdit() {
        if (!currentTarget) return;
        
        const subId = currentTarget.dataset.subId;
        const subName = currentTarget.dataset.subName;
        // Get CSRF token from the add button or input if available
        let csrfToken = '';
        const container = currentTarget.closest('.d-flex');
        const addBtn = container ? container.querySelector('.add-subsection-btn') : document.querySelector('.add-subsection-btn');
        if (addBtn) csrfToken = addBtn.dataset.csrf;
        
        hideMenu();
        
        // Hide current label and checkbox
        const label = currentTarget;
        const checkboxId = label.getAttribute('for');
        const checkbox = document.getElementById(checkboxId);
        const wrapper = checkbox.parentElement; // div.position-relative or just wrapper
        
        // Hide original elements
        label.style.display = 'none';
        checkbox.style.display = 'none';
        
        // Create inline input
        const input = document.createElement('input');
        input.type = 'text';
        input.value = subName;
        input.className = 'form-control textinput pt-1 d-inline-block';
        input.style.width = Math.max(subName.length * 10 + 50, 150) + 'px'; // Auto width
        input.dir = 'rtl';
        input.dataset.originalName = subName;
        
        // Insert input after label
        label.parentNode.insertBefore(input, label.nextSibling);
        input.focus();
        
        // Handlers
        const finishEdit = (save) => {
            if (input.parentNode) {
                if (save) {
                    saveEditSubsection(input, subId, csrfToken, label, checkbox);
                } else {
                    // Cancel: Restore original
                    input.remove();
                    label.style.display = '';
                    checkbox.style.display = '';
                }
            }
        };
        
        input.addEventListener('keydown', function(ev) {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                finishEdit(true);
            } else if (ev.key === 'Escape') {
                finishEdit(false);
            }
        });
        
        input.addEventListener('blur', function() {
            if (input.value.trim() && input.value.trim() !== subName) {
                finishEdit(true);
            } else {
                finishEdit(false);
            }
        });
    }

    function saveEditSubsection(input, subId, csrfToken, label, checkbox) {
        if (input.dataset.saving) return;
        
        const newName = input.value.trim();
        const originalName = input.dataset.originalName;
        
        if (!newName || newName === originalName) {
             // Revert if empty or unchanged
             input.remove();
             label.style.display = '';
             checkbox.style.display = '';
             return;
        }
        
        input.dataset.saving = 'true';
        input.disabled = true;
        
        const formData = new FormData();
        formData.append('name', newName);
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        // Assume parent/model from add button or context
        // But for edit we typically just need ID. 
        // The view expects ?model=...&parent=... to redirect, but since we use AJAX/JSON, 
        // the view likely uses those for redirect generation if not JSON.
        // We do need to handle the model resolution in view if it relies on GET params.
        // `edit_subsection` view uses GET params for model resolution!
        // So we must pass them.
        
        const container = currentTarget.closest('.d-flex');
        const addBtn = container ? container.querySelector('.add-subsection-btn') : document.querySelector('.add-subsection-btn');
        let queryParams = '';
        if (addBtn) {
            const queryParts = [
                `model=${addBtn.dataset.childModel}`,
                `parent=${addBtn.dataset.parentModel}`,
            ];
            if (addBtn.dataset.parentId) queryParts.push(`parent_id=${addBtn.dataset.parentId}`);
            if (addBtn.dataset.parentField) queryParts.push(`parent_field=${addBtn.dataset.parentField}`);
            queryParams = `?${queryParts.join('&')}`;
        }
        const editUrlTemplate = addBtn ? addBtn.dataset.editUrlTemplate : '';
        const editUrl = editUrlTemplate ? editUrlTemplate.replace('{id}', subId) : '';
        if (!editUrl) {
            alert('تعذر تحديد رابط التعديل.');
            input.disabled = false;
            delete input.dataset.saving;
            input.focus();
            return;
        }

        fetch(`${editUrl}${queryParams}`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (input.parentNode) { // Check if still in DOM
                if (data.success) {
                    input.remove();
                    
                    // Update label text and data
                    label.style.display = '';
                    checkbox.style.display = '';
                    
                    // The label text might contain an icon if locked, but here we just updated text?
                    // The label HTML is: `{{ checkbox.choice_label }} <i class="bi bi-lock-fill small ms-1"></i>`
                    // We should preserve the icon if it exists.
                    
                    const lockIcon = label.querySelector('i.bi-lock-fill');
                    label.textContent = data.name + ' ';
                    if (lockIcon) label.appendChild(lockIcon);
                    
                    label.dataset.subName = data.name;
                    
                } else {
                    alert('خطأ: ' + (data.error || 'تعذر التعديل'));
                    input.disabled = false;
                    delete input.dataset.saving;
                    input.focus();
                }
            }
        })
        .catch(err => {
            console.error(err);
            alert('حدث خطأ في الاتصال: ' + err.message);
            if (input.parentNode) {
                input.disabled = false;
                delete input.dataset.saving;
                input.focus();
            }
        });
    }
    
    function handleDelete() {
        if (!currentTarget) return;
        
        const subId = currentTarget.dataset.subId;
        const subName = currentTarget.dataset.subName;
        const isLocked = currentTarget.dataset.locked === 'true';
        
        if (isLocked) {
            alert('لا يمكن حذف هذا العنصر لارتباطه بسجلات أخرى');
            hideMenu();
            return;
        }
        
        if (confirm(`هل أنت متأكد من حذف "${subName}"؟`)) {
            // Submit delete form
            const form = document.getElementById('deleteSubsectionForm');
            if (form) {
                const container = currentTarget.closest('.d-flex');
                const addBtn = container ? container.querySelector('.add-subsection-btn') : document.querySelector('.add-subsection-btn');
                let queryParams = '';
                if (addBtn) {
                    const queryParts = [
                        `model=${addBtn.dataset.childModel}`,
                        `parent=${addBtn.dataset.parentModel}`,
                    ];
                    if (addBtn.dataset.parentId) queryParts.push(`parent_id=${addBtn.dataset.parentId}`);
                    if (addBtn.dataset.parentField) queryParts.push(`parent_field=${addBtn.dataset.parentField}`);
                    queryParams = `?${queryParts.join('&')}`;
                }
                const deleteUrlTemplate = addBtn ? addBtn.dataset.deleteUrlTemplate : '';
                const deleteUrl = deleteUrlTemplate ? deleteUrlTemplate.replace('{id}', subId) : '';
                if (!deleteUrl) {
                    alert('تعذر تحديد رابط الحذف.');
                    hideMenu();
                    return;
                }
                form.action = `${deleteUrl}${queryParams}`;
                form.submit();
            }
        }
        
        hideMenu();
    }
})();
