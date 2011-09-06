function mdgGoalText(gn){
    return ["Goal 1 &raquo; Eradicate extreme poverty and hunger",
    "Goal 2 &raquo; Achieve universal primary education",
    "Goal 3 &raquo; Promote gender equality and empower women",
    "Goal 4 &raquo; Reduce child mortality rates",
    "Goal 5 &raquo; Improve maternal health",
    "Goal 6 &raquo; Combat HIV/AIDS, malaria, and other diseases",
    "Goal 7 &raquo; Ensure environmental sustainability",
    "Goal 8 &raquo; Develop a global partnership for development"][gn-1];
}

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

var descriptionClick = (function(descriptionClickSelector){
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
    $(descriptionClickSelector).click(function(evt){
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
        return false;
    });
});

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

