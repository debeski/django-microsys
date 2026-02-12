(function() {
    'use strict';

    // Configuration
    const STORAGE_PREFIX = 'microsys_autofill_';
    const TOGGLE_KEY = 'enable_prefill';

    /**
     * Initialize Autofill System
     */
    function initAutofill() {
        const toggle = document.getElementById('autofillToggle');
        if (!toggle) return;

        // Check if enabled
        const isEnabled = localStorage.getItem(TOGGLE_KEY) === 'true';
        updateToggleUI(isEnabled);

        // Identify current context (app/model)
        // Expects data attributes on the form or a container
        const form = document.querySelector('form[data-model-name]');
        if (!form) return;

        const appLabel = form.dataset.appLabel;
        const modelName = form.dataset.modelName;

        if (!appLabel || !modelName) return;

        // Handle Form Submission (Store State)
        form.addEventListener('submit', function() {
            if (localStorage.getItem(TOGGLE_KEY) === 'true') {
                 // Store marker that last submit was "ON"
                 // We don't have the new ID yet, but we mark it.
                 // Actually, on the NEXT load, if this marker exists, we fetch last entry.
                 sessionStorage.setItem('microsys_last_submit_autofill', 'true');
            } else {
                 sessionStorage.removeItem('microsys_last_submit_autofill');
            }
        });

        // Handle Page Load (Autofill if needed)
        if (isEnabled) {
            handleAutofill(appLabel, modelName, form);
        }

        // Handle Toggle Change
        toggle.addEventListener('change', function() {
            const enabled = this.checked;
            localStorage.setItem(TOGGLE_KEY, enabled);
            
            if (enabled) {
                handleAutofill(appLabel, modelName, form);
            } else {
                // Clear fields?
                // The original script cleared fields. We might want to keep that behavior.
                clearAutofilledFields(form);
            }
        });
    }

    /**
     * Main Autofill Logic
     */
    async function handleAutofill(appLabel, modelName, form) {
        const storageKey = `${STORAGE_PREFIX}${appLabel}_${modelName}`;
        let targetId = null;

        // Check if we just submitted with Autosave ON
        if (sessionStorage.getItem('microsys_last_submit_autofill') === 'true') {
            // New entry created! Use it as the new base.
            // Fetch Last Entry from API
            try {
                const lastEntry = await fetchLastEntry(appLabel, modelName);
                if (lastEntry && lastEntry._pk) {
                    targetId = lastEntry._pk;
                    // Update LocalStorage (Smart Ignore: only update valid IDs)
                    localStorage.setItem(storageKey, targetId);
                }
                sessionStorage.removeItem('microsys_last_submit_autofill'); // Consumed
            } catch (e) {
                console.error("Autofill: Failed to fetch last entry", e);
            }
        } 
        
        // If no targetId yet, check LocalStorage (Sticky)
        if (!targetId) {
            targetId = localStorage.getItem(storageKey);
        }

        // If still no targetId (Cross-Device/Fresh), fallback to Last Entry
        if (!targetId) {
            try {
                const lastEntry = await fetchLastEntry(appLabel, modelName);
                if (lastEntry) targetId = lastEntry._pk;
            } catch (e) {
                 console.warn("Autofill: No history found.");
            }
        }

        // If we have a Target ID, Fetch & Fill
        if (targetId) {
            try {
                const data = await fetchModelDetails(appLabel, modelName, targetId);
                populateForm(form, data);
            } catch (e) {
                console.error("Autofill: Failed to fetch details for ID " + targetId, e);
            }
        }
    }

    // API Helpers
    async function fetchLastEntry(app, model) {
        const response = await fetch(`/sys/api/last-entry/${app}/${model}/`);
        if (!response.ok) throw new Error(response.statusText);
        return await response.json();
    }
    
    async function fetchModelDetails(app, model, pk) {
        const response = await fetch(`/sys/api/details/${app}/${model}/${pk}/`);
        if (!response.ok) throw new Error(response.statusText);
        return await response.json();
    }

    // UI Helpers
    function updateToggleUI(enabled) {
        const toggle = document.getElementById('autofillToggle');
        if (toggle) toggle.checked = enabled;
    }

    function populateForm(form, data) {
        if (!data) return;
        
        // Iterate over data and fill inputs
        for (const [key, value] of Object.entries(data)) {
            if (key.startsWith('_')) continue; // Skip metadata
            
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                // Determine field type
                if (input.type === 'checkbox') {
                    input.checked = !!value;
                } else if (input.type === 'radio') {
                    // Start logic for radio if needed
                } else {
                    input.value = value;
                }
                
                // Trigger change for dependencies
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }

        // Intelligent Increment
        // Find first integer field or field named 'number', 'sequence'
        const numberFields = Array.from(form.querySelectorAll('input[type="number"]'));
        let targetNumField = numberFields.find(f => f.name.includes('number') || f.name.includes('sequence'));
        if (!targetNumField && numberFields.length > 0) targetNumField = numberFields[0];

        if (targetNumField) {
            let val = parseInt(targetNumField.value);
            if (!isNaN(val)) {
                targetNumField.value = val + 1;
                targetNumField.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }

    function clearAutofilledFields(form) {
        // Option: Clear all non-hidden fields?
        // Or just reload page?
        // The previous implementation cleared fields.
        // We'll use a safe clear.
        const inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="csrfmiddlewaretoken"]), select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') input.checked = false;
            else input.value = '';
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    // Run
    document.addEventListener('DOMContentLoaded', initAutofill);

})();
