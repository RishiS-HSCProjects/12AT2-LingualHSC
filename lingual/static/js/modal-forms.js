const modalRegistry = new Map(); // Mapping of cached modals for quick retrieval
let activeModalId = null; // ID of currently opened modal
let lastActiveElement = null; // HTMLElement of last active element (before modal opened)

/**
 * Get the ID of the modal div.
 * Appropriate ID exists in one of the locations queried below.
 * @returns {string} None if no id found
 */
function getModalId(modalElement) {
	if (!modalElement) return null;
	const dataId = modalElement.getAttribute('data-modal-id'); // Get modal id
	if (dataId) return dataId; // If ID found, return

	const form = modalElement.querySelector('form'); // look for form
	if (form && form.id) return form.id; // get form id

	if (modalElement.id) return modalElement.id; // get element id

	return null;
}

/**
 * Save modal id to map for quick retrieval.
 * This should happen on instantiation.
 * 
 * @returns {string} Modal ID from element, or null if not found.
 */
function saveModal(modalElement) {
	const modalId = getModalId(modalElement);
	if (!modalId) {
		console.warn('Modal missing data-modal-id and form id.');
		return null;
	}

	modalElement.setAttribute('data-modal-id', modalId); // Set modal id (if doesn't exist)
	modalElement.setAttribute('aria-hidden', 'true'); // Class modal as non-interactive

	modalRegistry.set(modalId, modalElement); // Add to map
	initModalHandlers(modalElement, modalId); // Initialise
	return modalId;
}

/**
 * Helper function to save modal to mapper by passing modal HTML.
 * This simplifies processes of finding an appropriate element and getting its ID.
 */
function saveModalFromHtml(modalHtml) {
	if (!modalHtml) return null; // Falsy html.

	const template = document.createElement('template'); // Placeholder template for document querying
	template.innerHTML = modalHtml.trim(); // Remove potential blank spaces before/after html
	const modalElement = template.content.querySelector('.modal-container'); // Query template for modal element

	if (!modalElement) { // No modal found
		console.warn('No modal container found in modal HTML.');
		return null;
	}

	/* 	Append modal element to the modal roots to easily open/close them.
		Modal root not existing means the template does not extend app-container.html,
		so something would be horribly wrong. In that case, cancel the event and throw
		error.
	*/
	const root = document.getElementById('modal-root');
	if (!root) throw new Error("#modal-root not found.");

	root.appendChild(modalElement);

	return saveModal(modalElement); // Map element
}

/**
 * Opens modal using ID or element
 */
function openModal(modal) {
	const modalElement = resolveModal(modal); // Get the modal element (resolves from id/element input)
	if (!modalElement) {
		console.error('Modal not found: ' + modal)
		return;
	}

	const modalId = getModalId(modalElement);
	if (!modalId) return; // Shouldn't ever reach here due to previous checks.

	lastActiveElement = document.activeElement; // Set last active
	activeModalId = modalId; // Store modal ID

	modalElement.classList.add('is-active'); // Add active class
	modalElement.setAttribute('aria-hidden', 'false'); // Make screenreaders see this

	// If an element can be focused on, focus on it.
	const focusElement = modalElement.querySelector('input, select, textarea, button');
	if (focusElement) {
		focusElement.focus();
	}
}

/**
 * Closes active modal (if exists) and resets active modal id.
 * Also puts focus back on last active element.
 */
function closeActiveModal() {
	const modal = resolveModal(activeModalId); // Get active modal from storage.
	if (!modal) return; // Could not find modal

	modal.classList.remove('is-active'); // Set inactive
	modal.setAttribute('aria-hidden', 'true');

	if (activeModalId && getModalId(modal) === activeModalId) {
		activeModalId = null; // Reset active modal id
	}

	if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
		lastActiveElement.focus(); // Put focus back on previous element
	}
}

/**
 * Converts modal id / HTML element to HTML element
 * 
 * @returns {HTMLElement}
*/
function resolveModal(modal) {
	if (!modal) return null;

	if (typeof modal === 'string') { // Modal is ID
		return modalRegistry.get(modal) || // See if ID is registered (should be)
			document.querySelector(`.modal-container[data-modal-id="${modal}"]`); // Query first container with id 'modal'
	}

	if (modal instanceof HTMLElement) { // Modal is element
		return modal.closest('.modal-container') || modal; // Return the div of class modal-container or modal (as is)
	}

	return null; // Could not resolve. 
}

/**
 * Initialise modal form handlers
*/
function initModalHandlers(modalElement, modalId) {
	if (!modalElement || modalElement.dataset.modalReady === 'true') return; // Exit early to avoid double registration
	modalElement.dataset.modalReady = 'true'; // Set modal ready flag

	// If clicked outside, close modal
	modalElement.addEventListener('click', (event) => {
		if (event.target === modalElement) {
			closeActiveModal();
		}
	});

	const closeButtons = modalElement.querySelectorAll('[data-modal-close]'); // Get close buttons
	closeButtons.forEach((btn) => {
		btn.addEventListener('click', () => closeActiveModal()); // Add click listeners 
	});
}

document.addEventListener('DOMContentLoaded', () => {
	document.querySelectorAll('.modal-container').forEach((modalElement) => saveModal(modalElement)); // Save all modals
	document.querySelectorAll('[data-modal-auto-open="true"]').forEach((modalElement) => { // Get modals with auto-open set to true
		const modalId = getModalId(modalElement);
		if (modalId) openModal(modalId); // Open modal
	});

	// Remove type query parameter from URL
	// to avoid reopening modals on page reload
	const url = new URL(window.location.href);
	if (url.searchParams.has('type')) {
		url.searchParams.delete('type');
		const nextUrl = url.pathname + (url.search ? url.search : '') + url.hash;
		window.history.replaceState({}, '', nextUrl);
	}

	document.addEventListener('keydown', (event) => {
		if (event.key === 'Escape' && activeModalId) {
			closeActiveModal(); // Close active modal on escape pressed.
		}
	});
});

// Globally assign functions 
window.openModal = openModal;
window.closeActiveModal = closeActiveModal;
window.saveModalFromHtml = saveModalFromHtml;
