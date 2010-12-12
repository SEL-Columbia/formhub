//Resize the map window...
$(function(){
    $(window).resize(function(){
        var mapBox = $('.map-tab'),
            offset, sh,
        	padding = 10;
        	
    	offset = mapBox.offset().top;
    	wh = $(window).height();
    	sh = wh - (offset + padding);
     	if(sh>100) {mapBox.css({'height':sh})}
    });
    $(function(){$(window).trigger('resize')})
})

//colors to match up marker flags
var markerImages = {
	water: 'blue',
	school: 'green',
	health: 'red'
};

/*-- 
- This structure works, for now.
--*/
var SubmissionList, SubmissionPoint;

(function($){
	function _SubmissionList(arr){
	    this.points = $(arr).map(function(){return new _SubmissionPoint(this)});
		this.length = this.points.length;
	}
	$.extend(_SubmissionList.prototype, {
		sortBy: function(q){
			return this.points.sort(function(a, b){
				return a[q] < b[q] ? -1 : a[q] > b[q] ? 1 : 0
			})
		},
		groupBy: function(q){
			var _k, _output = {};
			$(this.points).each(function(){
				_k = String(this[q]);
				if(typeof(_output[_k])=='undefined') {_output[_k]=[]}
				_output[_k].push(this);
			});
			return _output;
		},
		toString: function(){
			return "" + this.points.length + " submissions";
		},
		addToMap: function(map){
		    $(this.points).each(function(){
		        this.addToMap(map);
		    })
		},
		prepare: function(){
		    $(this.points).each(function(){this.prepareForGoogleMaps()})
            return this;
		}
	})

    function _SubmissionPoint(options){
        this.images=[];
        $.extend(this, options);
    }
    $.extend(_SubmissionPoint.prototype, {
        prepareForGoogleMaps: function(){
            if(this.gps) {
                this.gpoint = new google.maps.LatLng(this.gps.lat, this.gps.lng);
                this.gmarker = new google.maps.Marker({
                    position: this.gpoint,
                    icon: this.icon(),
                    title: this.title
                })
            }
        },
        icon: function(){
            return '/site-media/images/geosilk/flag_'+markerImages[this.survey_type]+'.png';
        },
        hasGps: function() {
            return "undefined"!==typeof this.gmarker
        },
        hasImage: function() {
            return this.images.length > 0
        },
        addToMap: function(map) {
            if(this.hasGps() && map._) {
                this.gmarker.setMap(map._)
                var _image = this.images[0],
                    _title = this.title;
                google.maps.event.addListener(this.gmarker, 'click', function(){
                    $.fancybox({
                        padding: 5,
                        href: _image,
                        title: _title,
                        transitionIn: 'elastic',
                        transitionOut: 'elastic'
                    })
                })
            }
        },
        popupImage: function(){
            console.log(this, arguments);
            if(this.hasImage()) {
                $.fancybox({
        			'padding'		: 5,
        			'href'			: this.images[0],
        			'title'   		: this.title,
        			'transitionIn'	: 'elastic',
        			'transitionOut'	: 'elastic'
        		});
            }
        }
    });
    
    
    window.SubmissionList = _SubmissionList;
    window.SubmissionPoint = _SubmissionPoint;
})(jQuery);

/*-
- jQuery plugin which instantiates a Gmap wrap for a google map on the
- first element.
-*/
(function($){
    function Gmap(elem, options) {
        if($(elem).data('gmap')) {
            return $(elem).data('gmap');
        }
        this.elem=elem;
        this._=false;
        this.opts=$.extend({
            mapType: 'terrain',
            center: [0,0],
            zoom: 6
        }, options);
    }
    $.extend(Gmap.prototype, {
        load: function(){
            if(this._) {
                return;
            }
            this._ = new google.maps.Map(this.elem, $.extend(this.opts, {
                mapTypeId: google.maps.MapTypeId[this.opts.mapType.toUpperCase()],
                center: new google.maps.LatLng(this.opts.center[0], this.opts.center[1])
            }))
        }
    });
    function $gmap(options) {
        var elem = this.get(0);
        if(elem) {
            var _gmap = new Gmap(elem, options);
            $(elem).data('gmap', _gmap);
            return _gmap;
        }
    }
    $.extend($.fn, {
        gmap: $gmap
    });
})(jQuery)
