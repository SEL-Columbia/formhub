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

(function(){
    var popupRequested = false;
    var popupDiv;
    var popupWidth;
    var descriptionWrap;
    function getDescriptionWrap() {
        if(descriptionWrap===undefined) {
            descriptionWrap = $('.description-wrap').eq(0);
            if(descriptionWrap.length===0) {
                descriptionWrap = $('<div />')
                        .addClass('description-wrap')
                        .appendTo($('#header'));
            }
        }
        return descriptionWrap;
    }
    $('a#hlogo').click(function(evt){
        getDescriptionWrap().toggleClass('showing');
        if(!popupRequested) {
            var popupReq = $.get('/description').then(function(d){
                popupDiv = $(d).find('#site-description');
                popupWidth = popupDiv.data('width');
                descriptionWrap
                    .addClass('filled')
                    .css({'width': popupWidth})
                    .html(popupDiv);
            });
            popupRequested = true;
        }
        evt.preventDefault();
    });
})();

var getMustacheTemplate = (function(){
    var mTemplates = {};
    return function getMustacheTemplateFromCacheOrAjax(templateName, cb) {
        if(!mTemplates[templateName]) {
            $.get("/mustache/"+templateName).done(function(d){
                mTemplates[templateName] = d;
                cb.call({
                    name: templateName,
                    template: d,
                    templates: mTemplates
                }, d);
            });
        } else {
            cb.call({
                name: templateName,
                template: mTemplates[templateName],
                templates: mTemplates
            });
        }
    }
})();

