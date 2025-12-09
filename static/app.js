// static/app.js
const App = (() => {
	// Initialize city search input with autocomplete
	function initCitySearch() {
		const input = document.getElementById("cityInput");
		const resultsBox = document.getElementById("cityInputResults");

		if (!input || !resultsBox) return; // prevents crashes

		let debounceTimer;

		// Hide dropdown when clicking outside
		document.addEventListener("click", (e) => {
			if (!input.contains(e.target) && !resultsBox.contains(e.target)) {
			resultsBox.classList.add("hidden");
			}
		});

		// Prevent inside clicks from closing it
		input.addEventListener("click", (e) => {
			e.stopPropagation();
			// Show again
			if (resultsBox.children.length > 0) {
				resultsBox.classList.remove("hidden");
			}
		});
		resultsBox.addEventListener("click", (e) => e.stopPropagation());

		// Hide on Escape key
		input.addEventListener("keydown", (e) => {
			if (e.key === "Escape") {
			resultsBox.classList.add("hidden");
			input.blur();
			}
		});

		input.addEventListener("input", () => {
			clearTimeout(debounceTimer);

			const query = input.value.trim();
			if (!query) {
			resultsBox.innerHTML = "";
			resultsBox.classList.add("hidden");
			return;
			}

			debounceTimer = setTimeout(async () => {
			try {
				const res = await fetch(`/api/cities?city=${encodeURIComponent(query)}`);
				if (!res.ok) throw new Error("API error");

				const cities = await res.json();
				resultsBox.innerHTML = "";

				if (!cities.length) {
				resultsBox.classList.add("hidden");
				return;
				}

				cities.forEach(city => {
				const li = document.createElement("li");
				li.textContent = city;
				li.className = "px-4 py-2 hover:bg-gray-700 cursor-pointer rounded-lg";

				// On click, set input value and redirect
				li.onclick = (e) => {
					e.stopPropagation(); // prevent outside click handler
					input.value = city;
					resultsBox.classList.add("hidden");
					window.location.href = '/?city=' + encodeURIComponent(city);
				};

				resultsBox.appendChild(li);
				});

				resultsBox.classList.remove("hidden");
			} catch (err) {
				console.error("City search failed:", err);
			}
			}, 250);
		});
	}

	// Get user's location and redirect to weather page
	function getLocation() {
		const options = {enableHighAccuracy: true, timeout: 5000, maximumAge: 0};
		
		function success(pos) {
			const crd = pos.coords;
			// Get city name
			async function city() {
				// Redirect to weather page
				window.location.href = '/?lat=' + crd.latitude + '&lon=' + crd.longitude;
			}
			city();
		}
		
		function error(err) {
			window.location.href = '/?lat=&lon=';
			console.warn(`ERROR(${err.code}): ${err.message}`);
		}
		
		navigator.geolocation.getCurrentPosition(success, error, options); 
	}

	// Public API
	return {
		initCitySearch,
		getLocation,
	};

})();
