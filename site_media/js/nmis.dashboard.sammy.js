(function($) {
  Sammy = Sammy || {};
  Sammy.Title = function() {
    this.setTitle = function(title) {
      if (!$.isFunction(title)) {
        this.title_function = function(additional_title) {
          return [title, additional_title].join(' ');
        }
      } else {
        this.title_function = title;
      }
    };
    this.helper('title', function() {
      var new_title, 
            o_title = $.makeArray(arguments).join(' ');
      if (this.app.title_function) {
        new_title = this.app.title_function(new_title);
      }
      document.title = new_title;
      $('#page-title').text(o_title);
    });
  };
})(jQuery);

(function($){
    Sammy = Sammy || {};
    Sammy.SwitchTo = function() {
        var dests = [], parentElement, duration=0, destElems = {};
        this.switchToDuration = function(d){duration=d}
        this.activateSwitchTo = function(selector) {
            var parentElem = $(selector),
                idElements = [];
            
            parentElem.children().each(function(){
                if(!this.id) {
                    $(this).hide();
                } else {
                    dests.push(this.id);
                    destElems[this.id]=$(this);
                    idElements.push(this);
                }
            });
            var parentWidth = (100 * idElements.length);
            var childWidth =  (100 / idElements.length);
            
            parentElem.css({'width':parentWidth+"%"});
            $(dests).each(function(c){
                var _elem = destElems[this];
                _elem.css({'width':childWidth+"%",'float':'left'});
                _elem.data('switchToOffset', (-100 * c) + "%")
                _elem.bind('switchTo', function(evt){
                    var target = $(evt.target);
                    if(!target.hasClass('switchedTo')) {
                        $(".switchedTo", parentElem).removeClass('switchedTo');
                        target.addClass('switchedTo');
                        var _lOffset = target.data('switchToOffset');
                        parentElem.animate({'left':_lOffset}, duration, 'linear');
                    }
                })
            });
        }
        this.helper('switchTo', function(dest){
            if(dests.indexOf(dest)!==-1) {
                destElems[dest].trigger('switchTo');
                return destElems[dest];
            }
            return false;
        });
    }
})(jQuery);

var SammyMapLoaded;
(function(){
    Sammy.GoogleMaps = function(){
        var loadStarted = false,
            loadFinished = false,
            gmap = false,
            gmapElem = false;
        this.helper('ensureMapScriptLoaded', function(cb){
            if(!loadStarted) {
                $.getScript('http://maps.google.com/maps/api/js?sensor=false&callback=SammyMapLoaded');
                loadStarted = true;
            }
            if("function"==typeof cb) {
                cb.call(this);
            }
        });
        this.helper('ensureMap', function(elem, optsString, cb){
            //if the elem has not been set, then set it.
            //this is where the load function is binded to
            if(!gmapElem) {
                gmapElem = $(elem);
            }
            
            if(!loadFinished) {
                var sammyObj = this;
                gmapElem.bind('gmapLoaded', function(){
                    //make the map and call the callback with the first argument as the map object
                    eval("var opts="+optsString);
                    gmap = new google.maps.Map($(elem).get(0), opts);
                    cb.call(sammyObj, gmap);
                })
            } else {
                if(!gmap) {
                    eval("var opts="+optsString);
                    gmap = new google.maps.Map($(elem).get(0), opts);
                }
                cb.call(this, gmap);
            }
        });
        SammyMapLoaded = function(){
            loadFinished = true;
            if(gmapElem) {
                $(gmapElem).trigger('gmapLoaded');
            }
        }
    }
})()


var SetResizer = (function($, resizeSelector, excludeSelector, extraPadding){
	var resizeElem = $(resizeSelector),
		excludeElem = $(excludeSelector);
	
	function ResizePage(){
		var windowHeight = $(window).height(),
			totalHeight = windowHeight - extraPadding;
		
		excludeElem.each(function(){
			totalHeight -= $(this).height();
		});
		resizeElem.css({'height':totalHeight})
	}
	$(window).resize(ResizePage);
	$(function(){
		resizeElem.css({'overflow':'auto'});
		$(document.body).css({'overflow':'hidden'})
		$(window).trigger('resize')
	});
});

var urls = {
    dashboard: "#/",
    activity: '#/activity',
    freqTables: '#/frequency-tables',
    map: '#/map',
    mapBy: '#/map/by/(.*)'
}
var dashboard = (function($){
    $(function(){
        var menu = $('#menu .fwidth').empty();
        menu.append($('<li />').html($("<a />", {href:urls.activity}).html("Activity")))
        menu.append($('<li />').html($("<a />", {href:urls.freqTables}).html("Frequency Tables")))
        menu.append($('<li />').html($("<a />", {href:urls.map}).html("Map")))
    })
    
    var dashboard = $.sammy("#main", function(){
        this.use(Sammy.Storage);
        this.use(Sammy.SwitchTo);
        this.use(Sammy.GoogleMaps);
        this.store('mystore', {type: 'cookie'});
        this.use(Sammy.Title);
        this.setTitle(function(title){
            return ["Baseline Data Collection: ", title].join("");
        });
        this.get("#/", function(context){
            this.switchTo("dashboard");
            this.title("Dashboard");
        })
    });
    $(function(){
        dashboard.run("#/");
        dashboard.switchToDuration(200);
    });
    return dashboard;
})(jQuery)
