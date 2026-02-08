document.addEventListener('DOMContentLoaded', function() {
    console.log('Permissions Widget JS Loaded');

    // Handle Card Header Clicks for Toggle
    document.querySelectorAll('.permissions-card-header').forEach(header => {
        header.addEventListener('click', function(e) {
            // Prevent toggle if clicking directly on the checkbox
            if (e.target.closest('.form-check')) return;

            const targetId = this.getAttribute('data-bs-target');
            const target = document.querySelector(targetId);
            if (target) {
                const isCollapsed = target.classList.contains('show');
                if (isCollapsed) {
                    this.classList.add('collapsed');
                    bootstrap.Collapse.getOrCreateInstance(target).hide();
                } else {
                    this.classList.remove('collapsed');
                    bootstrap.Collapse.getOrCreateInstance(target).show();
                }
            }
        });
    });

    // Master Checkbox Logic: App Level
    document.querySelectorAll('.app-master-checkbox').forEach(master => {
        master.addEventListener('change', function() {
            const isChecked = this.checked;
            const card = this.closest('.permissions-card');
            card.querySelectorAll('.permission-checkbox, .model-master-checkbox').forEach(cb => {
                cb.checked = isChecked;
                cb.indeterminate = false;
            });
            updateGlobalStatus();
        });
    });

    // Master Checkbox Logic: Model Level
    document.querySelectorAll('.model-master-checkbox').forEach(master => {
        master.addEventListener('change', function() {
            const isChecked = this.checked;
            const modelGroup = this.closest('.model-group');
            modelGroup.querySelectorAll('.permission-checkbox').forEach(cb => {
                cb.checked = isChecked;
            });
            updateAppMasterStatus(this.closest('.permissions-card'));
            updateGlobalStatus();
        });
    });

    // Individual Permission Checkbox Logic
    document.querySelectorAll('.permission-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            updateModelMasterStatus(this.closest('.model-group'));
            updateAppMasterStatus(this.closest('.permissions-card'));
            updateGlobalStatus();
        });
    });

    function updateModelMasterStatus(modelGroup) {
        const master = modelGroup.querySelector('.model-master-checkbox');
        const children = modelGroup.querySelectorAll('.permission-checkbox');
        const checkedCount = Array.from(children).filter(c => c.checked).length;

        master.checked = checkedCount === children.length && children.length > 0;
        master.indeterminate = checkedCount > 0 && checkedCount < children.length;
    }

    function updateAppMasterStatus(card) {
        const master = card.querySelector('.app-master-checkbox');
        const children = card.querySelectorAll('.permission-checkbox');
        const checkedCount = Array.from(children).filter(c => c.checked).length;

        master.checked = checkedCount === children.length && children.length > 0;
        master.indeterminate = checkedCount > 0 && checkedCount < children.length;
    }

    function updateGlobalStatus() {
        // Optional: Update top-level "Global" selectors if any remain
    }

    // Initial State Sync
    document.querySelectorAll('.model-group').forEach(group => updateModelMasterStatus(group));
    document.querySelectorAll('.permissions-card').forEach(card => updateAppMasterStatus(card));

    // Prevent toggle propagation for specific elements
    document.querySelectorAll('.prevent-toggle').forEach(el => {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});
