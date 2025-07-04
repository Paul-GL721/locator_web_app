$(document).ready(function() {
    //allow multiple selections
    $('.multiselect').select2();

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

    //Get all psoitions belonging to that group
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

    /******* On group selection get the users assoiciated with it *******/
    $('#reportusergrp').on('change', function () {
        var groupId = $(this).val(); // Get selected property ID
        fetchAndPopulateUsers(groupId, 'reportusersingrp'); // Call reusable function
        // Enable the field if it's disabled
        //userField.prop('disabled', false)
    }); 

    /*
    * Fetch and populate user based on the selected group.
    * @param {string} groupId - The ID of the selected group.
    * @param {string} userId - The ID of the user select field to update.
    */
    function fetchAndPopulateUsers(groupId, userId) {
        const userField = $(`#${userId}`); 
        fullurl = $('#CreateTabularReport').attr('data-url');

        if (groupId && groupId.length > 0) {
            $.ajax({
                url: fullurl,
                data: {
                    groupId: groupId,
                },
                traditional: true,
                dataType: 'json',
                success: function (data) {
                    userField.empty(); // Clear current options
                    //userField.append('<option value="ALL">All Users</option>'); // Add placeholder
                    const selectData = data.user_list;

                    // Add options dynamically
                    selectData.forEach(function (usr) {
                        userField.append(
                            `<option value="${usr.userid}">${usr.usernames}</option>`
                        );
                    });
                    // Enable the field if it's disabled
                    userField.prop('disabled', false);
                },
                error: function () {
                    alert('Failed to fetch users. Please try again.');
                },
            });
        } else {
            // If no group selected, reset and disable the user field
            userField.empty();
            userField.append('<option value="ALL">ALL Users</option>');
            userField.prop('disabled', true);
        }
    }

    /* Post data when the user changes select or data inputs */
    function loadPositionTable() {
        const groupIds = $('#reportusergrp').val() || [];
        const userIds = $('#reportusersingrp').val() || [];
        const fromDate = $('#datepicker1').val();
        const toDate = $('#datepicker2').val();
    
        $.ajax({
            url: $('#CreateTabularReport').attr('action'),
            type: 'POST',
            data: {
                groupIds: groupIds,
                userIds: userIds,
                fromDate: fromDate,
                toDate: toDate,
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
            },
            traditional: true,
            success: function(response) {
                $('#ajaxtables').html(response.table_html);
                // Re-initialize the Bootstrap Table plugin
                $('#ajaxtables table').bootstrapTable();
                /*$('#report-title').html(
                    `User Position Tracking Report<br>
                    <span class="fw-normal">for ${response.groupname}</span><br>
                    <span class="fw-light">From ${response.start} to ${response.end}</span>`
                );*/
            },
            error: function() {
                alert('Failed to load table.');
            }
        });
    }
    
    // Attach change listeners
    $('#reportusergrp, #reportusersingrp, #datepicker1, #datepicker2').on('change', function () {
        loadPositionTable();
    });    
    
});