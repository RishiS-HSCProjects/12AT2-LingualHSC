class BaseTilePage {
    constructor(page) {
        // Get elements from page and store as properties for later use.
        this.page = page;
        this.list = page.querySelector('.tiles-list');
        this.menu = page.querySelector('.tiles-menu');
        this.menuClose = page.querySelector('[data-tile-close="true"]');
        this.tiles = Array.from(page.querySelectorAll('[data-tile-trigger="true"]'));
        this.tileValueAttr = page.dataset.tileValueAttr || 'tile';

        if (!this.page || !this.list || !this.menu || !this.tiles.length) return;

        // Bind menu close logic to a HTML element
        if (this.menuClose) this.menuClose.addEventListener('click', () => this.closeMenu());

        // Add event listeners for tiles to allow keyboard interaction and navigation.
        this.tiles.forEach((tile) => {
            tile.tabIndex = 0; // Make tiles focusable
            tile.setAttribute('role', 'button') // Announce as button

            tile.addEventListener('click', () => this.selectTile(tile));
            tile.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.selectTile(tile);
                }
            });
        });

        // Add event listener for the escape key to close any open menu (if it exists).
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.page.classList.contains('menu-open')) {
                this.closeMenu();
            }
        });

        this.bindVisibilityObserver(); // Add observer for tile visibility (for animation purposes)
    }

    getTileValue(tile) {
        if (!tile) return '';
        const key = this.tileValueAttr;
        return tile.dataset[key] || '';
    }

    setActive(tile) {
        this.tiles.forEach((item) => item.classList.remove('is-active'));
        tile.classList.add('is-active');
    }

    openMenu() {
        this.page.classList.add('menu-open');
        this.menu.setAttribute('aria-hidden', 'false');

        // Call custom event to notify of menu opening, passing page and menu elements for reference.
        this.page.dispatchEvent(new CustomEvent('tiles:open', {
            bubbles: true,
            detail: {
                pageElement: this.page,
                menuElement: this.menu
            }
        }));
    }

    closeMenu() {
        this.page.classList.remove('menu-open');
        this.menu.setAttribute('aria-hidden', 'true');
        this.tiles.forEach((tile) => tile.classList.remove('is-active'));

        // Call custom event to notify of menu closing, passing page and menu elements for reference.
        this.page.dispatchEvent(new CustomEvent('tiles:close', {
            bubbles: true,
            detail: {
                pageElement: this.page,
                menuElement: this.menu
            }
        }));
    }

    selectTile(tile) {
        const value = this.getTileValue(tile);
        this.setActive(tile);
        this.openMenu();

        tile.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center'
        });

        /* Custom event called when a tile is selected */
        this.page.dispatchEvent(new CustomEvent('tiles:select', {
            bubbles: true,
            detail: {
                value,
                tileElement: tile,
                pageElement: this.page,
                menuElement: this.menu
            }
        }));
    }

    /** Helper function to bind a visibility observer. */
    bindVisibilityObserver() {
        // Skip processes if IntersectionObserver is already binded (preventing client-side functions)
        if (!('IntersectionObserver' in window)) {
            this.tiles.forEach((tile) => tile.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver(
            // When tiles come into view, add 'is-visible' class for animation and unobserve them to prevent future triggers.
            (entries, entryObserver) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('is-visible');
                        entryObserver.unobserve(entry.target);
                    }
                });
            },
            {
                root: this.list,
                rootMargin: '60px',
                threshold: 0.2
            }
        );

        this.tiles.forEach((tile) => observer.observe(tile)); // Add observer to all tiles.
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Run this logic for any page that is a tiles page (set by data attribute)
    const pages = Array.from(document.querySelectorAll('[data-tiles-page="true"]'));
    pages.forEach((page) => new BaseTilePage(page)); // Add event listeners and functionality to each page
});
