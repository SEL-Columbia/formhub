var SetResizer = (function($, resizeSelector, excludeSelector, extraPadding){
	var resizeElem = $(resizeSelector),
		excludeElem = $(excludeSelector);

	function ResizePage(){
		var windowHeight = $(window).height(),
			totalHeight = windowHeight - extraPadding;

		excludeElem.each(function(){totalHeight -= $(this).height();});
		resizeElem.css({'height':totalHeight})
	}
	$(window).resize(ResizePage);

	$(function(){
		resizeElem.css({'overflow':'auto'});
		$(document.body).css({'overflow':'hidden'});
		$(window).trigger('resize');
	});
});

(function($){
	$.fn.thinButton = function(){
		this.button();
		$('span.ui-button-text', this).css({'padding':'1px 5px'});
		return this;
	}
})(jQuery);

function setTitle(t) {
    var dtext = $("<span />").html(t.clone()).text();
    $('#header .title').html(t);
    $('title').html(dtext);
}

function log() {
	if(console !== undefined && console.log !== undefined) {
		console.log.apply(console, arguments);
	}
}
function warn() {
	if(console !== undefined && console.warn !== undefined) {
	    console.warn.apply(console, arguments);
	    throw(arguments[0]);
	}
}