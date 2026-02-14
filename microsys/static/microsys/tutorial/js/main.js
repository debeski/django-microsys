document.addEventListener("DOMContentLoaded", function () {
    // Tutorial Logic
    const driver = window.driver.js.driver;
    
    function getTutorialSteps() {
        const path = window.location.pathname;
        let steps = [];

        // 1. Dashboard / Home
        if (path === '/' || path === '/index/') {
            steps = [
                { element: '#sidebar', popover: { title: 'القائمة الجانبية', description: 'يمكنك التنقل بين أقسام الأرشيف المختلفة من هنا في اي وقت (بريد صادر، وارد، قرارات...).', side: "top", align: 'start' }},
                { element: '.titlebar', popover: { title: 'شريط العنوان', description: 'يحتوي على اسم النظام والقائمة الشخصية للمستخدم.', side: "top", align: 'center' }},
                { element: '.login-title-btn', popover: { title: 'قائمة المستخدم', description: 'من هنا يمكنك تسجيل الخروج أو الذهاب لصفحة الملف الشخصي.', side: "top", align: 'end' }},
                { element: '#mainContent', popover: { title: 'منطقة العمل', description: 'هنا تظهر الجداول، النماذج، والمحتوى الرئيسي للنظام.', side: "top", align: 'end' }},
                { element: '#sidebarToggle', popover: { title: 'اخفاء/اظهار القائمة', description: 'يمكنك توسيع أو تصغير القائمة الجانبية لتوفير مساحة أكبر للعرض.', side: "top", align: 'end' }},
            ];
        }
        // 2. List Views (Check for search form or table)
        else if (document.querySelector('input[name="keyword"]') || document.querySelector('.table')) {
            steps = [
                { element: '#sidebar', popover: { title: 'القائمة الجانبية', description: 'يمكنك التنقل بين أقسام الأرشيف المختلفة من هنا في اي وقت (بريد صادر، وارد، قرارات...).', side: "top", align: 'start' }},
                { element: 'input[name="keyword"]', popover: { title: 'البحث', description: 'ابحث عن المستندات باستخدام العناوين، الكلمات المفتاحية، الأرقام، والجهات والسنوات.', side: "right", align: 'center' }},
                { element: 'select[name="date__year"]', popover: { title: 'الفرز عبر السنة', description: 'فرز النتائج حسب السنة.', side: "left", align: 'center' }},

                { element: '#advanced-search', popover: { title: 'البحث المتقدم', description: 'استخدم الفلاتر لتقليص نتائج البحث (مثلا: الرقم بالضبط، السنة، النوع).', side: "top", align: 'center' }},
                { element: '.bi-plus-lg', popover: { title: 'إضافة جديد', description: 'اضغط هنا لإضافة مستند جديد لهذا القسم.', side: "left", align: 'center' }},
                { element: '.bi-download', popover: { title: 'تنزيل ملفات PDF', description: 'اضغط هنا لتحميل جميع ملفات النتائج الظاهرة في الجدول.', side: "left", align: 'center' }},
                { element: '.bi-file-earmark-spreadsheet', popover: { title: 'تنزيل كملف اكسل', description: 'اضغط هنا لتحميل جميع بيانات النتائج الظاهرة في الجدول الى ملف اكسل.', side: "left", align: 'center' }},

                { element: '.nav-tabs', popover: { title: 'انواع المستندات', description: 'بالضغط على مختلف الازرار هنا، يمكنك فرز المستندات حسب نوعها او تصنيفها بسرعه، كما يمكنك اضافة فلاتر اخرى من البحث المتقدم لتقليص النتائج الى اقصى حد.', side: "top", align: 'start' }},

                { element: '.table-responsive-lg', popover: { title: 'جدول البيانات', description: 'هنا يتم عرض المستندات بهذا القسم. اضغط على الثلاث نقاط لعرض التفاصيل او التعديل، او اضعط على ايقونة الملف لتحميل ملف المستند.', side: "top", align: 'start' }},
            ];
        }
        // 3. Form Views (Check for main form)
        else if (document.querySelector('form[method="post"]')) {
                steps = [
                { element: '#sidebar', popover: { title: 'القائمة الجانبية', description: 'تأكد من أنك تقوم بالادخال في المكان الصحيح،  تنبيه: الخروج دون الحفظ سيفقدك البيانات التي قمت بإدخالها.', side: "top", align: 'start' }},
                { element: 'input[name="number"]', popover: { title: 'الرقم الرئيسي للمستند', description: 'هذا هو الرقم الرئيسي للمستند، للبريد الوارد فهو رقم التسجيل في ختم التسجيل، للبريد الصادر فهو رقم الكتاب، للقرارات والمناشير والخ فهو رقم المستند.', side: "top", align: 'start' }},
                { element: 'input[name="og_number"]', popover: { title: 'رقم الكتاب الأصلي', description: 'اما هذا فهو رقم كتاب الوارد الاصلي، عادة يكون مكتوبا باليد في اعلى يسار الورقة.', side: "top", align: 'start' }},
                { element: 'select[name="affiliate"]', popover: { title: 'الجهات الاخرى والجهات التابعة', description: 'بعد اختيارك للجهة، تأكد من اختيار التقسيم الاداري الصحيح في الخانة التالية.', side: "top", align: 'start' }},
                { element: 'select[name="destination"]', popover: { title: 'التقسيم الاداري الموجه له الكتاب', description: 'في حالة كان الكتاب موجه الى تقسيم اداري اخر غير التقسيم الرئيسي "في هذه الحالة مكتب الوكيل" سيتم اعتباره تلقائيا على انه بريد تم اعادة توجيهه / احالته الى مكتب الوكيل.', side: "top", align: 'start' }},
                
                { element: 'input[name="is_routed"]', popover: { title: 'بريد معاد توجيهه', description: 'قم بتفعيل هذا الخيار اذا كان الكتاب قد وصل الى قسم آخر أولاً (مثلاً: مكتب الوزير) ثم تمت إحالته إلينا. عند التفعيل، يجب عليك تحديد الجهة الأصلية (المرسل الخارجي) والجهة المحال منها (المرسل الداخلي).', side: "top", align: 'start' }},
                { element: 'input[name="is_fyi"]', popover: { title: 'صورة للعلم', description: 'قم بتفعيل هذا الخيار اذا كان الكتاب عبارة عن "صورة للعلم" فقط من قسم داخلي آخر، وليس كتاباً أصلياً موجهاً لنا من جهة خارجية. عند التفعيل، ستختفي خانات الجهة الخارجية ويكتفى بتحديد القسم الداخلي المرسل.', side: "top", align: 'start' }},
                
                { element: 'select[name="source_routed"]', popover: { title: 'الجهة المصدر / المحال منها', description: 'من هذه الخانة يمكنك اخنيار التقسيم الاداري الذي تم اعادة توجيه الرسالة منه أو ارسل كصورة للعلم.', side: "top", align: 'start' }},

                { element: 'select[name="type"]', popover: { title: 'نوع المستند', description: 'من هنا يمكنك اختيار نوع المستند، قد تتغير بعض الحقول بناء على النوع المختار.', side: "top", align: 'start' }},
                { element: 'input[type="file"]', popover: { title: 'حقل الملف', description: 'يمكنك الضغط على الزر لرفع ملف الPDF، او يمكنك سحبه الى هنا مباشرة.', side: "top", align: 'start' }},
                { element: '.scan-btn', popover: { title: 'استخدام الماسح الضوئي', description: 'اذا كان لديك ماسح ضوئي متصل، استخدم هذا الزر لمسح المستند مباشرة من هنا، تأكد من ان تطبيق ScanLink شغال وان الماسح الضوئي شغال ومتصل بجهازك..', side: "top", align: 'center' }},
                { element: 'button[name="save"]', popover: { title: 'الحفظ', description: 'اضغط لحفظ البيانات والخروج.', side: "top", align: 'center' }},
                { element: 'button[name="save_add_more"]', popover: { title: 'حفظ و إضافة المزيد', description: 'اضغط لحفظ البيانات والقيام بادخال اخر جديد دون الرجوع الى القائمة السابقة.', side: "top", align: 'center' }},
            ];
        }
        // Fallback
        else {
            steps = [
                { element: '#sidebar', popover: { title: 'القائمة الجانبية', description: 'استخدم القائمة للتنقل.', side: "left", align: 'start' }},
                { element: '#mainContent', popover: { title: 'المحتوى', description: 'محتوى الصفحة الحالي.', side: "top", align: 'center' }},
            ];
        }
        
        // Filter out steps where element doesn't exist
            return steps.filter(step => document.querySelector(step.element));
    }

    // Driver instance will be created on click
    // const driverObj = driver({...}); removed to avoid stale config

    // Hack: Force LTR for Driver.js popovers to prevent positioning bugs in RTL layout
    // Check if style already exists to avoid duplication
    if (!document.getElementById('driver-rtl-fix')) {
        const style = document.createElement('style');
        style.id = 'driver-rtl-fix';
        style.innerHTML = `
            .driver-popover {
                /* Reset direction for positioning calculations */
                direction: ltr !important; 
                
                /* Force high z-index and fixed positioning */
                z-index: 2147483647 !important;
                position: fixed !important;
                
                /* CRITICAL: Reset right/bottom defaults in RTL to allow top/left to function */
                right: auto !important;
                bottom: auto !important;
                
                /* Styling */
                background-color: #fff !important;
                color: #333 !important;
                border: 1px solid #ddd !important;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
                border-radius: 5px !important;
                min-width: 250px !important;
                max-width: 300px !important;
            }
            
            /* Ensure content inside uses RTL for Arabic text */
            .driver-popover-title, .driver-popover-description {
                direction: rtl !important;
                text-align: right !important;
                font-family: 'Shabwa', sans-serif !important;
                color: #333 !important;
            }
            
            .driver-popover-title {
                font-weight: bold !important;
                font-size: 1.1rem !important;
                margin-bottom: 8px !important;
            }
            
            .driver-popover-arrow {
                content: '' !important;
                display: none !important; /* Hide arrow as it often causes misalignments in hacks */
            }

            /* Hide Default Footer and Buttons Aggressively */
            .driver-popover-footer,
            .driver-popover-progress-text,
            .driver-popover-navigation-btns,
            .driver-popover-prev-btn,
            .driver-popover-next-btn,
            .driver-popover-close-btn {
                display: none !important;
                opacity: 0 !important;
                visibility: hidden !important;
                pointer-events: none !important;
            }

            /* Custom Controls Bar */
            #tutorial-controls {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                width: 100vw;
                background-color: rgba(255, 255, 255, 0.95);
                border-top: 1px solid #dee2e6;
                padding: 15px 0;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 20px;
                z-index: 2147483648; /* Higher than popover */
                box-shadow: 0 -4px 12px rgba(0,0,0,0.05);
                backdrop-filter: blur(5px);
                direction: ltr;
                animation: slideUp 0.3s ease-out;
            }
            
            @keyframes slideUp {
                from { transform: translateY(100%); }
                to { transform: translateY(0); }
            }

            .tut-btn {
                border: none;
                border-radius: 50px;
                padding: 8px 20px;
                font-family: 'Shabwa', sans-serif;
                font-size: 0.95rem;
                cursor: pointer;
                transition: all 0.2s;
                font-weight: bold;
            }

            .tut-btn-next {
                background-color: #3b82f6;
                color: white;
                box-shadow: 0 2px 5px rgba(59, 130, 246, 0.3);
            }
            .tut-btn-next:hover { background-color: #2563eb; transform: translateY(-1px); }

            .tut-btn-prev {
                background-color: #f3f4f6;
                color: #4b5563;
                border: 1px solid #e5e7eb;
            }
            .tut-btn-prev:hover { background-color: #e5e7eb; }
            .tut-btn-prev:disabled { opacity: 0.5; cursor: not-allowed; }

            .tut-btn-skip {
                background-color: transparent;
                color: #ef4444;
                border: 1px solid #fecaca;
            }
            .tut-btn-skip:hover { background-color: #fef2f2; }

            .tut-progress {
                font-family: 'Shabwa', sans-serif;
                color: #4b5563;
                font-weight: bold;
                min-width: 60px;
                text-align: center;
            }
        `;

        document.head.appendChild(style);
    }

    const startTourBtn = document.getElementById('start-tour');
    if (startTourBtn) {
        startTourBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const steps = getTutorialSteps();
            
            if (steps.length === 0) {
                console.warn('No tutorial steps found for this page.');
                return;
            }

            // Instantiate Driver on click to ensure fresh config
            
            // Helper to get active index since getActiveIndex() availability varies
            let currentIndex = 0;

            // Create Custom UI if not exists
            let controls = document.getElementById('tutorial-controls');
            if (!controls) {
                controls = document.createElement('div');
                controls.id = 'tutorial-controls';
                controls.innerHTML = `
                    <span id="tut-progress" class="tut-progress"></span>
                    <div style="display: flex; gap: 10px;">
                        <button id="tut-prev" class="tut-btn tut-btn-prev">السابق</button>
                        <button id="tut-next" class="tut-btn tut-btn-next">التالي</button>
                        <button id="tut-skip" class="tut-btn tut-btn-skip">إلغاء</button>
                    </div>
                `;
                document.body.appendChild(controls);
            }
            controls.style.display = 'flex';

            const driverObj = driver({
                showProgress: false, // We handle it manually
                showButtons: [], // Hide default buttons if possible via config
                steps: steps,
                onHighlightStarted: (element, step, options) => {
                    // Update UI
                    // Try to find index of current step in steps array
                    // Since steps are objects, simple indexOf might fail if cloned, but let's try direct object ref first or rely on internal tracking
                    // driverObj.getActiveIndex() is best if available.
                    
                    try {
                        currentIndex = driverObj.getActiveIndex();
                    } catch (e) {
                         // Fallback if needed, but it should be there in recent versions
                    }

                    updateControls();
                },
                onDestroyStarted: () => {
                    controls.style.display = 'none';
                    driverObj.destroy();
                },
                onCloseClick: () => {
                     controls.style.display = 'none';
                     driverObj.destroy();
                }
            });

            // Bind Actions
            document.getElementById('tut-next').onclick = () => {
                if (currentIndex === steps.length - 1) {
                    controls.style.display = 'none';
                    driverObj.destroy();
                } else {
                    driverObj.moveNext();
                }
            };
            document.getElementById('tut-prev').onclick = () => driverObj.movePrevious();
            document.getElementById('tut-skip').onclick = () => {
                controls.style.display = 'none';
                driverObj.destroy();
            };

            function updateControls() {
                const total = steps.length;
                const isLast = currentIndex === total - 1;
                const isFirst = currentIndex === 0;

                document.getElementById('tut-progress').innerText = `${currentIndex + 1} من ${total}`;
                
                const nextBtn = document.getElementById('tut-next');
                const prevBtn = document.getElementById('tut-prev');

                nextBtn.innerText = isLast ? 'إنهاء' : 'التالي';
                prevBtn.disabled = isFirst;
            }
            
            driverObj.drive();
        });
    }
});
