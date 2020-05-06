    /*
        On submiting the form, send the POST ajax
        request to server and after successfull submission
        display the object.
    */
    $("#answers-form").submit(function (e) {
        // preventing from page reload and default actions
        e.preventDefault();
        // serialize the data for sending the form data.
        var serializedData = $(this).serialize();
        // make POST ajax call
        $.ajax({
            type: 'POST',
            url: "{% url 'add_answer' %}",
            data: serializedData,
            success: function (response) {
                // on successfull creating object
                // 1. clear the form.
                $("#answers-form").trigger('reset');
                // 2. focus to nickname input 
                $("#id_name").focus();

                // display the newly friend to table.
                var instance = JSON.parse(response["instance"]);
                var fields = instance[0]["fields"];
                $("#my_friends tbody").prepend(
                    `<tr>
                    <td>${fields["name"]||""}</td>
                    <td>${fields["points"]||""}</td>
                    <td>${fields["correct"]||""}</td>
                    </tr>`
                )
            },
            error: function (response) {
                // alert the error if any error occured
                alert(response["responseJSON"]["error"]);
            }
        })
    })