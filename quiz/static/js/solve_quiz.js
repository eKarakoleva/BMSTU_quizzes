function localAnswerSave(quiz_id){
		var lsname = "quiz"+quiz_id
	window.onbeforeunload = function() {
		console.log('SAVED')
		//localStorage.removeItem("StudentAnswers");
		student_answers =  $( "form" ).serializeArray();
		if (!submitted){
			localStorage.setItem(lsname, JSON.stringify(student_answers));
		}else{
			window.localStorage.removeItem(lsname);
		}
		
	}
	if (localStorage[lsname]) {
		var answers = JSON.parse(localStorage[lsname]);
		var i;
		for (i = 1; i < answers.length; i++) {
			let isnum = /^\d+$/.test(answers[i].value)
			if (isnum){
				$( "input[value='"+answers[i].value+"']" ).prop( "checked", true );
			}
			else {
				$( "textarea[name='"+answers[i].name+"']" ).val(answers[i].value);
			}
		}
	}
}

function startTimer(duration, display) {
	var timer = duration, minutes, seconds, hours;
	var x = setInterval(function () {
		hours = (timer / 3600) | 0;
		minutes = ((timer % 3600) / 60) | 0;
		seconds = (timer % 60) | 0;
			
		hours = hours < 10 ? "0" + hours : hours;
		minutes = minutes < 10 ? "0" + minutes : minutes;
		seconds = seconds < 10 ? "0" + seconds : seconds;

		display.textContent = hours + ":" + minutes + ":" + seconds;

		if (--timer < 0) {
			clearInterval(x);
			document.getElementById("timer").innerHTML = "Time is over!";
			$("form").find('input[type="submit"]').attr('disabled','disabled');
			user_data =  $( "form" ).serializeArray();
			submitted = 1
			ajax_send(user_data)
		}
	}, 1000);
}