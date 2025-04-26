$(document).ready(function() {
    //Generate a qr code which when scanned by a user will generate latitude and longititude
    var usersgrps = $('#usergrp')
    usersgrps.change(function() {
        var selectedGroup = $(this).val();
        if (selectedGroup.trim() !== "") {
            $.ajax({
                url: usersgrps.data("url"),
                type: "POST",
                data: {
                    'usergrp': selectedGroup,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    $('#qrcode-container').html(response.html);
                },
                error: function(xhr, status, error) {
                    console.error("Error generating QR code:", error);
                }
            });
        }
    });
});