$("#mod_but").click(function(){
			console.log($(this).attr('href'))
			$("#item_update_form").attr("action",$(this).attr('href'));

		});

		$("#answers-form").submit(function (e) {
				// preventing from page reload and default actions
				e.preventDefault();
				// serialize the data for sending the form data.
				var serializedData = $(this).serialize();
				// make POST ajax call
				$.ajax({
						type: 'POST',
						url: "{% url 'teachers:add_answer' question_id %}",
						data: serializedData,
						success: function (response) {
								// on successfull creating object
								$("#answers-form").trigger('reset');
								$("#id_nick_name").focus();

								var instance = JSON.parse(response["instance"]);
								var fields = instance[0]["fields"];
								$("#my_answers tbody").prepend(
										`<tr>
										<td>${fields["name"]||""}</td>
										<td>${fields["points"]||""}</td>
										<td>${fields["correct"]||""}</td>
										<td class="text-right"><a class="btn btn-warning" disabled>Delete</a><td>
										</tr>`
								)
								location.reload();
						},
						error: function (response) {
								// alert the error if any error occured
								 alert("fail");
						}
				})
		})

function deleteAnswer(id) {
	var action = confirm("Are you sure you want to delete this answer?");
	if (action != false) {
		$.ajax({
				url: '{% url "teachers:delete_answer" %}',
				data: {
						'id': id,
				},
				dataType: 'json',
				success: function (data) {
						if (data.deleted) {
							$("#my_answers #answer-" + id).remove();
						}
				}
		});
	}
}
