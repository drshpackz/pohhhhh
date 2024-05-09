// Function to check for updates in bag count and delivered count for a specific flight
    function checkForUpdates(flightId) {
        var bagDeliveredSpan = document.getElementById("bag-delivered-" + flightId);
        var bagCountSpan = document.getElementById("bag-count-" + flightId);
        
        var deliveredCount = parseInt(bagDeliveredSpan.textContent);
        var bagCount = parseInt(bagCountSpan.textContent);
        
        // Check if there's a change in counts
        if (deliveredCount !== 0 || bagCount !== 0) {
            // Reload the page to reflect the changes
            location.reload();
        }
    }

    // Call the function for a specific flight
    function checkForUpdatesForFlight(flightId) {
        // Check for updates for the specified flight
        checkForUpdates(flightId);
        
        // Remove the event listener for this flight to avoid continuous checks
        var bagDeliveredSpan = document.getElementById("bag-delivered-" + flightId);
        bagDeliveredSpan.removeEventListener("DOMSubtreeModified", updateHandler);
        var bagCountSpan = document.getElementById("bag-count-" + flightId);
        bagCountSpan.removeEventListener("DOMSubtreeModified", updateHandler);
    }

    // Function to handle updates
    function updateHandler(event) {
        var flightId = event.target.id.replace("bag-delivered-", "").replace("bag-count-", "");
        checkForUpdatesForFlight(flightId);
    }

    // Add event listeners to each flight on page load
    document.addEventListener("DOMContentLoaded", function() {
        var flights = document.querySelectorAll("[id^='bag-delivered-'], [id^='bag-count-']");
        flights.forEach(function(flight) {
            flight.addEventListener("DOMSubtreeModified", updateHandler);
        });
    });