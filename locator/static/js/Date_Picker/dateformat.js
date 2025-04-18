

$(document).ready(function(){
    var date = new Date();
    var today = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd'
    });
   $( '#datepicker3, #datepicker4').datepicker( 'setDate', today );
    $('#datepicker3, #datepicker4').datepicker('remove');
    
});