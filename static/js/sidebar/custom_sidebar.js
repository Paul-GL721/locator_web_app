$(document).ready(function () {

    $("#sidebar").mCustomScrollbar({
         theme: "minimal"
    });

    $('#sidebarCollapse').on('click', function () {
        // open or close navbar
        $('#sidebar').toggleClass('active');
        $('#content').toggleClass('active');

        // Change button text based on sidebar state
        if ($('#sidebar').hasClass('active')) {
            $('#sidebarCollapse span').text('Show Menu');
        } else {
            $('#sidebarCollapse span').text('Hide Menu');
        }

        // close dropdowns
        $('.collapse.in').toggleClass('in');
        // and also adjust aria-expanded attributes we use for the open/closed arrows
        // in our CSS
        $('a[aria-expanded=true]').attr('aria-expanded', 'false');
    });

});
  