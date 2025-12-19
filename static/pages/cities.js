const CitiesPage = (() => {
    //Initialize the cities page
    // Sets up click handlers for city cards and restores last selection
    const init = () => {
        const cards = document.querySelectorAll(".city-card");
        if (!cards.length) return;
        
        // Attach click handler to each city card
        cards.forEach(card => {
            card.addEventListener("click", () => {
                setActive(card);
                const data = getPayload(card);
                renderSide(data);
                remember(card);
            });
        });
        
        // Restore previously selected city or select first by default
        restore(cards);
    };

    // Extract weather data payload from a city card
    const getPayload = (card) => {
        return JSON.parse(
            card.querySelector(".city-payload").textContent
        );
    };

    // Tailwind classes applied to the active city card
    const ACTIVE_CLASSES = ["ring-1", "ring-blue-500", "bg-transparent"];

    // Mark a city card as active and remove active state from others
    const setActive = (activeCard) => {
        // Remove active styling from all cards
        document.querySelectorAll(".city-card")
            .forEach(c => c.classList.remove(...ACTIVE_CLASSES));
        
        // Add active styling to selected card
        activeCard.classList.add(...ACTIVE_CLASSES);
    };

    // Render weather data in the sidebar
    const renderSide = ({ city, weather_current, forecast_3hour, forecast_daily }) => {
        // Update current weather display
        document.getElementById("city").textContent = city.name;
        document.getElementById("description").textContent = weather_current.description;
        document.getElementById("current-temp").textContent = weather_current.feels_like;
        document.getElementById("current-icon").style.backgroundImage = `url('${weather_current.icon}')`;
        
        // Render forecast sections
        render3hourly(forecast_3hour);
        renderDaily(forecast_daily);
    };

    // Render 3-hour forecast blocks
    const render3hourly = (blocks) => {
        const container = document.getElementById("hourly-container");
        container.innerHTML = "";
        
        blocks.forEach(h => {
            container.insertAdjacentHTML("beforeend", `
                <div class="flex flex-col items-center justify-between min-w-[100px] p-1">
                    <p class="text-xs">${h.time}</p>
                    <div class="flex flex-1 w-full p-3 items-center justify-center">
                        <img src="${h.icon}" class="w-full aspect-square object-contain">
                    </div>
                    <p class="text-white text-lg font-semibold">${h.feels_like}</p>
                </div>
            `);
        });
    };

    // Render daily forecast blocks
    const renderDaily = (days) => {
        const container = document.getElementById("daily-container");
        container.innerHTML = "";
        
        days.forEach(d => {
            container.insertAdjacentHTML("beforeend", `
                <div class="flex items-center p-2">
                    <span class="flex-1 text-xs">${d.day}</span>
                    <div class="flex items-center flex-1 gap-4">
                        <img src="${d.icon}" class="size-16">
                        <span class="text-gray-200">${d.main}</span>
                    </div>
                    <span class="flex-1 text-end">
                        <span class="text-gray-300">${d.temp_max}</span>
                        <span>/${d.temp_min}</span>
                    </span>
                </div>
            `);
        });
    };

    // Save the selected city to localStorage
    const remember = (card) => {
        localStorage.setItem("lastCity", card.dataset.key);
    };

    // Restore last selected city or default to first
    // Resets selection if the list of cities has changed
    const restore = (cards) => {
        if (!cards.length) return;
        
        // Create signature of current city list (all keys joined)
        const currentSig = Array.from(cards)
            .map(c => c.dataset.key)
            .join("|");
        const savedSig = localStorage.getItem("citiesSig");
        const lastKey = localStorage.getItem("lastCity");
        
        // If city list changed, reset to first city
        if (savedSig !== currentSig) {
            localStorage.setItem("citiesSig", currentSig);
            localStorage.removeItem("lastCity");
            cards[0].click();
            return;
        }
        
        // If city list unchanged, restore last selection
        if (lastKey) {
            const el = document.querySelector(`.city-card[data-key="${lastKey}"]`);
            if (el) {
                el.click();
                return;
            }
        }
        
        // Fallback to first city
        cards[0].click();
    };

    // Public API
    return { init };
})();
