function capitalizeString(str) {
    return str.slice(0,1).toUpperCase() + str.slice(1);
}
function Mappable(){}
Mappable.prototype.showMapPoint = function() {
	if(!this.mapPoint) {
		var ll = new google.maps.LatLng(this.gps.lat, this.gps.lng)
		this.mapPoint = new google.maps.Marker({
			title: this.title,
			position: ll,
			map: _map,
			icon: this.icon(),
			shadow: this.shadow()
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
Mappable.prototype.flagColor = 'green';
var flagColors = "blue green orange pink purple red yellow".split(" ");
Mappable.prototype.shadow = function(){
    var shadow = new google.maps.MarkerImage("/site-media/images/gmap-icons/shadow-s.png", new google.maps.Size(25, 25),
        new google.maps.Point(0,0), new google.maps.Point(11,22));
    return shadow;
};
Mappable.prototype.icon = function(){
    var color = "grey";
    switch(this.survey_type) {
        case 'water':
        color = "blue";
        break;
        case 'education':
        color = 'green';
        break;
        case 'health':
        color = 'red';
        break;
    }
    var icon = new google.maps.MarkerImage("/site-media/images/gmap-icons/"+color+"-pointer-s.png", new google.maps.Size(25, 25),
        new google.maps.Point(0,0), new google.maps.Point(11,22));
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

(function($) {

  // Simple JavaScript Templating
  // John Resig - http://ejohn.org/ - MIT Licensed
  // adapted from: http://ejohn.org/blog/javascript-micro-templating/
  // originally $.srender by Greg Borenstein http://ideasfordozens.com in Feb 2009
  // modified for Sammy by Aaron Quint for caching templates by name
  var srender_cache = {};
  var srender = function(name, template, data) {
    // target is an optional element; if provided, the result will be inserted into it
    // otherwise the result will simply be returned to the caller
    if (srender_cache[name]) {
      fn = srender_cache[name];
    } else {
      if (typeof template == 'undefined') {
        // was a cache check, return false
        return false;
      }
      // Generate a reusable function that will serve as a template
      // generator (and which will be cached).
      fn = srender_cache[name] = new Function("obj",
      "var ___$$$___=[],print=function(){___$$$___.push.apply(___$$$___,arguments);};" +

      // Introduce the data as local variables using with(){}
      "with(obj){___$$$___.push(\"" +

      // Convert the template into pure JavaScript
      String(template)
        .replace(/[\r\t\n]/g, " ")
        .replace(/\"/g, '\\"')
        .split("<%").join("\t")
        .replace(/((^|%>)[^\t]*)/g, "$1\r")
        .replace(/\t=(.*?)%>/g, "\",h($1),\"")
        .replace(/\t!(.*?)%>/g, "\",$1,\"")
        .split("\t").join("\");")
        .split("%>").join("___$$$___.push(\"")
        .split("\r").join("")
        + "\");}return ___$$$___.join('');");
    }

    if (typeof data != 'undefined') {
      return fn(data);
    } else {
      return fn;
    }
  };

  Sammy = Sammy || {};

  // <tt>Sammy.Template</tt> is a simple plugin that provides a way to create
  // and render client side templates. The rendering code is based on John Resig's
  // quick templates and Greg Borenstien's srender plugin.
  // This is also a great template/boilerplate for Sammy plugins.
  //
  // Templates use <% %> tags to denote embedded javascript.
  //
  // ### Examples
  //
  // Here is an example template (user.template):
  //
  //      <div class="user">
  //        <div class="user-name"><%= user.name %></div>
  //        <% if (user.photo_url) { %>
  //          <div class="photo"><img src="<%= user.photo_url %>" /></div>
  //        <% } %>
  //      </div>
  //
  // Given that is a publicly accesible file, you would render it like:
  //
  //       $.sammy(function() {
  //         // include the plugin
  //         this.use(Sammy.Template);
  //
  //         this.get('#/', function() {
  //           // the template is rendered in the current context.
  //           this.user = {name: 'Aaron Quint'};
  //           // partial calls template() because of the file extension
  //           this.partial('user.template');
  //         })
  //       });
  //
  // You can also pass a second argument to use() that will alias the template
  // method and therefore allow you to use a different extension for template files
  // in <tt>partial()</tt>
  //
  //      // alias to 'tpl'
  //      this.use(Sammy.Template, 'tpl');
  //
  //      // now .tpl files will be run through srender
  //      this.get('#/', function() {
  //        this.partial('myfile.tpl');
  //      });
  //
  Sammy.Template = function(app, method_alias) {

    // *Helper:* Uses simple templating to parse ERB like templates.
    //
    // ### Arguments
    //
    // * `template` A String template. '<% %>' tags are evaluated as Javascript and replaced with the elements in data.
    // * `data` An Object containing the replacement values for the template.
    //   data is extended with the <tt>EventContext</tt> allowing you to call its methods within the template.
    // * `name` An optional String name to cache the template.
    //
    var template = function(template, data, name) {
      // use name for caching
      if (typeof name == 'undefined') name = template;
      return srender(name, template, $.extend({}, this, data));
    };

    // set the default method name/extension
    if (!method_alias) method_alias = 'template';
    // create the helper at the method alias
    app.helper(method_alias, template);

  };

})(jQuery);

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
                _elem.css({'width':childWidth+"%",'float':'left','position':'relative'});
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
        this.helper('switchTo', function(dest, opts){
            if(opts && opts.title) {
                this.title(opts.title);
            }
            if(dests.indexOf(dest)!==-1) {
                destElems[dest].trigger('switchTo');
                return destElems[dest];
            }
            return false;
        });
    }
})(jQuery);



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
            test: function(){
                console.log("Hello", this);
            },
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
                console.log(this.map, "clearing points");
            },
            getMapElem: function(){return gmapElem},
            addPoints: function(pts){
                console.log(pts, "added");
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
        menu.append($('<li />').html($("<a />", {href:"#/activity"}).html("Activity")))
        menu.append($('<li />').html($("<a />", {href:"#/frequency-tables"}).html("Frequency Tables")))
        menu.append($('<li />').html($("<a />", {href:"#/map"}).html("Map")))
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
            var dashbElem = this.switchTo("dashboard");
            this.title("Dashboard");
            $.get("/survey-list", function(htResponse){
                var surveyList = $(htResponse);
                $('a', surveyList).button();
                $('.iiwrap', dashbElem).html(surveyList);
            })
        })
    });
    $(function(){
        dashboard.run("#/");
        dashboard.switchToDuration(200);
    });
    return dashboard;
})(jQuery);
