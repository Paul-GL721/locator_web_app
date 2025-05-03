$(document).ready(function() {
    //Generate a qr code which when scanned by a user will generate latitude and longititude
    var usersgrps = $('#usergrp')
    usersgrps.change(function() {
        var selectedGroup = $(this).val();
        fullurl = $('#getdeviceposition').attr('action');
        if (selectedGroup.trim() !== "") {
            $.ajax({
                url: fullurl,
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

    $('#print-qr-btn').on('click', function () {
        var printContent = $('#qr-print-section');
        if (printContent.length === 0) {
            console.error('Print section not found!');
            return;
        }
    
        var printWindow = window.open('', '', 'height=600,width=800');
        printWindow.document.write('<html><head><title>Print QR Code</title>');
        printWindow.document.write('<style>body{font-family:sans-serif;text-align:center;} img{max-width:100%;} </style>');
        printWindow.document.write('</head><body>');
        printWindow.document.write(printContent.clone().html());
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
        printWindow.close();
    });
    
});