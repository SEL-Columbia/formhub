/*--
(function(surveyorDiv){
	//a tangent that doesn't really do what it needs to...
	var tbod = ['tbody', {}], group,
		ph, grouped = points.groupBy('phone');
	for(ph in grouped) {
		group=grouped[ph];
		var htd = ["td", {'rowspan':group.length}, ph];
		if(ph=="undefined") {
			continue;
		}
		for(var tt = 0; tt<group.length; tt++) {
			var qq = ['td', {}, String(group[tt].date)];
			var qtype = ['td', {}, String(group[tt].survey_type)]
			if(tt==0) {
				tbod.push(['tr', {}, htd, qtype, qq]);
			} else {
				tbod.push(['tr', {}, qtype, qq]);
			}
		}
	}
	surveyorDiv.buildIn(['table', {'class':'shade-alternate fullw align-top padded'}, tbod]);
})//($('#surveyors'))
--*/

var markerImages = {
	water: 'blue',
	school: 'green',
	health: 'red'
};

var ResizeMap;

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
 
/*-- 
- I don't like this structure. Will re-do soon.
--*/
var SubmissionList = (function($){
	function Slist(arr){
		this.points = arr;
		this.length = this.points.length;
	}
	$.extend(Slist.prototype, {
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
		prepare: function(){
		    this.gatherGpoints();
            this.gatherGmarkers();
            return this;
		},
		gatherGpoints: function(){
			$(this.points).each(function(){
				if(!this.gpoint) {
					if(this.gps) {
						this.gpoint = new google.maps.LatLng(this.gps.lat, this.gps.lng);
					}
				}
			})
		},
		gatherGmarkers: function() {
			for(var pi in this.points) {
				if(this.points[pi].gpoint){
					
					// Origins, anchor positions and coordinates of the marker
				  // increase in the X direction to the right and in
				  // the Y direction down.
				var mrk, st= this.points[pi].survey_type;
				if(typeof(st)=='undefined') {
					st='orange';
				}
				  var image = new google.maps.MarkerImage('/site-media/images/geosilk/flag_'+markerImages[st]+'.png',
				      // This marker is 20 pixels wide by 32 pixels tall.
				      new google.maps.Size(16,16),
				      // The origin for this image is 0,0.
				      new google.maps.Point(0,0),
				      // The anchor for this image is the base of the flagpole at 0,32.
				      new google.maps.Point(11,15));

					var gmarker = new google.maps.Marker({
						'position':this.points[pi].gpoint,
						'title': this.points[pi].title,
						'icon': image
					});
					gmarker.xpoint = this.points[pi];
					
					var contentString = "<div class='popup-image'><img src='"+this.points[pi].images[0]+"' /></div>";
					this.points[pi].infowindow = new google.maps.InfoWindow({
					    content: contentString
					});

					this.points[pi].gmarker = gmarker;
				}
			}
		}
	})
	return Slist;
})(jQuery);


(function($){
    function Gmap(elem, options) {this.elem=elem;this.opts=$.extend({
            mapType: 'terrain',
            center: [0,0],
            zoom: 6
        }, options);
    }
    $.extend(Gmap.prototype, {
        load: function(options){
            var options = {
                mapTypeId: google.maps.MapTypeId[this.opts.mapType.toUpperCase()],
                center: new google.maps.LatLng(this.opts.center[0], this.opts.center[1])
            }
            this._ = new google.maps.Map(this.elem, $.extend(this.opts, options))
        },
        addPoints: function(points){
            for(var xi in points) {
                var x = points[xi];
                if(x.gmarker) {
                    var mapp = this._;
                    x.gmarker.setMap(mapp)
                    google.maps.event.addListener(x.gmarker, 'click', function(){
                        if(this.xpoint.images.length > 0) {
                            $.fancybox({
                    			'padding'		: 10,
                    			'href'			: this.xpoint.images[0],
                    			'title'   		: this.title,
                    			'transitionIn'	: 'elastic',
                    			'transitionOut'	: 'elastic'
                    		});
                        }
                    })
                }
            }
        }
    })
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

/*--
var $map = (function(){
    function GoogleMap(){
        this.site="google.com";
    }
    $.extend(GoogleMap.prototype, {
        load: function(){
            
        }
    });
    return GoogleMap
})();

(function($){
    var googmap = google.maps,
        elem,
        Map;
    
    function AddPoint(ll, options) {
        if(!this.isAgmap) {return false;}
        if(!ll.lat || !ll.lng || !ll instanceof Array) {return false;}
        var latlng, marker;
        if(ll instanceof Array) { latlng = new googmap.LatLng(ll[0], ll[1]);
        } else { latlng = new googmap.LatLng(ll.lat, ll.lng);}
        
        var opts = $.extend({
            title: 'Mapped Point'
        }, options);
        marker = new googmap.Marker({position: latlng, title: opts.title});
        
        marker.setMap(Map);
        return marker;
    }
    function MapLayer($map) {this.$map=$map;$map.layers.push(this);this.points=[];}
    $.extend(MapLayer.prototype, {
        show: function() {
            
        },
        hide: function(){
    //        console.log('hides everything')
        },
        addPoint: function(pt, options){
    //        this.$map
        },
        removePoint: function(pt){
            console.log("removing point", pt);
        }
    })
    function CreateLayer(options) {
        var layer = new MapLayer(options);
    }
    function addLayer() {
    }
    function CreateMap(options){
//        this.$map = new $map.apply(this, arguments);
        this.isAgmap=true;
        this.layers = [];
        
        var opts = $.extend({
            center: [0,0],
            mapType: "terrain",
            zoom: 6
        }, options);
        
///        var center = new googmap.LatLng(opts.center[0], opts.center[1])
        elem = this.get(0);
        
  //      Map = new googmap.Map(elem, {
    //        center: center,
//            mapTypeId: google.maps.MapTypeId[opts.mapType.toUpperCase()],
  //          zoom: opts.zoom
    //    })
        return this
    }
    function GetMapObject() {return Map;}


    function CreateView(options) {
        this.layers.push('a')
        console.log(this.layers);
    }
    function ActivateView(options) {
        console.log(this.layers);
    }
    $.extend($.fn, {
//        gmap: CreateMap,
  //      addPoint: AddPoint,
 //       getMapObject: GetMapObject,
 //       createView: CreateView,
 //       activateView: ActivateView
    });
})(jQuery)
--*/
