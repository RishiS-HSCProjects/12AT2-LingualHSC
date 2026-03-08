document.addEventListener('DOMContentLoaded', () => {
    const page = document.getElementById('particles-page');
    const title = document.getElementById('particles-info-title');
    const category = document.getElementById('particles-info-category');
    const content = document.getElementById('particles-info-content');

    if (!page || !title || !category || !content) {
        console.error('Essential particle tile elements are missing from the DOM.');
        return;
    }

    // (same logic as kanji.js. I'm not going to explain all of the elements again.)
    
    const particleCache = new Map();// Map of paticle cache
    const setError = (message) => {
        content.innerHTML = `<p>${message}</p>`;
    };

    /** Render the particle info based on an api payload */
    const renderParticle = (payload) => {
        title.textContent = payload?.title || payload?.tile || 'Particle Notes';
        category.textContent = payload?.category || '';
        content.innerHTML = payload?.content_html || '<p>No content available.</p>';

        if (typeof window.initHelpTooltips === 'function') { // Failsafe in case parent js does not exist
            window.initHelpTooltips();
        } else {
            console.error("initHelpTooltips function does not exist!") // Log error
        }
    };

    /** Asynchronously fetch particle payload from API */
    const fetchParticle = async (slug) => {
        const response = await fetch(`api/${encodeURIComponent(slug)}`); // todo: document why I needed to use encodeURIComponent()
        if (!response.ok) {
            throw new Error(`Failed to load particle markdown: ${response.status}`);
        }

        const payload = await response.json();
        if (payload?.status !== 'ready' || !payload?.data) {
            throw new Error('Particle markdown payload malformed.'); // Log malformation error
        }

        return payload.data; // Return verified payload data, abstracting metainformation like status
    };

    page.addEventListener('tiles:select', async (event) => {
        const slug = event.detail?.value || '';
        if (!slug) return;

        const cached = particleCache.get(slug);
        if (cached) {
            renderParticle(cached);
            return;
        }

        // Set loading screen
        title.textContent = slug ? `Loading ${slug}...` : 'Select a particle';
        category.textContent = '';
        content.innerHTML = '<p>Loading markdown notes...</p>';

        try {
            const payload = await fetchParticle(slug);
            particleCache.set(slug, payload);
            renderParticle(payload);
        } catch (error) {
            console.error('Particle markdown fetch failed:', error);
            setError('Unable to load particle notes right now. Please try again.');
        }
    });
});
