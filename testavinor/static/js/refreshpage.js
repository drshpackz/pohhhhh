<script>
    let touchStartY = 0;
    let touchCurrentY = 0;
    let isTouching = false;

    document.addEventListener('touchstart', function(e) {
        touchStartY = e.touches[0].clientY;
        isTouching = true;
    }, { passive: true });

    document.addEventListener('touchmove', function(e) {
        if (!isTouching) return;
        touchCurrentY = e.touches[0].clientY;

        // Check if the user is pulling down
        if (touchCurrentY > touchStartY + 50) { // 50px threshold for pulling down
            displayPullDownNotice(); // Function to display a visual cue
        }
    }, { passive: true });

    document.addEventListener('touchend', function(e) {
        if (touchCurrentY > touchStartY + 50) { // Same 50px threshold
            window.location.reload(); // Refresh the page
        }
        isTouching = false;
        touchStartY = 0;
        touchCurrentY = 0;
        hidePullDownNotice(); // Hide any visual cue
    }, { passive: true });

    function displayPullDownNotice() {
        // Add your code to display a notice like "Release to refresh"
    }

    function hidePullDownNotice() {
        // Add your code to remove the notice
    }
</script>
