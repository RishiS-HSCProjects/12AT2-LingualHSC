// PLEASE NOTE
// Some of the concept and structures were generated using AI.
// Specifically, smoothness logic and the Intersection Observer implementation were
// written with the help of ChatGPT. Refer to AI declaration.

document.addEventListener("DOMContentLoaded", () => {
    // Assign DOM elements to constants for faster access
	const page = document.getElementById("kanji-page");
	const grid = document.getElementById("kanji-grid");
	const blocks = Array.from(document.querySelectorAll(".kanji-block"));
	const panel = document.getElementById("kanji-info");
	const closeButton = document.getElementById("kanji-info-close");

	const infoChar = document.getElementById("kanji-info-char");
	const infoPrimary = document.getElementById("kanji-info-primary");
	const infoMeanings = document.getElementById("kanji-info-meanings");
	const infoOnyomi = document.getElementById("kanji-info-onyomi");
	const infoKunyomi = document.getElementById("kanji-info-kunyomi");

	if (!page || !grid || blocks.length === 0 || !panel) {
        console.error("Essential kanji elements are missing from the DOM.");
		return; // Essential elements are missing, so we exit early to avoid errors.
	}

    /** Parses a comma-separated or JSON-formatted string into an array */
	const parseList = (value) => {
		if (!value) {
			return []; // Return an empty array if the value is falsy (null, undefined, empty string)
		}

		try {
			const parsed = JSON.parse(value); // Attempt to parse as JSON first (handles both arrays and single values)
			return Array.isArray(parsed) ? parsed : [parsed]; // Ensure the result is always an array
		} catch (error) { // If JSON parsing fails, fallback to comma-separated parsing
			return value
				.split(",")
				.map((item) => item.trim())
				.filter(Boolean);
		}
	};

	const setActive = (activeBlock) => {
		blocks.forEach((block) => block.classList.remove("is-active")); // Remove all other active states
		activeBlock.classList.add("is-active"); // Set the clicked block as active
	};

	const openPanel = () => {
		page.classList.add("panel-open"); // Add class to body to trigger CSS changes for panel visibility
		panel.setAttribute("aria-hidden", "false"); // Update ARIA attribute for accessibility
	};

	const closePanel = () => {
		page.classList.remove("panel-open"); // Remove class to hide the panel
		panel.setAttribute("aria-hidden", "true"); // Update ARIA attribute for accessibility
		blocks.forEach((block) => block.classList.remove("is-active")); // Remove all active states when closing the panel
	};

    /** Updates the information panel with data from the selected kanji block */
	const updatePanel = (block) => {
        // Get data attributes or default to empty strings/arrays if not present
		const kanji = block.dataset.kanji || "";
		const primary = block.dataset.primary || "";
		const meanings = parseList(block.dataset.meanings);
		const onyomi = parseList(block.dataset.onyomi);
		const kunyomi = parseList(block.dataset.kunyomi);

		infoChar.textContent = kanji;
		infoPrimary.textContent = primary ? `Primary: ${primary}` : "Primary: N/A";
		infoMeanings.textContent = meanings.length ? meanings.join(", ") : "No meanings listed.";
		infoOnyomi.textContent = onyomi.length ? onyomi.join(" ・ ") : "No on'yomi recorded.";
		infoKunyomi.textContent = kunyomi.length ? kunyomi.join(" ・ ") : "No kun'yomi recorded.";
	};

	blocks.forEach((block) => {
        // Add click event listener to each kanji block to handle selection and panel updates
		block.addEventListener("click", () => {
			setActive(block); // Set the clicked block as active
			updatePanel(block); // Update panel info
			openPanel(); // Open the information panel (if not already open)
			block.scrollIntoView({ // Smoothly scroll the selected block into view, centered in the viewport
				behavior: "smooth",
				block: "center",
				inline: "center"
			});
		});
	});

	if (closeButton) {
		closeButton.addEventListener("click", () => {
			closePanel(); // Close the information panel when the close button is clicked
		});
	}

	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape") {
			closePanel(); // Close the information panel when the Escape key is pressed
		}
	});

    // Intersection Observer to add "is-visible" class to kanji blocks as they enter the
    // viewport for animation effects. This implementation uses the Intersection Observer
    // API to efficiently detect when kanji blocks enter the viewport. When a block
    // becomes visible, it adds the "is-visible" class, which can trigger CSS animations
    // or transitions. The observer is configured with a root margin to start the animation
    // slightly before the block fully enters the view, creating a smoother user experience.
    // If the browser does not support Intersection Observer, all blocks are made visible
    // immediately as a fallback.
	if ("IntersectionObserver" in window) {
		const observer = new IntersectionObserver(
			(entries, entryObserver) => { // Loop through observed entries to check if they are intersecting (visible in the viewport)
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						entry.target.classList.add("is-visible"); // Add class to trigger visibility/animation
						entryObserver.unobserve(entry.target); // Stop observing this block since it's already visible.
					}
				});
			},
			{
				root: document.getElementById("kanji-list"), // Set the root to the scrollable container of the kanji blocks
				rootMargin: "60px", // Start the animation slightly before the block fully enters the view for a smoother effect
				threshold: 0.2 // Trigger when 20% of the block is visible in the viewport
			}
		);

		blocks.forEach((block) => observer.observe(block)); // Start observing each kanji block for visibility changes
	} else {
		blocks.forEach((block) => block.classList.add("is-visible")); // Fallback for browsers that do not support Intersection Observer: make all blocks visible immediately
	}
});
