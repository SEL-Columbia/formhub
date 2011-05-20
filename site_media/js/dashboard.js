(function(listTable){
	listTable.find('tr.state-row').click(function(){
		if($(this).hasClass('selected')) {
			$(this).removeClass('selected')
				.parents('tbody').removeClass('opened');
			$(listTable).removeClass('active');
		} else {
			$('tbody.opened', listTable).removeClass('opened');
			$('.selected', listTable).removeClass('selected');
			$(this).addClass('selected')
				.parents('tbody').addClass('opened');
			$(listTable).addClass('active');
		}
	})
})($('#state-lga-list'))

	$('.button').button();
	
	function capitalizeString(str) {
	    return str.slice(0,1).toUpperCase() + str.slice(1);
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
			$(document.body).css({'overflow':'hidden'})
			$(window).trigger('resize')
		});
	});
	(function($){
		$.fn.thinButton = function(){
			this.button();
			$('span.ui-button-text', this).css({'padding':'1px 5px'});
			return this;
		}
	})(jQuery);


	SetResizer(jQuery, ".iiwrap", "#header, #menu", (16+24));

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
				return this.mapKey;
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
            defaultCenter: function(){
                this.map.setZoom(defaultMapCenter.zoom);
                this.map.setCenter(new google.maps.LatLng(defaultMapCenter.lat, defaultMapCenter.lng))
            },
            getMapElem: function(){return gmapElem}
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
					var l = new google.maps.KmlLayer("/site-media/kml/113_lgas.kml", {
						preserveViewport: true,
						suppressInfoWindows: true,
						map: gmap
					});
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
		//			addNga113Map(gmap);
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
})();

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
		prependButton: function(text, url){
			this.tr.prepend($("<td />").html($("<a />", {'href':url}).html(text).thinButton()));
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
		}
	}
})();

	var dashboard = (function($){
	    var dashboard = $.sammy("#main", function(){
	        this.use(Sammy.Storage);
			
	        this.use(Sammy.SwitchTo);
	        this.use(Sammy.GoogleMaps);
			this.setMapElem("#map-div");
	

	        this.use(Sammy.Title);
	        this.setTitle(function(title){
	            return ["Baseline Data Collection: ", title].join("");
	        });

	        this.use(Sammy.Template);
	    });
	    $(function(){
	        dashboard.run("#/");
	        dashboard.switchToDuration(200);
	    });
	    return dashboard;
	})(jQuery);
	dashboard.activateSwitchTo(".full-content.sliding");
	/*-- landing page
	--*/
	dashboard.get("#/", function(context){
        var dashbElem = this.switchTo("dashboard", {title: "Data"});
    });

	/*-- LGA/State List
	--*/
	
	//redirects to submission-counts
	dashboard.get("#/lga-list", function(){dashboard.setLocation("#/submission-counts");});
	
	dashboard.get("#/submission-counts", function(){
		var pageElem = this.switchTo("lga-list", {title: "LGA List"});
		$('.pretty-table-wrap', pageElem).fadeIn().css({'z-index':99});
		$("#map-wrap", pageElem).fadeOut();
	});
	
	dashboard.get("#/map/lga/:lga_id", function(){
		var lgaId = this.params.lga_id;
		var pageElem = this.switchTo("lga-list", {title: "LGA Map"});
		$('.pretty-table-wrap', pageElem).fadeOut();
		$("#map-wrap", pageElem).fadeIn();
		var that = this;
		
		var oneTime = 0;
		
		$.retrieveJSON("/xforms/map_data_points/"+lgaId+"/", function(data){
			if(!oneTime++) {
				var list = new ActivityList(data);
				var llWindow = list.latLngWindow();
				if(llWindow) {
					var neBounds = [llWindow.range.lat.max, llWindow.range.lng.max];
					var swBounds = [llWindow.range.lat.min, llWindow.range.lng.min];
					that.Map(function(){
						__map = this.map;
						var center = new google.maps.LatLng(llWindow.range.lat.avg,
											llWindow.range.lng.avg);
						var ne = new google.maps.LatLng(neBounds[0], neBounds[1]);
						var sw = new google.maps.LatLng(swBounds[0], swBounds[1]);
	                    var bounds = new google.maps.LatLngBounds(sw, ne);
						this.map.fitBounds(bounds);
						var map = this.map;
						var nav = this.key({clear:true});
						MapKey.empty();
						MapKey.appendMapTypeSelector();
						MapKey.prependButton("&laquo; Back to the List of LGAs", "#/submission-counts");
						list.each(function(){
							if(!this.gps) {
								return;
							}
							if(!this.pt) {
								var position = new google.maps.LatLng(this.gps.lat, this.gps.lng);
								this.pt = new google.maps.Marker({
									title: this.title,
									position: position,
									icon: this.icon()
								});
								this.pt.activityPoint = this;
								this.pt.setMap(map);
								var thatPt = this;
								google.maps.event.addListener(this.pt, 'click', function(){
									var oneTime = 0;
									var jsonUrl = "/xforms/survey/"+this.activityPoint.instanceId+"/";
									$.retrieveJSON(jsonUrl, function(data){
										if(!oneTime++) {
											InstancePopup(thatPt, data);
										}
									})
				        		});
							}
						})
					})
				}
			}
		});
	});
	
	var MapPopup = (function(){
		var showing = false;  //,		  wrapElem;
		return (function show(elem){
			if(showing) {
				$(showing).dialog('close');
				$(showing).remove();
			}
			$(elem).dialog({
				resizable: false,
				width: 600
			});
			showing = elem;
		});
	})();
	
	function InstancePopup(activityPoint, data) {
		var popupElem = $("<div />", {'style':'max-height:500px;overflow:auto'});
		if(activityPoint.imageUrl) {
			popupElem.append($("<div />", {'class': 'instance-image'}).html());
		}
		var topContext = $("<tbody />");
//		topContext.append($("<tr />", {'rowspan':4}).html())
		var link = $("<a />", {'href': activityPoint.imageUrl, target: '_blank', 'class': 'img-link'}).html($("<img />", {'src': activityPoint.imageUrl}));
		var tcWrap = $("<div />", {'class':'clearfix'}).append(link).append($("<table />", {'class':'popup-context'}).html(topContext));
		var ddList = $("<dl />", {'style':'clear:both'});
		$.each(data, function(i, qaPair){
			if(qaPair[0]=="imei") {
				var tr = $("<tr />");
				tr.append($("<td />").text("Device ID"))
					.append($("<td />").text(qaPair[1]))
				topContext.append(tr)
			} else if(qaPair[0]=="start_time") {
				var tr = $("<tr />");
				tr.append($("<td />").text("Start Time"))
					.append($("<td />").text(qaPair[1]))
				topContext.append(tr)
			} else if(qaPair[0]=="end_time") {
				var tr = $("<tr />");
				tr.append($("<td />").text("End Time"))
					.append($("<td />").text(qaPair[1]))
				topContext.append(tr)
			} else {
				ddList.append($("<dt />").text(qaPair[0]))
					.append($("<dd />").text(qaPair[1]));
			}
		});
		popupElem.append(tcWrap);
		popupElem.append(ddList);
		MapPopup($("<div />", {title: activityPoint.title}).html(popupElem))
	}
	
	var ActivityList, ActivityPoint;
	(function($){
		function _ActivityList(arr){
			if(arr){
				this.addPoints(arr)
			}
		}
		_ActivityList.prototype = new Array();
		$.extend(_ActivityList.prototype, {
			find: function(id){
				var i = 0, l=this.length;
				for(;i<l;i++) {
					if(id==this[i].id) {
						return this[i];
					}
				}
				return false;
			},
			each: function(cb){
				$(this).each(cb);
			},
			filter: function(k, v){
				var subList = new _ActivityList([]);
				if($.type(v)=='string') {
					v=v.toLowerCase();
				}
				$(this).each(function(){
					if($.type(this[k])==='string') {
						if(this[k].toLowerCase()===v) {
							subList.addPoint(this);
						}
					} else {
						if(this[k]===v) {
							subList.addPoint(this)
						}
					}
				});
				return subList;
			},
			addPoint: function(point){
				this.push(new _ActivityPoint(point))
			},
			addPoints: function(points){
				var _Sl = this;
				$(points).each(function(){_Sl.addPoint(this)});
			},
			latLngWindow: function(){
				var lats = [], lngs = [];
				$.each(this, function(){
					if(this.gps && this.gps.lat) {
						lats.push(this.gps.lat);
						lngs.push(this.gps.lng);
					}
				});
				if(lats.length == 0 || lngs.length==0) {
					return null;
				}
				var llRange = {
					lat: {
						min: Math.min.apply(this, lats),
						max: Math.max.apply(this, lats)
					},
					lng: {
						min: Math.min.apply(this, lngs),
						max: Math.max.apply(this, lngs)
					}
				}
				llRange.lat.avg = (llRange.lat.min + llRange.lat.max)/2
				llRange.lng.avg = (llRange.lng.min + llRange.lng.max)/2
				return {
					lat: llRange.lat.avg,
					lng: llRange.lng.avg,
					range: llRange
				}
			},
			getVarieties: function(){
				var survey_types = [], dates = [], surveyors = [];
				$(this).each(function(){
					if(survey_types.indexOf(this.survey_type)==-1) { survey_types.push(this.survey_type); }
					if(dates.indexOf(this.date)==-1) { dates.push(this.date); }
					if(surveyors.indexOf(this.surveyor)==-1) { surveyors.push(this.surveyor); }
				});
				return {
					surveyor: surveyors,
					date: dates,
					survey: survey_types
				}
			}
		})

	    var months = "Jan Feb Mar Apr May June July Aug Sept Oct Nov Dec".split(" ");
		function _ActivityPoint(o){
			if(o instanceof _ActivityPoint) {return o}
			this._contents = o;
			var ll = o['location/gps'].split(" ");
			this.gps = {lat: ll[0], lng: ll[1]};
			this.surveyType = o._name;
			this.surveyor = o._surveyor_name;
			this.instanceId = o._id;
			this.time = o.start_time;
			this.title = this.surveyType;
			this.imageUrl = o._attachments[0];
			if(this.imageUrl) {this.imageUrl = '/site-media/'+this.imageUrl;}
		}
		var flagColors = "blue green orange pink purple red yellow".split(" ");
		var stColors = {
			water: "blue",
			health: "red",
			agriculture: "orange",
			lga: "purple",
			education: "green",
			defaultColor: "purple"
		};
		
		_ActivityPoint.prototype.icon = function(){
			var color;
			if(this.surveyType==undefined) {
				color = 'purple'
			} else {
				color = stColors[this.surveyType.toLowerCase()]
			}
			var icon = new google.maps.MarkerImage("/site-media/images/geosilk/flag_"+color+".png", new google.maps.Size(16, 16),
		        new google.maps.Point(0,0), new google.maps.Point(9, 15));
		    
			return icon;
		}
		_ActivityPoint.prototype.shadow = function(){
			var icon = new google.maps.MarkerImage("/site-media/images/gmap-smaller-dots/"+color+".png", new google.maps.Size(13, 13),
		        new google.maps.Point(0,0), new google.maps.Point(6, 6));
		    
			return icon;
		}
		
		_ActivityPoint.prototype.district=function(){
			var result, district_id = this.district_id;
			if(this.district_id) {
				$(districts).each(function(){ if(this.id==district_id) {result = this} })
			}
			return result;
		}
		window.ActivityList = _ActivityList;
	})(jQuery);
