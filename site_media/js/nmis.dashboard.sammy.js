function capitalizeString(str) {
    return str.slice(0,1).toUpperCase() + str.slice(1);
}
function Mappable(){}
Mappable.prototype.showMapPoint = function() {
    if(this.gps && this.gps.lat) {
    	if(!this.mapPoint) {
    		var ll = new google.maps.LatLng(this.gps.lat, this.gps.lng)
    		this.mapPoint = new google.maps.Marker({
    			title: this.title,
    			position: ll,
    			map: _map,
    			icon: this.icon()
    		});
    		if(this.mapPointListener) {
    		    var _pt = this;
        		google.maps.event.addListener(this.mapPoint, 'click', function(){
        		    _pt.mapPointListener();
        		});
    		}
    	}
    	this.mapPoint.setVisible(true)
    }
}
Mappable.prototype.flagColor = 'green';
var flagColors = "blue green orange pink purple red yellow".split(" ");
Mappable.prototype.shadow = function(){};
Mappable.prototype.icon = function(){
    var color = "grey";
    switch(this.survey_type.toLowerCase()) {
        case 'water':
        color = "blue";
        break;
        case 'education':
        case 'school':
        color = 'green';
        break;
        case 'health':
        color = 'red';
        break;
    }
    var icon = new google.maps.MarkerImage("/site-media/images/gmap-dots/"+color+".png", new google.maps.Size(25, 25),
        new google.maps.Point(0,0), new google.maps.Point(12,12));
    return icon;
//	return "http://thydzik.com/thydzikGoogleMap/markerlink.php?text="+this.iconText+"&color="+this.iconColor;
}
Mappable.prototype.setFlagColor = function(color) {
    if(this.flagColor==color) {
        return;
    }
    if(flagColors.indexOf(color)!==-1) {
        this.flagColor = color;
    } else {
        this.flagColor = "yellow"
    }
    this.updateIcon();
}
Mappable.prototype.updateIcon = function(){
    if(this.mapPoint) {
        this.mapPoint.setIcon(this.icon())
    }
}
Mappable.prototype.iconText = "1";
Mappable.prototype.iconColor = "ff0000";
Mappable.prototype.hideMapPoint = function(){
    if(this.mapPoint) {
    	this.mapPoint.setVisible(false)
    }
}


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


var MapKey = (function(){
	var mapKeyElem,
	    mapKeySelectors,
	    mapTypeSelectors,
		mapPar;
	return {
		create: function(){
		    var odiv = $.json2dom([
		            "div", {'class':'map-key-ww'}, [
		                "div", {'class': 'map-key-w'}, [
		                    "div", {'class': 'ui-dialog-titlebar ui-widget-header ui-corner-all ui-helper-clearfix', 'id': 'm-key'},
		                        ["table", {}, ["tbody", {}]]
		                ]
		            ]
		        ]);
		    
		    this.tr = $("<tr />");
		    this.tr.append($("<td />", {'class':'empty-spacer'}).html("<div />"));

		    mapKeySelectors=$('<td />', {'class':'selectors'});
	        this.tr.append(mapKeySelectors);
	        
	        this.appendMapTypeSelector();
            
		    $("tbody", odiv).append(this.tr);
			return odiv;
		},
		appendMapTypeSelector: function(){
		    mapTypeSelectors = $("<td />", {'id':'map-type-choices'})
		    var terrainButton = $("<a href='#'>Terrain</a>");
            terrainButton.click(function(evt){
                _map.setMapTypeId(google.maps.MapTypeId.TERRAIN);
                evt.preventDefault();
            });
            var satelliteButton = $("<a href='#'>Satellite</a>");
            satelliteButton.click(function(evt){
                _map.setMapTypeId("satellite")
                evt.preventDefault();
            });
            var mapButton = $("<a href='#'>Map</a>");
            mapButton.click(function(evt){
                _map.setMapTypeId('roadmap')
                evt.preventDefault();
            });
            var tDiv = $("<div />").css({'float':'right'});
            tDiv.append(terrainButton).append(satelliteButton).append(mapButton);
            mapTypeSelectors.append(tDiv);
            $('a', mapTypeSelectors).button().find('span.ui-button-text').css({'padding':'1px 5px'});
            this.tr.append(mapTypeSelectors);
		},
		selectors: function(){
		    return mapKeySelectors;
		},
		empty: function(){
		    this.tr.empty();
		},
		insert: function(cb){
		    var td = $("<td />").html(cb);
		    this.tr.append(td);
		},
		addDivider: function(){
			this.tr.append($("<td />").html($("<div />", {'class':'table-spacer'})));
		},
		addDistrictDropdown: function(){
			this.districtSelector = $("<select />");
			var nigeria = $("<option />", {value:'all'}).html("Republic of Nigeria");
			var allOpt = $("<optgroup />", {label:'Full view'}).html(nigeria)

			var districtView = $("<optgroup />", {label: 'District view'})
			this.districtSelector.append(allOpt);
			$(districts).each(function(){
				var opt = $("<option />", {value: this.id}).html(this.name);
				districtView.append(opt);
			});
			this.districtSelector.append(districtView);
			this.tr.append($("<td />").html(this.districtSelector));
			return this.districtSelector;
		},
		addChoiceDropdown: function(){
			this.addDivider();
			this.choiceSelector = $("<select />");
			this.choiceSelector.append($("<option>Date</option>"));
			this.choiceSelector.append($("<option>Surveyor</option>"));
			this.choiceSelector.append($("<option>Survey</option>"));
			this.iDiv.find('tr').append($('<td />').html(this.choiceSelector))
			return this.choiceSelector;
		},
		addSpecificityDropdown: function(choices){
			this.addDivider();
			var opt, selector = $("<select />");
			$(choices).each(function(){
				opt = $("<option />").html(this);
				selector.append(opt);
			});
			this.tr.append($("<td />").html(selector))
		},
		showSelection: function(pType) {
//				console.log("make selection for ", pType);
		}
	}
})();

var SammyMapLoaded,
    _map;
    
var zz;

(function(){
    Sammy.GoogleMaps = function(){
        var loadStarted = false,
            loadFinished = false,
            gmap = false,
            map,
            mapKey = false,
            gmapElem = false;
        this.setMapElem = function(elem){
            gmapElem = $(elem);
        }
        function mapObj() {
            this.sammyMap=true;
        }
        $.extend(mapObj.prototype, {
            // test: function(){
            //     console.log("Hello", this);
            // },
            mapCenter: function(center, opts){
                var zoom = opts.zoom;
                if(opts.bounds) {
                    var ne = new google.maps.LatLng(opts.bounds.lat.min, opts.bounds.lng.min);
                    var sw = new google.maps.LatLng(opts.bounds.lat.max, opts.bounds.lng.max);
                    var bounds = new google.maps.LatLngBounds(sw, ne);
                }
                this.map.setCenter(center);
                if(zoom) {
                    this.map.setZoom(zoom)
                }
            },
            ensureDistrictKmls: function(){
                var _map = this.map;
                $(districts).each(function(){
                    this.ensureKmlLoaded(_map);
                })
            },
            display: function(list, opts){
                if(!opts){var opts={}}
                if(opts.hideList) {
                    $(opts.hideList).each(function(){
                        if(list.indexOf(this)==-1) {
                            this.hideMapPoint();
                        } else {
                            this.showMapPoint();
                        }
                    })
                } else {
                    $(arr).each(function(){
                        this.showMapPoint();
                    });
                }
                if(opts.boundWindow) {
                    var curWindow = list.latLngWindow();
					if(curWindow) {
						this.setMapCenter(curWindow.lat, curWindow.lng, curWindow)
					}
                }
            },
            key: function(opts){
                if(!this.mapKey) {
                    this.mapKey = MapKey.create()
                    gmapElem.parent().append(this.mapKey)
                }
                if(opts && opts.clear) {
                    MapKey.selectors().empty();
                }
            },
            addSelector: function(opts, fn){
                var choices = opts.list || [],
                    text = opts.text,
                    selector = $("<select />");
                
                $(choices).each(function(){
                    if(this.name) {
                        var opt = $("<option />", {value: this.id}).html(capitalizeString(this.name))
                    } else {
                        var opt = $("<option />", {value: String(this)}).html(capitalizeString(String(this)));
                    }
                    selector.append(opt);
                });

                var selectorDiv = $("<div />", {'class':'selector-wrap'}).html(text);
                selectorDiv.append(selector);
                MapKey.selectors().append(selectorDiv);
                fn.call(this, selector);
            },
            divider: function(){
                MapKey.addDivider();
            },
            debug: function(mapState){
                str = "";
                str += "scale: " + mapState.scale
                if(mapState.district) {
                    str += " &mdash ";
                    str += "district: " + mapState.district
                }
                if(mapState.filter) {
                    str += " &mdash ";
                    str += "filter: " + mapState.filter
                }
                if(mapState.xyz) {
                    str += " &mdash ";
                    str += "x: "+ mapState.xyz
                }
                if(mapState.points) {
                    str += " &mdash ";
                    str += "point count: "+ mapState.points.length
                }
//                MapKey.insert(str);
            },
            setMapCenter: function(lat, lng, opts){
                var opts = opts || {};
                var zoom = opts.zoom;
                this.map.setCenter(new google.maps.LatLng(lat, lng))
                if(opts.range) {
                    var ne = new google.maps.LatLng(opts.range.lat.min, opts.range.lng.max);
                    var sw = new google.maps.LatLng(opts.range.lat.max, opts.range.lng.min);
                    var bounds = new google.maps.LatLngBounds(sw, ne);
                    this.map.fitBounds(bounds);
                }
            },
            nigeriaCenter: function(){
                this.map.setZoom(6);
                this.map.setCenter(new google.maps.LatLng(9.243092645104804, 7.9156494140625))
            },
            clearPoints: function(){
                // console.log(this.map, "clearing points");
            },
            getMapElem: function(){return gmapElem},
            addPoints: function(pts){
                // console.log(pts, "added");
            }
        });
        map = new mapObj();
        
        this.helper('SetMapElem', function(elem){gmapElem = $(elem)});
        var mapLoadCallbacks = [];
        this.helper('addMapLoadCallback', function(cb){mapLoadCallbacks.push(cb);})
        this.helper('Map', function(cb){
            mapLoadCallbacks.push(cb);
            if(!loadFinished) {
                var sammyObj = this;
                gmapElem.bind('gmapLoaded', function(){
                    //make the map and call the callback with the first argument as the map object
                    gmap = new google.maps.Map(gmapElem.get(0), {zoom:6,center:new google.maps.LatLng(9.243092645104804, 7.9156494140625), mapTypeId:'terrain', mapTypeControl: false});
                    _map = gmap;
                    map.map = gmap;
//                    cb.call(map);
                    $(mapLoadCallbacks).each(function(){
                        this.call(map);
                    })
                });
            } else {
                if(!gmap) {
                    gmap = new google.maps.Map(gmapElem.get(0), {zoom:6,center:new google.maps.LatLng(9.243092645104804, 7.9156494140625), mapTypeId:'terrain', mapTypeControl: false });
                    map.map = gmap;
                    _map = gmap;
                }
                // cb.call(map);
                $(mapLoadCallbacks).each(function(){
                    this.call(map);
                })
            }
            if(!loadStarted) {
                $.getScript('http://maps.google.com/maps/api/js?sensor=false&callback=SammyMapLoaded');
                loadStarted = true;
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

var dashboard = (function($){
    $(function(){
        var menu = $('#menu .fwidth').empty();
        menu.append($('<li />', {'class':'dashboard'}).html($("<a />", {href:"#/"}).html("Data Export"))); //why is this not loading in the page?
        menu.append($('<li />', {'class':'activity'}).html($("<a />", {href:"#/activity"}).html("Recent Surveys")))
        menu.append($('<li />', {'class':'frequency-tables'}).html($("<a />", {href:"#/frequency-tables"}).html("Frequency Tables")))
        menu.append($('<li />', {'class':'map'}).html($("<a />", {href:"#/map"}).html("Map")))
    })
    
    var dashboard = $.sammy("#main", function(){
        this.use(Sammy.Storage);
        this.store('mystore', {type: 'cookie'});
        
        this.use(Sammy.SwitchTo);
        this.use(Sammy.GoogleMaps);
        
        this.use(Sammy.Title);
        this.setTitle(function(title){
            return ["Baseline Data Collection: ", title].join("");
        });
        
        this.use(Sammy.Template);
        
        this.get("#/", function(context){
            var dashbElem = this.switchTo("dashboard", {title: "Data"});
            $.get(baseUrl + "survey-list", function(htResponse){
                var surveyList = $(htResponse);
                $('a', surveyList).button();
                $('tr td:nth-child(2)', surveyList).css({'text-align':'center'})
                $('.iiwrap', dashbElem).html(surveyList);
            });
        });
    });
    $(function(){
        dashboard.run("#/");
        dashboard.switchToDuration(200);
    });
    return dashboard;
})(jQuery);
