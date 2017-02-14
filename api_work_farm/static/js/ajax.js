function start_task(tid) {
    $.ajax({
        url: "/start_task/",
        dataType: "json",
        type: "POST",
        data: {'api_id': $('#id_api_id')[0].value, 'json': $('textarea')[0].value},
        success: function(result) {
            if ('form_errors' in result) {
                $('#ajax_result').html("<b>ERRORS</b>: " + result['form_errors'].toString());
            } else {
                res = "You added tasks:<br>"
                for (var i=0; i<result['task_ids'].length; i++) {
                    task = result['task_ids'][i];
                    res += "<b>" + task['id'] + "</b>: " + task['state'] + "<br/>";
                }
                $('#ajax_result').html(res);
            }
            return true;
        }
        
    });
}

function current_tasks(tid) {
    $.ajax({
        url: "/my_tasks/",
        dataType: "json",
        type: "GET",
        data: {'api_id': $('#id_api_id')[0].value},
        success: function(result) {
            if (result.length>0) {
                current = "<table><tr><td>ID</td><td>status</td><td>estimate</td><td>result</td></tr>";
                for (var i=0; i<result.length; i++) {
                    task = result[i];
                    current += "<tr><td><b>" + task['fields']['unique_id'] + "</b></td><td>" + task['fields']['status'] + 
                               "</td><td>" + task['fields']['estimate'] + "</td><td>" + task['fields']['result'] + "</td></tr>";
                 }
                current += "</table>";
                $('#current_tasks').html(current);

            } else {
                $('#current_tasks').html("No tasks now");
            }
            return true;
        }
        
    });
}

$( function() { 
    $('#button_send_tasks').on('click', function() {
        start_task();
    });

    current_tasks();

    window.setInterval(function(){
        current_tasks();
    }, 3000);

})
