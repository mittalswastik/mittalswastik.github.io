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
