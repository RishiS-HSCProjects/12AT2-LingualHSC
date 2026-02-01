document.addEventListener("DOMContentLoaded", () => {
    const items = document.querySelectorAll(".lesson-item");
    const searchInput = document.getElementById("lesson-search-input");
    const emptyBox = document.querySelector(".lesson-empty");

    // Build searchable data from lesson items
    const lessonsData = Array.from(items).map(item => { // Map DOM elements to data objects
        const content = item.dataset.content || "";

        // Objects include slug, title, summary, content, and the original element
        return {
            slug: item.dataset.slug,
            title: item.dataset.title || "",
            summary: item.dataset.summary || "",
            content: content,
            element: item
        };
    });

    // Initialize Fuse.js for fuzzy search on lessons
    const fuse = new Fuse(lessonsData, {

        // The weight attribute allows us to order results by possible relevance.
        // Higher weight = more likely to be the intended match.
        /* This is a very simple configuration, however, sufficient for the basic
            searching of small lesson datasets. */

        keys: [
            { name: "title", weight: 2 },
            { name: "summary", weight: 1.5 },
            { name: "content", weight: 1 }
        ],

        // Fuzzy search allows for typos and partial matches to deliver a result.
        // This means that users can find lessons even if they don't type the exact words present.

        threshold: 0.6,              // 0.6 / 1 => Somewhat strict, restricts irrelevant results
        ignoreLocation: true,        // Search entire string, not just beginning
        minMatchCharLength: 1,       // Match single characters
        includeScore: true,          // Include score within HTML. Required because we sort by score.
        useExtendedSearch: false,    /* This settings allows for the use of special characters in the search
                                        query for advanced searching (e.g. quotes for exact matches). This is
                                        unnecessary due to how small the search grid is, thus it is disabled as
                                        it unnecessarily makes the search slower. */
        findAllMatches: false,       // Stops at the first match as we only need to know if it matches or not.
        shouldSort: true             // Sorts by score / relevance
    });

    // Add click event listeners to lesson items
    // If a lesson item is clicked, navigate to the lesson page.
    items.forEach(item => {
        item.addEventListener("click", () => {
            const slug = item.dataset.slug;
            const url = lessonUrl.replace("__SLUG__", encodeURIComponent(slug));
            window.location.href = url;
        });
    });

    // Helper: hide categories that have no visible lessons
    const updateCategoryVisibility = () => {
        const separators = document.querySelectorAll(".lesson-category-separator");
        let anyVisible = false;

        separators.forEach(sep => {
            // Get all visible lesson items in this category
            const grid = sep.querySelector(".lesson-category-grid");
            const visibleItems = Array.from(grid.querySelectorAll(".lesson-item"))
                .filter(item => item.style.display !== "none");

            if (visibleItems.length === 0) {
                // Hide category if no visible lessons
                sep.style.display = "none";
            } else {
                // Show category if it has visible lessons
                sep.style.display = "";
                anyVisible = true; // Set flag if any category is visible
            }
        });

        // Show or hide the "No lessons found" box
        emptyBox.style.display = anyVisible ? "none" : "";
    };

    // Add search functionality
    if (searchInput) {
        let debounceTimer; // Timer for debouncing input events. Prevents excessive searches on every keystroke.

        // Auto-focus search box on page load
        searchInput.focus();

        searchInput.addEventListener("input", (e) => {
            clearTimeout(debounceTimer);

            debounceTimer = setTimeout(() => {
                const query = e.target.value.trim(); // Get trimmed search query

                if (!query) {
                    // Reset to original order when search is empty
                    items.forEach(item => {
                        item.style.display = "";
                        item.style.order = "";
                    });

                    // Reset category order
                    document.querySelectorAll(".lesson-category-separator")
                        .forEach(sep => sep.style.order = "");

                    updateCategoryVisibility();
                    return;
                }

                // Perform fuzzy search and get scores
                const results = fuse.search(query);
                const resultMap = new Map(results.map(r => [r.item.slug, r.score || 1]));

                // Show matching items with sorted order, hide others
                items.forEach(item => {
                    const score = resultMap.get(item.dataset.slug);
                    if (score !== undefined) {
                        item.style.display = "";
                        // Use score as order (multiply by 1000 for finer granularity)
                        item.style.order = String(Math.floor(score * 1000));
                    } else {
                        item.style.display = "none";
                        item.style.order = "9999"; // Push non-matching items to the end (9999 is arbitrary large number)
                    }
                });

                // Sort categories by their best (lowest) score
                const separators = document.querySelectorAll(".lesson-category-separator");

                separators.forEach(sep => {
                    const grid = sep.querySelector(".lesson-category-grid");
                    const categoryItems = Array.from(grid.querySelectorAll(".lesson-item"));

                    const visibleScores = categoryItems
                        .map(item => resultMap.get(item.dataset.slug))
                        .filter(score => score !== undefined);

                    if (visibleScores.length > 0) {
                        const bestScore = Math.min(...visibleScores); // Best (lowest) score in this category
                        sep.style.order = String(Math.floor(bestScore * 1000)); // Set order based on best score
                    } else {
                        sep.style.order = "9999"; // No matches in this category
                    }
                });

                updateCategoryVisibility();
            }, 100); // 100ms debounce delay
        });
    }

    // Initial check (handles case where directory is empty before searching)
    updateCategoryVisibility();
});
