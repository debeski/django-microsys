(function() {
    'use strict';

    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Modal Builder
    function showModal(title, bodyContent, footerContent, variant = 'primary') {
        const modalId = 'sectionManagerModal';
        let modalEl = document.getElementById(modalId);
        
        if (modalEl) {
            modalEl.remove();
        }

        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content border-0 shadow-lg" style="border-radius: 12px; overflow: hidden;">
                        <div class="modal-header bg-${variant} text-white border-0">
                            <h5 class="modal-title fw-bold"><i class="bi bi-info-circle me-2"></i> ${title}</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4" style="background-color: #f8f9fa;">
                            ${bodyContent}
                        </div>
                        <div class="modal-footer bg-white border-top-0">
                            ${footerContent}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modalEl = document.getElementById(modalId);
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
        
        modalEl.addEventListener('hidden.bs.modal', () => {
             modalEl.remove();
        });
    }

    function buildRelatedHtml(relatedData) {
        if (!relatedData || Object.keys(relatedData).length === 0) {
            return '<p class="text-muted text-center my-3">لا توجد سجلات مرتبطة.</p>';
        }
        
        let html = '<div class="row g-3">';
        for (const [modelName, items] of Object.entries(relatedData)) {
            html += `
                <div class="col-md-6">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-header bg-white border-bottom-0 fw-bold text-primary">
                            ${modelName}
                        </div>
                        <ul class="list-group list-group-flush list-group-item-action">
                            ${items.map(item => `<li class="list-group-item bg-light border-0 mb-1 rounded px-3 mx-2">${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }

    document.addEventListener('DOMContentLoaded', function() {
        const sectionDataEl = document.getElementById('sectionData');
        if (!sectionDataEl) return;
        
        const sectionData = JSON.parse(sectionDataEl.textContent);
        const csrfToken = sectionData.csrf || getCookie('csrftoken');

        // ---------------------------------------------------------
        // Smart Delete Handler
        // ---------------------------------------------------------
        document.body.addEventListener('micro:section:delete', function(e) {
            const data = e.detail.data;
            if (!confirm('هل أنت متأكد من حذف: ' + data.name + ' ؟')) return;

            // Perform AJAX delete checks
            fetch(sectionData.deleteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    model: data.model,
                    pk: data.id // Ensure backend expects 'pk' (utils calls it data-pk, script passes it)
                })
            })
            .then(response => response.json())
            .then(res => {
                if (res.success) {
                    // Success -> Reload
                    window.location.reload();
                } else {
                    // Error
                    if (res.related) {
                        // Smart Delete: Show Blocking Relations
                        const body = `
                            <div class="alert alert-danger border-0 d-flex align-items-center mb-4">
                                <i class="bi bi-exclamation-triangle-fill fs-3 me-3"></i>
                                <div>
                                    <div class="fw-bold fs-5">لا يمكن حذف العنصر</div>
                                    <div class="small">هذا القسم مرتبط بالسجلات التالية، يجب حذفها أو فك ارتباطها أولاً.</div>
                                </div>
                            </div>
                            <h6 class="fw-bold mb-3 text-secondary">السجلات المرتبطة:</h6>
                            ${buildRelatedHtml(res.related)}
                        `;
                        const footer = '<button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">إغلاق</button>';
                        showModal('خطأ في الحذف', body, footer, 'danger');
                    } else {
                        // Generic Error
                        alert('خطأ: ' + res.error);
                    }
                }
            })
            .catch(err => {
                console.error('Delete Error:', err);
                alert('حدث خطأ غير متوقع.');
            });
        });

        // ---------------------------------------------------------
        // Smart View Handler
        // ---------------------------------------------------------
        document.body.addEventListener('micro:section:view', function(e) {
            const data = e.detail.data;
            
            // Fetch Details
            // Use the new detailsUrl (we need to pass it from template or construct it)
            // Assuming we added it to sectionData or use existing pattern
            // The user removed get_section_subsections and added get_section_details
            
            // Construct URL: we can assume a pattern or use the one from sectionData if updated
            // Let's assume sectionData.detailsUrl exists. I will update template next.
            
            const url = `${sectionData.detailsUrl}?model=${data.model}&pk=${data.id}`;

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(res => {
                if (res.success) {
                    // Build Fields HTML
                    let fieldsHtml = '<div class="row g-3 mb-4">';
                    for (const [label, value] of Object.entries(res.fields)) {
                        fieldsHtml += `
                            <div class="col-md-6">
                                <div class="p-3 bg-white rounded shadow-sm border h-100">
                                    <div class="text-muted small mb-1">${label}</div>
                                    <div class="fw-bold text-dark">${value}</div>
                                </div>
                            </div>
                        `;
                    }
                    fieldsHtml += '</div>';

                    // Build Related HTML
                    const relatedHtml = buildRelatedHtml(res.related);

                    const body = `
                        <h6 class="fw-bold mb-3 text-secondary border-bottom pb-2">تفاصيل بيانات السجل</h6>
                        ${fieldsHtml}
                        <h6 class="fw-bold mb-3 text-secondary border-bottom pb-2 mt-4">السجلات والاستخدامات المرتبطة</h6>
                        ${relatedHtml}
                    `;
                    const footer = '<button type="button" class="btn btn-primary rounded-pill px-4" data-bs-dismiss="modal">تم</button>';
                    
                    showModal(res.title || data.name, body, footer, 'primary');
                } else {
                    alert('خطأ: ' + res.error);
                }
            })
            .catch(err => {
                console.error('View Error:', err);
                alert('حدث خطأ أثناء جلب البيانات.');
            });
        });

    });
})();
