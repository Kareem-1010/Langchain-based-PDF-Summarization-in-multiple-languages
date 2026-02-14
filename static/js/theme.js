// Theme Management
(function() {
    const THEME_KEY = 'pdf-summarizer-theme';
    
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
    
    // Apply theme immediately to avoid flash
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const themeToggle = document.getElementById('themeToggle');
        
        if (themeToggle) {
            // Set initial state
            updateThemeIcon(savedTheme);
            
            // Toggle theme on click
            themeToggle.addEventListener('click', function() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                setTheme(newTheme);
            });
        }
    });
    
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
        updateThemeIcon(theme);
    }
    
    function updateThemeIcon(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            if (theme === 'dark') {
                themeToggle.setAttribute('title', 'Switch to Light Mode');
            } else {
                themeToggle.setAttribute('title', 'Switch to Dark Mode');
            }
        }
    }
})();
