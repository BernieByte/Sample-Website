document.addEventListener('DOMContentLoaded', () => {
    const items = document.querySelectorAll('.reveal');

    items.forEach((item, index) => {
        item.style.animationDelay = `${index * 120}ms`;
    });

    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach((link) => {
        const href = link.getAttribute('href');
        if (href === '#') {
            link.addEventListener('click', (event) => event.preventDefault());
        }
    });

    const actionButtons = document.querySelectorAll('.btn');
    actionButtons.forEach((button) => {
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
        });
    });
});
