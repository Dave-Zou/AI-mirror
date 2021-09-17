
is_display=0;
function jswrite_iframe(){
	is_display++;
	if(is_display%2 == 1){
		Iframe = '<div style="height: calc(100vh);"><div class="p2-body-center-iframe"><iframe src="surface_wave.html" frameborder="1" scrolling="no"></iframe></div><button class="js-button" onclick="jswrite_iframe()"style="color:black">Close Surface</button></div>';
		document.getElementById("js-p2-iframe").innerHTML = Iframe;
		document.getElementById("button-math").innerHTML = "Close Surface";
		document.getElementById("to-mao-m2").click();
	}
	else{
		document.getElementById("js-p2-iframe").innerHTML = '';
		document.getElementById("button-math").innerHTML = "Open Surface";
		document.getElementById("to-mao-m3").click();
	}
}
is_display_2 = 0;
function jswrite_iframe_2(){
	is_display_2++;
	if(is_display_2%2 == 1){
		Iframe2 = '<div style="height: calc(100vh);"><div class="p2-body-center-iframe"><iframe src="bar3d_punch_card.html" frameborder="1" scrolling="no"></iframe></div><button class="js-button" onclick="jswrite_iframe_2()"style="color:black">Close Statistics</button></div>';
		document.getElementById("js-p2-iframe-2").innerHTML = Iframe2;
		document.getElementById("button-English").innerHTML = "Close Statistics";
		document.getElementById("to-mao-m4").click();
	}
	else{
		document.getElementById("js-p2-iframe-2").innerHTML = '';
		document.getElementById("button-English").innerHTML = "Look At Me";
		document.getElementById("to-mao-m3").click();
	}
}