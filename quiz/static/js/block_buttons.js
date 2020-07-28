document.addEventListener('contextmenu', function(e) {
  e.preventDefault();
});
document.onkeydown = function(e) {
  if(event.keyCode == 123) {
     return false;
  }
  if(e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0)) {
     return false;
  }
  if(e.ctrlKey && e.shiftKey && e.keyCode == 'C'.charCodeAt(0)) {
     return false;
  }
  if(e.ctrlKey && e.keyCode == 'C'.charCodeAt(0)) {
     return false;
  }
  if(e.ctrlKey && e.keyCode == 'S'.charCodeAt(0)) {
     return false;
  }
  if(e.ctrlKey && e.shiftKey && e.keyCode == 'J'.charCodeAt(0)) {
     return false;
  }
  if(e.ctrlKey && e.keyCode == 'U'.charCodeAt(0)) {
     return false;
  }
}

$('body').bind('cut copy paste', function (e) {
	$("#error").fadeIn("slow");
	setTimeout(function(){
		$("#error").fadeOut("slow");
	},2000);
	return false;
});

$(document).bind('contextmenu', function (e) {
	$("#error").fadeIn("slow");
	setTimeout(function(){
		$("#error").fadeOut("slow");
	},2000);
	return false;
});

