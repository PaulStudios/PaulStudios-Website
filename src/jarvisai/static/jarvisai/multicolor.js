document.addEventListener('DOMContentLoaded', function() {
    const heading = document.getElementById('flashy_heading');

    // Function to toggle alternate animation class
    function toggleAlternateAnimation() {
        heading.classList.toggle('alternate');
    }

    // Set an interval to toggle the animation class every 5 seconds
    setInterval(toggleAlternateAnimation, 5000);
});
