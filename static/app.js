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
				const res = await fetch(`/api/cities?q=${encodeURIComponent(query)}`);
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

				li.onclick = (e) => {
					e.stopPropagation(); // prevent outside click handler
					input.value = city;
					resultsBox.classList.add("hidden");
					window.location.href = '/weather?q=' + encodeURIComponent(city);
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
				let response = await fetch('/api/locate?lat=' + crd.latitude + '&lon=' + crd.longitude);
				let name = await response.json();
				// Redirect to weather page
				window.location.href = '/?q=' + name[0].name;
			}
			city();
		}
		
		function error(err) {
			window.location.href = '/?q=';
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


async function display() {
	let loc = document.getElementById('location').innerText;

	// Get weather data
	let response = await fetch('/api/weather?q=' + loc);
	var weather = await response.json();

	// Error handling
	if (weather.cod == 404) {
		window.location.href = '/weather?q=error';
	}
	
	// Display temperatue
	let temp = parseInt(weather.main.temp);
	document.getElementById('temp').innerHTML = temp + '°';
	
	let min = parseInt(weather.main.temp_min);
	let max = parseInt(weather.main.temp_max);
	let range = min + '°' + ' / ' + max + '°' + ' ' + 'Feels like ' + weather.main.feels_like.toString() + '°';
	document.getElementById('range').innerHTML = range;
	
	// Display date and time
	
	// Fix date and time for floating timezone
	function timezone(minutes, hour) {
		if (!Number.isInteger(hour)) {
			let n = minutes + hour * 60;
			minutes = n % 60;
			hour = parseInt(n / 60);
			if (hour < 0) {
				hour += 24;
			}
			else if (hour > 23) {
				hour -= 24;
			}
		}
		return {'minutes': minutes, 'hour': hour}
	}
	
	// Display discription
	let _weather_icon = document.getElementById('weather_icon');
	// https://openweathermap.org/img/wn/10d@2x.png
	_weather_icon.setAttribute('src' , 'https://openweathermap.org/img/wn/' + weather.weather[0].icon + '@2x.png')
	_weather_icon.setAttribute('alt', 'weather_icon');
	document.getElementById('description').innerHTML = weather.weather[0].description.toString();

	// Display weather details
	document.getElementById('humidity').innerHTML = weather.main.humidity + '%';
	document.getElementById('pressure').innerHTML = weather.main.pressure + 'hPa';
	document.getElementById('wind').innerHTML = weather.wind.speed + 'm/s';
	document.getElementById('visibility').innerHTML = weather.visibility + 'm';
	
	// Display sunrise and sunset
	let sunrise = new Date((weather.sys.sunrise) * 1000);
	let sunset = new Date(weather.sys.sunset  * 1000);
	
	sunrise = timezone(sunrise.getUTCMinutes(), sunrise.getUTCHours() + weather.timezone / 3600);
	sunset = timezone(sunset.getUTCMinutes(), sunset.getUTCHours() + weather.timezone / 3600);
	
	document.getElementById('sunrise').innerHTML = ('0' + sunrise.hour).substr(-2)  + ':' + ('0' + sunrise.minutes).substr(-2);
	document.getElementById('sunset').innerHTML = ('0' + sunset.hour).substr(-2)  + ':' + ('0' + sunset.minutes).substr(-2);
	
	let t = new Date();
	let timestamp = timezone(t.getUTCMinutes(), t.getUTCHours() + weather.timezone / 3600);
	timestamp = ('0' + timestamp.hour).substr(-2) + ':' + ('0' + timestamp.minutes).substr(-2);
	document.getElementById('timestamp').innerHTML = timestamp
	
	// Weather forecast
	async function forecast() {
		let response = await fetch('/api/forecast?lat=' + weather.coord.lat + '&lon=' + weather.coord.lon);
		var forecast = await response.json();
		
		// Time, icon, temp, rain
		let html = '';
		let svg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-droplet-half" viewBox="0 0 16 16">'
		+ '<path fill-rule="evenodd" d="M7.21.8C7.69.295 8 0 8 0c.109.363.234.708.371 1.038.812 1.946 2.073 3.35 3.197 4.6C12.878 7.096 14 8.345 14 '
		+ '10a6 6 0 0 1-12 0C2 6.668 5.58 2.517 7.21.8zm.413 1.021A31.25 31.25 0 0 0 5.794 3.99c-.726.95-1.436 2.008-1.96 3.07C3.304 8.133 3 9.138 3'
		+ ' 10c0 0 2.5 1.5 5 .5s5-.5 5-.5c0-1.201-.796-2.157-2.181-3.7l-.03-.032C9.75 5.11 8.5 3.72 7.623 1.82z"/><path fill-rule="evenodd" d="M4.55'
		+ '3 7.776c.82-1.641 1.717-2.753 2.093-3.13l.708.708c-.29.29-1.128 1.311-1.907 2.87l-.894-.448z"/></svg>';
		for (let i = 0; i < 8; i++) {
			let time = new Date(forecast.list[i].dt * 1000);
			time = timezone(time.getUTCMinutes(), time.getUTCHours() + weather.timezone / 3600);
			time = ('0' + time.hour).substr(-2) + ':' + ('0' + time.minutes).substr(-2);
			let icon = forecast.list[i].weather[0].icon;
			let temp = forecast.list[i].main.temp;
			let rain = forecast.list[i].pop ? forecast.list[i].pop * 100 : 0;

			html += '<div class="forecast">';
			html += '<div class="time">' + time + '</div>';
			html += '<div class="icon"><img src="https://openweathermap.org/img/wn/' + icon + '@2x.png" alt="weather_icon"></div>';
			html += '<div class="temp">' + parseInt(temp) + '°' + '</div>';
			html += '<div class="rain">' + svg + ' ' + parseInt(rain) + '%</div>';
			html += '</div>';
		}
		document.getElementById('forecast').innerHTML = html;
	}
	forecast();
}
