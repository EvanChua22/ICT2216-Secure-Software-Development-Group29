$(document).ready(function() {
    // Set "active" class based on the current page URL
    var current_page_URL = location.href;
    $(".navbar-nav a").each(function () {
        var target_URL = $(this).prop("href");
        if (target_URL === current_page_URL) {
            $(".navbar-nav a").removeClass("active");
            $(this).addClass("active");
            return false;
        }
    });
});
