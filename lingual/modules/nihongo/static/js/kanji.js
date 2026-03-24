// PLEASE NOTE
// Some of the concept and structures were generated using AI.
// Specifically, smoothness logic and the Intersection Observer implementation were
// written with the help of ChatGPT. Refer to AI declaration.

document.addEventListener("DOMContentLoaded", () => {
	// Assign DOM elements to constants for faster access
	const page = document.getElementById("kanji-page");
	const grid = document.getElementById("kanji-grid");
	const blocks = Array.from(document.querySelectorAll("#kanji-grid .kanji-block"));

	const infoChar = document.getElementById("kanji-info-char");
	const infoPrimary = document.getElementById("kanji-info-primary");
	const infoType = document.getElementById("kanji-info-type");
	const infoMeanings = document.getElementById("kanji-info-meanings");
	const infoOnyomi = document.getElementById("kanji-info-onyomi");
	const infoKunyomi = document.getElementById("kanji-info-kunyomi");
	const infoNanori = document.getElementById("kanji-info-nanori");
	/** 
	 * Client-side cache to store fetched kanji data during runtime.
	 * @see Documentation D-AE04
	 */
	const kanjiCache = new Map();

	if (!page || !grid || !blocks.length || !infoChar || !infoPrimary || !infoType || !infoMeanings || !infoOnyomi || !infoKunyomi || !infoNanori) {
		console.error("Essential kanji elements are missing from the DOM.");
		return; // Essential elements are missing, so we exit early to avoid errors.
	}

	/** Updates the information panel with data from the selected kanji block */
	const setLoadingPanel = (kanji) => {
		// Default loading state.
		infoChar.textContent = kanji;
		infoPrimary.textContent = "Data not available yet. Please try again in a moment.";
		infoType.hidden = true;
		const label = infoType.querySelector(".kanji-type-label");
		if (label) label.textContent = "";
		infoMeanings.textContent = "";
		infoOnyomi.textContent = "";
		infoKunyomi.textContent = "";
		infoNanori.textContent = "";
	};

	/**
	 * Updates the information panel with data from the fetched kanji.
	 */
	const updatePanelFromData = (kanji, payload) => {
		const data = payload?.data || {};
		const type = payload?.type || null;
		const meanings = Array.isArray(data?.meanings)
			? data.meanings.map((m) => m.meaning).filter(Boolean) // Filter out any falsy values
			: []; // Default to empty array if meanings is not an array
		const primaryMeaning = Array.isArray(data?.meanings)
			? (data.meanings.find((m) => m.primary)?.meaning || "")
			: ""; // Default to empty string if meanings is not an array
		const onyomi = Array.isArray(data?.readings)
			? data.readings.filter((r) => r.type === "onyomi").map((r) => r.reading).filter(Boolean) // Filter out any falsy values
			: []; // Default to empty array if readings is not an array
		const kunyomi = Array.isArray(data?.readings)
			? data.readings.filter((r) => r.type === "kunyomi").map((r) => r.reading).filter(Boolean) // Filter out any falsy values
			: []; // Default to empty array if readings is not an array
		const nanori = Array.isArray(data?.readings)
			? data.readings.filter((r) => r.type === "nanori").map((r) => r.reading).filter(Boolean) // Filter out any falsy values
			: []; // Default to empty array if readings is not an array
		const url = data?.document_url || "#"; // Fallback to "#" if URL is not provided

		// Set info content
		infoChar.textContent = kanji;
		if (url && url !== "#") {
			infoChar.classList.add("is-link");
			infoChar.title = "Click to view on WaniKani";
			infoChar.addEventListener("click", () => {
				// Open the kanji's document URL in a new tab if it exists
					window.open(url, "_blank");
			});
		}
		infoPrimary.textContent = primaryMeaning ? `Primary: ${primaryMeaning}` : "Primary: N/A";

		let typeLabel = infoType.querySelector(".kanji-type-label");
		if (!typeLabel) {
			typeLabel = document.createElement("span");
			typeLabel.className = "kanji-type-label";
			infoType.prepend(typeLabel);
		}

		typeLabel.textContent = type
			? `${type.toLowerCase().charAt(0).toUpperCase() + type.toLowerCase().slice(1)}`
			: "Passive"; // Fallback. Implemented in case we want to add more kanji in the future.

		infoType.hidden = !primaryMeaning; // Hide if data not fetched
		infoType.classList.remove("type-active", "type-recognition");
		if (type) infoType.classList.add(`type-${type.toLowerCase()}`);

		/** Help text when hovering over kanji type. */
		const helpTextMap = {
			active: "You are expected to read and write this kanji.",
			recognition: "You are expected to recognise this kanji, but not necessarily write it."
		};

		const helpText = helpTextMap[type?.toLowerCase()] || "You are not expected to actively know this kanji. It may be included for reference or future learning.";
		infoType.setAttribute("data-help", helpText);

		const tooltip = infoType.querySelector(".help-tooltip");
		if (tooltip) {
			tooltip.textContent = helpText;
		} else if (typeof window.initHelpTooltips === "function") {
			window.initHelpTooltips();
		}

		infoMeanings.textContent = meanings.length ? meanings.join(", ") : "No meanings listed.";
		infoOnyomi.textContent = onyomi.length ? onyomi.join(" ・ ") : "No on'yomi recorded.";
		infoKunyomi.textContent = kunyomi.length ? kunyomi.join(" ・ ") : "No kun'yomi recorded.";
		infoNanori.textContent = nanori.length ? nanori.join(" ・ ") : "No nanori recorded.";
	};

	/**
	 * Fetches kanji data from the server API.
	 */
	const fetchKanjiData = async (kanji) => {
		try {
			// Fetch kanji data from the server's API
			// Encode the kanji to ensure it's safe for use in a URL (just in case)
			const res = await fetch(`api/${encodeURIComponent(kanji)}`);
			if (!res.ok) { // Handle non-OK responses
				throw new Error(`Failed to fetch kanji data: ${res.status}`); // Throw error to be caught below
			}
			return await res.json(); // Return the fetched kanji data
		} catch (error) {
			console.error("Kanji fetch failed:", error); // Log any errors during fetch
			return { status: "loading" }; // Return loading status on error
		}
	};

	/**
		This page uses a prefetch system to cache kanji elements before they are required for usage.
		https://developer.mozilla.org/en-US/docs/Glossary/Prefetch
		
		@see Documentation D-AE06
	*/

	/** Limit to how many kanji can be fetched in one request (batch). Used to reduce number of API requests. */
	const PREFETCH_BATCH_SIZE = 12;
	/** Set of kanji characters waiting to be fetched. */
	const prefetchQueue = new Set();
	/** A map linking kanji characters to DOM elements */
	const DOMToKanji = new Map();
	/** ID of setTimeout() timer to limit requests to one batch at a time. */
	let prefetchTimer = null;
	/** Flag for prefetch operation currently running. */
	let isPrefetchActive = false;

	/** Set prefetch timer (if possible) */
	const schedulePrefetch = () => {
		if (prefetchTimer) return;
		prefetchTimer = window.setTimeout(flushPrefetch, 120); // 120ms delay
	};

	/** Run prefetch and batch. */
	const flushPrefetch = async () => {
		if (isPrefetchActive) return;
		const batch = Array.from(prefetchQueue).slice(0, PREFETCH_BATCH_SIZE);
		if (!batch.length) {
			// Quit prefetch and timer
			prefetchTimer = null;
			return;
		}

		// Remove all kanji from queue
		batch.forEach((kanji) => prefetchQueue.delete(kanji));
		isPrefetchActive = true; // Currently fetching
		prefetchTimer = null;

		try {
			// Asynchronously get a response from nihongo/kanji/api/batch
			const res = await fetch("api/batch", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ kanji: batch })
			});

			if (!res.ok) throw new Error(`Failed batch fetch: ${res.status}`);

			const payload = await res.json(); // Wait for response and set payload
			const dataMap = payload?.data || {};
			// Create an object for each tile.
			Object.entries(dataMap).forEach(([kanji, data]) => {
				const block = DOMToKanji.get(kanji);
				const type = block?.dataset.category || null;
				kanjiCache.set(kanji, { data, type });
				if (block) block.dataset.loaded = "true"; // Set as loaded
			});
		} catch (error) {
			console.error("Kanji prefetch failed:", error);
		} finally {
			isPrefetchActive = false;
			if (prefetchQueue.size) schedulePrefetch(); // If queue has items, schedule prefetch
		}
	};

	/** Add kanji to queue for fetching. */
	const queuePrefetch = (kanji) => {
		if (!kanji || kanjiCache.has(kanji)) return;
		prefetchQueue.add(kanji);
		schedulePrefetch();
	};

	blocks.forEach((block) => {
		const kanji = block.dataset.kanji || "";
		if (kanji) DOMToKanji.set(kanji, block);
	});

	/** Base tile interactions (click, keyboard selection, open/close panel, visibility animation)
		are in `lingual/static/js/tiles.js`. */
	page.addEventListener("tiles:select", async (event) => { // Asynchronously run
		const { value: kanji, tileElement } = event.detail || {};
		if (!kanji) { // No kanji found in element
			setLoadingPanel(""); // Set kanji to empty (falsy) string to stylise error screen.
			return;
		}

		const cached = kanjiCache.get(kanji);
		if (cached) {
			updatePanelFromData(kanji, cached);
			return;
		}

		setLoadingPanel(kanji); // Load kanji info
		const result = await fetchKanjiData(kanji); // Wait for data fetch then continue
		if (result.status === "ready" && result.data) {
			const type = tileElement?.dataset?.category || null;
			kanjiCache.set(kanji, { data: result.data, type }); // Set cache on every run
			if (tileElement) tileElement.dataset.loaded = "true";
			updatePanelFromData(kanji, { data: result.data, type });
		}
	});

	// Prefetch nearby kanji only when they enter the viewport to reduce load.
	if ("IntersectionObserver" in window) {
		const prefetchObserver = new IntersectionObserver(
			(entries, entryObserver) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						const kanji = entry.target.dataset.kanji || "";
						queuePrefetch(kanji);
						entryObserver.unobserve(entry.target);
					}
				});
			},
			{
				root: document.getElementById("kanji-list"),
				rootMargin: "200px", // Offset by 200px for a more smooth experience.
				threshold: 0.1
			}
		);

		blocks.forEach((block) => prefetchObserver.observe(block)); // Add observer to all blocks
	}
});
