// Tab-switching logic for index.html
document.addEventListener('DOMContentLoaded', () => {
    const tabs     = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // activate clicked tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // show corresponding panel
            contents.forEach(c => {
                c.classList.toggle('active', c.id === tab.dataset.target);
            });
        });
    });
});

// —— contact modal —— //
document.addEventListener('DOMContentLoaded', () => {
    const contactLink = document.getElementById('contact-link');
    const overlay     = document.getElementById('contactModal');
    const closeBtn    = document.getElementById('closeModal');

    // open
    contactLink.addEventListener('click', e => {
        e.preventDefault();
        overlay.style.display = 'flex';
        overlay.setAttribute('aria-hidden', 'false');
    });

    // close button
    closeBtn.addEventListener('click', () => {
        overlay.style.display = 'none';
        overlay.setAttribute('aria-hidden', 'true');
    });

    // click outside dialog closes too
    overlay.addEventListener('click', e => {
        if (e.target === overlay) closeBtn.click();
    });

    // (esc key optional)
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && overlay.getAttribute('aria-hidden') === 'false')
            closeBtn.click();
    });
});

