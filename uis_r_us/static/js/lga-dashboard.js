//right div popup (is functionally separate from the rest of the application logic)

(function($){
	var overMapContent;
	var rightDiv, rdNav;
	var mapContent;
	$.fn._showSideDiv = function(opts){
	    if(opts===undefined) { opts={}; }
		if(mapContent===undefined) { mapContent = $('.content-inner-wrap'); }
		if(rightDiv===undefined) {
			var rdWrap = $("<div />", {'class':'rd-wrap'}).appendTo(mapContent);
			rightDiv = $("<div />", {'class': 'right-div'}).appendTo(rdWrap);
            rdNav = $("<p />", {
                'html': $("<span />", {'class':'facility-title'})
            }).append($("<a />", {'href': '#', 'class': 'close', 'text':'[X]'}))
                .appendTo(rightDiv);
            rightDiv.delegate('a.close', 'click', function(){
                rightDiv.trigger('click-close');
                return false;
            });
			}
		rightDiv.unbind('click-close');
		rightDiv.bind('click-close', function(){
		    rightDiv.hide();
		    opts.close !== undefined && opts.close.apply(this, arguments);
		});
		opts.title !== undefined && rdNav.find('.facility-title').text(opts.title);
		rightDiv.html(rdNav)
		   .append(this.eq(0))
		   .show();
	}
})(jQuery);

// openlayers specific actions for icons
var olStyling = (function(){
    var iconMakers;
    var iconMode;
    var markerLayer;
	
    return {
        addIcon: function(facility, mode, opts){
            if(facility.iconModes === undefined) { facility.iconModes = {}; }
            facility.iconModes[mode] = {
                'url': opts.url,
                'size': opts.size
            };
        },
        setMarkerLayer: function(ml){
            markerLayer = ml;
        },
        setMode: function(facilityData, mode){
            $.each(facilityData.list, function(k, fac){
                if(fac.iconModes && fac.iconModes[mode] !== undefined) {
                    var iconModeData = fac.iconModes[mode];
                    if(iconModeData.size instanceof OpenLayers.Size) {
                        var size = iconModeData.size;
                    } else {
                        var size = new OpenLayers.Size(iconModeData.size[0], iconModeData.size[1]);
                    }
                    var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
                    var url = iconModeData.url;
                    if(fac.mrkr === undefined) {
                        var icon = new OpenLayers.Icon(url, size, offset);
                        fac.mrkr = new OpenLayers.Marker(fac.openLayersLatLng, icon);
                        markerLayer.addMarker(fac.mrkr);
                    } else {
                        fac.mrkr.icon.setSize(size);
                        fac.mrkr.icon.setUrl(iconModeData.url);
                    }
                }
            });
        },
        markIcon: function(pt, status){
            var mrkr = pt.mrkr;
            if(mrkr === undefined) { return; }
            if(status==='hidden') {
                $(mrkr.icon.imageDiv).hide();
            } else if(status==='showing') {
                $(mrkr.icon.imageDiv).show();
            }
        },
        changeIcon: function(facility, data){
            if(data===undefined) {return;}
            if(facility.mrkr !== undefined) {
                var iconSize = new OpenLayers.Size(16,16);
                var url = data.url;
                facility.mrkr.icon.setSize(iconSize);
                facility.mrkr.icon.setUrl(url);
            }
        }
    }
})();


//wrapping everything in the "lga" object, to stay out of the global scope.
var lga = (function(){

var selectedSubSector,
    selectedSector,
    selectedFacility,
    selectedColumn,
    facilitySectorSlugs,
    facilityData,
    facilitySectors;

var facilityTabsSelector = "div#facility-tabs";

var specialClasses = {
    showTd: 'show-me',
    tableHideTd: 'hide-tds'
};
var urls = {
    variables: '/facility_variables',
    lgaSpecific: '/facilities/site/'
};

var subSectorDelimiter = "-";

(function($){
    //a quick ajax cache, just trying to prevent multiple
    // requests to the same url in one pageload... (for now)
    var cacheData = {};
    $.getCacheJSON = function(){
        var url = arguments[0];
        if(url in cacheData) {
            return cacheData[url];
        } else {
            var q = $.getJSON.apply($, arguments);
            q.done(function(){
                cacheData[url] = q;
            });
            return q;
        }
    }
})(jQuery);

// Load data functions (creating ajax requests and triggering callbacks)
function loadLgaData(lgaUniqueId, onLoadCallback) {
    var siteDataUrl = urls.lgaSpecific + lgaUniqueId;
    var variablesUrl = urls.variables;
	var fv1 = $.getCacheJSON(siteDataUrl);
	var fvDefs = $.getCacheJSON(variablesUrl);
	$.when(fv1, fvDefs).then(function(lgaQ, varQ){
	    var lgaData = lgaQ[0];
		var stateName = lgaData.stateName;
		var lgaName = lgaData.lgaName;
		var facilityData = lgaData.facilities;
		var varDataReq = varQ[0];
		var variableDefs = varDataReq.sectors;
		var facilityDataARr = [];
		$.each(facilityData, function(k, v){
			v.uid = k;
			facilityDataARr.push(v);
		});
		facilityDataStuff(lgaQ, {sectors: variableDefs, data: facilityDataARr});
		if(facilityData!==undefined && facilitySectors!==undefined) {
			var context = {
				data: facilityData,
				sectors: facilitySectors,
				stateName: stateName,
				lgaName: lgaName,
				triggers: [],
				trigger: function addTrigger(tname, edata) {
				    this.triggers.push([tname, edata || {}]);
				},
				buildTable: false
			};
			onLoadCallback.call(context);
			
			if(!FACILITY_TABLE_BUILT && context.buildTable) {
			    buildFacilityTable(facilityData, facilitySectors);
			}
			if(context.triggers.length===0) {
			    //set up default page mode
			    $('body').trigger('select-sector', {
            	        fullSectorId: defaultSectorSlug
            	        });
			} else {
			    $.each(context.triggers, function(i, tdata){
    			    $('body').trigger(tdata[0], tdata[1]);
    			});
			}
		}
//		createSectorNav()
	}, function dataLoadFail(){
		//called when the lga data fails to load
		log("Data failed to load");
	});
}

// Moving "bind"ers up to the top.

$('body').bind('select-sector', function(evt, edata){
	var ftabs = $(facilityTabsSelector);
	
	(function(ftabs){
		ftabs.find('.'+specialClasses.showTd).removeClass(specialClasses.showTd);
		ftabs.removeClass(specialClasses.tableHideTd);
	})(ftabs);
	
	if(edata===undefined) {edata = {};}
    var sector, subSector, fullSectorId;
    
    (function(lsid){
        var lids = lsid.split(subSectorDelimiter);
        sector = lids[0];
        if(lids.length > 1) {
            subSector = lids[1];
        } else {
            subSector = undefined;
        }
        
        if(subSector===undefined) {
            subSector = 'general';
        }
        //would be good to confirm that sector &/or
        // subsector exist
        
        fullSectorId = [sector, subSector].join(subSectorDelimiter);
    })(edata.fullSectorId);
	
	if(sector !== undefined) {
		//fullSectorId is needed to distinguish between 
		// health:general  and  education:general (for example)
		
		if(selectedSector !== sector) {
		    $('body').trigger('unselect-facility');
		    $('body').trigger('unselect-column');
		    selectedSector = sector;
		    var ftabs = $(facilityTabsSelector);
		    ftabs.tabs('select', facilitySectorSlugs.indexOf(selectedSector));
		    (typeof(filterPointsBySector)==='function') && filterPointsBySector(selectedSector);
		}
		
		if(selectedSubSector!==fullSectorId) {
			$('body').trigger('unselect-sector');
			var selector = '#facilities-'+sector+' .subgroup-'+subSector;
			ftabs.find(selector).addClass(specialClasses.showTd);
			ftabs.addClass(specialClasses.tableHideTd);
			selectedSubSector = fullSectorId;
			$('.sub-sector-list a.selected').removeClass('selected');
			$('.sub-sector-list').find('a.subsector-link-'+subSector).addClass('selected');
		}
		olStyling.setMode(facilityData, 'main');
	} else {
		$('body').trigger('unselect-sector');
	}
});
$('body').bind('unselect-sector', function(evt, edata){
	$(facilityTabsSelector)
		.removeClass(specialClasses.tableHideTd)
		.find('.'+specialClasses.showTd).removeClass(specialClasses.showTd);
});

$('body').bind('select-facility', function(evt, edata){
	var facility = facilityData.list[edata.uid];
	if(facility === selectedFacility) {
		return false;
	}
	
	selectedFacility === undefined || $('body').trigger('unselect-facility', {uid: selectedFacility.uid});
	
	selectedFacility = facility;
	facility.tr === undefined || $(facility.tr).addClass('selected-facility');

	//scrolls to row by default (?)
//		if (edata.scrollToRow === undefined) { edata.scrollToRow = true; }

	edata.scrollToRow && (function scrollToTheFacilitysTr(){
		if(facility.tr!==undefined) {
			var ourTr = $(facility.tr);
			var offsetTop = ourTr.offset().top - ourTr.parents('table').eq(0).offset().top
			var tabPanel = ourTr.parents('.ui-tabs-panel');
			tabPanel.scrollTo(offsetTop, 500, {
				axis: 'y'
			});
		}
	})();

	$.each(facilityData.list, function(i, fdp){
	    olStyling.markIcon(fdp, facility===fdp ? 'showing' : 'hidden');
	});
    
	var popup = $("<div />");
	var sector = $(facilitySectors).filter(function(){return this.slug==facility.sector}).get(0);
	(function buildDefinitionList(){
		var tab = $("<table />").css({
			'width': 400
		});
		var imgFullUrl = ("http://nmis.mvpafrica.org/site-media/attachments/" + facility.img_id).toLowerCase();
		var imgLink = $("<a />", {'href':imgFullUrl, 'target': '_BLANK'}).html($("<img />", {src: imgFullUrl}).css({'width': 90}));
		popup.prepend(imgLink);

		$(sector.columns).each(function(i, col){
			var tr = $("<tr />");
			var colSlug = col.slug;
			var colName = col.name;
			tr.append($("<td />").text(colName))
			tr.append($("<td />").text(facility[colSlug]))
			tab.append(tr);
		});
		popup.append(tab);
	})();
	popup._showSideDiv({
	    title: "Facility "+ facility.uid,
		close: function(){
		    $('body').trigger('unselect-facility');
		}
	});
});

$('body').bind('unselect-facility', function(){
    $('tr.selected-facility').removeClass('selected-facility');
});

function getColDataDiv() {
	var colData = $('.widget-outer-wrap').find('div.column-data');
	if(colData.length===0) {
		colData = $("<div />", {'class': 'column-data'});
		$('.widget-outer-wrap').prepend($('<div />', {'class':'column-data-wrap'}).html(colData));
	}
	return colData;
}

function getTabulations(sector, col) {
	var sList = facilityData.bySector[sector];
	var valueCounts = {};
	$(sList).each(function(i, id){
		var fac = facilityData.list[id];
		var val = fac[col];
		if(valueCounts[val] === undefined) {
			valueCounts[val] = 0;
		}
		valueCounts[val]++;
	});
	return valueCounts;
}

$('body').bind('select-column', function(evt, edata){
	var wrapElement = $('#lga-facilities-table');
	var column = edata.column;
	var sector = edata.sector;
	if(selectedColumn!==edata.column) {
		$('body').trigger('unselect-column', {column:selectedColumn, nextColumn: edata.column});
		if(column.clickable) {
			$('.selected-column', wrapElement).removeClass('selected-column');
			(function highlightTheColumn(column){
				var columnIndex = column.thIndex;
				var table = column.th.parents('table');
				table.find('tr').each(function(){
					$(this).find('td').eq(columnIndex).addClass('selected-column');
				})
			})(column);
		}
		if(column.click_actions!== undefined && ~column.click_actions.indexOf('tabulate')) {
			var colDataDiv = getColDataDiv();
			var cdiv = $("<div />", {'class':'col-info'}).html($("<h2 />").text(column.name));
			if(column.description!==undefined) {
				cdiv.append($("<h3 />", {'class':'description'}).text(column.description));
			}
			var tabl = $("<table />").css({'width':'100%'});
			var tbod = $("<tbody />").appendTo(tabl);
			var tr = $("<tr />").appendTo(tbod);
			var tabulations = getTabulations(sector.slug, column.slug);
			$.each(tabulations, function(k, count){
				var td = $("<td />");
				td.append($("<strong />").text(k))
					.append($("<span />").text(': '))
					.append($("<span />", {'class': 'count'}).text(count));
				tr.append(td);
			});
			cdiv.append(tabl);
			colDataDiv.html(cdiv)
					.css({'height':80});
		}
		var columnMode = "view_column_"+column.slug;
		if(~column.click_actions.indexOf('iconify') && column.iconify_png_url !== undefined) {
		    var t=0, z=0;
		    var iconStrings = [];
		    $.each(facilityData.list, function(i, fdp){
		        if(fdp.sectorSlug===sector.slug) {
		            var iconUrl = column.iconify_png_url + fdp[column.slug] + '.png';
		            olStyling.addIcon(fdp, columnMode, {
		                url: iconUrl,
		                size: [16, 16]
		            });
		        }
        	});
        	olStyling.setMode(facilityData, columnMode);
		}
		selectedColumn = edata.column;
	}
});

$('body').bind('unselect-column', function(evt, edata){
	if(edata===undefined) { edata = {}; }
	getColDataDiv().empty().css({'height':0});
});

// page mode "bind"ers should be above.

var filterPointsBySector;
var FACILITY_TABLE_BUILT = false;

function buildFacilityTable(data, sectors){
    filterPointsBySector = function(sector){
        if(sector==='all') {
            log("show all sectors");
        } else {
            //On first load, the OpenLayers markers are not created.
            // this "showHide" function tells us when to hide the markers
            // on creation.
            function showHideMarker(pt, tf) {
                pt.showMrkr = tf;
                olStyling.markIcon(pt, tf ? 'showing' : 'hidden')
            }
            $.each(facilityData.list, function(i, pt){
                showHideMarker(pt, (pt.sector === sector))
            });
        }
    }
	FACILITY_TABLE_BUILT = true;
	var facilityTableWrap = $('#lga-facilities-table').html($('<div />', {'id': 'facility-tabs'}).html($('<ul />'))).append($('<div />', {'id':'image-nav'}));
	var ftabs = $(facilityTabsSelector, facilityTableWrap).css({'padding-bottom':18});
	var ftabUl = $('ul', ftabs);
	var imageNavigation = $('div#image-nav', facilityTableWrap);

/*    var allLink = $("<li />", {
            'html': $("<a />", {'href':'#all'}).text('All')
        }).appendTo($(ftabUl)); */
    
	$.each(facilitySectors, function(i, sector){
		var li = $("<li />");
		var fdata = facilityData.bySector[sector.slug] || facilityData.bySector[sector.name];
		var sectorCount = $("<span />", {'class':'sector-count '+sector.slug});
		if(fdata instanceof Array && fdata.length > 0) {
			sectorCount.text(" ("+fdata.length+")")
		}
		li.append($("<a />", {'href':'#facilities-'+sector.slug}).text(sector.name).append(sectorCount));
		ftabUl.append(li);
		ftabs.append(createTableForSectorWithData(sector, facilityData));
	});

	ftabs.tabs({select: function(evt, ui){
	    var sectorId = $(ui.panel).data('sector-slug');
	    
	    //* sammy setLocation will handle setting up the page:
	    _dashboard.setLocation([pageRootUrl, lgaId, sectorId].join("/"))
	    //* otherwise, we could trigger the event ourselves:
        //>> $(evt.target).trigger('select-sector', {fullSectorId: sectorId})
        //* doing both causes problems right now.
	}});

	(function deleteThisWhenYouWantToDoItProperly(){
		var stColors = {
  			'facilities-water': "blue",
  			'facilities-health': "red",
  			'facilities-agriculture': "orange",
  			lga: "purple",
  			'facilities-education': "green",
  			defaultColor: "pink"
  		};
		$('.ui-tabs-nav', ftabs).find('li a').each(function(){
			var colorSlug = this.hash.replace("#", "");
			var flagColor = stColors[colorSlug];
			var flagUrl = "/static/images/geosilk/flag_"+flagColor+".png"
			$(this).prepend($("<img />", {src: flagUrl, 'class': 'flag'}));
		})
	})();
	ftabs.height(220);
	ftabs.find('.ui-tabs-panel').css({'overflow':'auto','height':'75%'})
	facilityTableWrap.addClass('ready');
	loadMap && launchOpenLayers({
		centroid: {
			lat: 649256.11813719,
			lng: 738031.10112355
		}
	})(function(){
	    function urlForSectorIcon(s) {
	        var surveyTypeColors = {
        		water: "water_s",
        		health: "clinic_s",
        		agriculture: "orange",
        		lga: "purple",
        		education: "school_b",
        		'default': "pink"
        	};
	        var st = surveyTypeColors[s] || surveyTypeColors['default'];
	        return '/static/images/icons/'+st+'.png';
	    }
		var iconMakers = {};
//		window._map = this.map;
		var markers = new OpenLayers.Layer.Markers("Markers");
		var bounds = new OpenLayers.Bounds();
		$.each(facilityData.list, function(i, d){
    	        if(d.latlng!==undefined) {
    	            d.sectorSlug = (d.sector || 'default').toLowerCase();
    	            olStyling.addIcon(d, 'main', {
    	                url: urlForSectorIcon(d.sectorSlug),
    	                size: [34, 20]
    	            });
    	            var ll = d.latlng;
    	            var oLl = new OpenLayers.LonLat(ll[1], ll[0]).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
    	            d.openLayersLatLng = oLl;
    	            bounds.extend(oLl);
/*
            	    var ll = d.latlng;
            	    
            	    d.mrkr = new OpenLayers.Marker(oLl, icon);
            	    
            	    //checks to see if the facility has already been hidden
            	    if(d.showMrkr !== undefined && !d.showMrkr) {
            	        olStyling.markIcon(d.mrkr, 'hidden');
            	    }
            	    d.mrkr.facilityUid = d.uid;
            	    d.mrkr.events.on({
            	        'click': function(evt){
            	            $(evt.element).trigger('select-facility', {'uid': d.uid});
            	        }
            	    });
            	    markers.addMarker(d.mrkr);
            	    bounds.extend(oLl); */
    	        } 
    	});
    	olStyling.setMarkerLayer(markers);
    	olStyling.setMode(facilityData, 'main');
		var tilesat = new OpenLayers.Layer.TMS("Boundaries", "http://tilestream.openmangrove.org:8888/",
		            {
		                layerName: 'nigeria_overlays_white',
		                type: 'png'
		            });
		this.map.addLayers([tilesat, markers]);
        // (function defineNewZoomer(map){
        //  map.zoomToExtentInBox = (function(){
        //      return function(bounds, pixel, size){
        //          if(pixel instanceof Array) { pixel = new OpenLayers.Pixel(pixel[0], pixel[1]) }
        //          if(size instanceof Array) { size = new OpenLayers.Size(size[0], size[1]) }
        //          (function(){
        //              var center = bounds.getCenterLonLat();
        //              if (this.baseLayer.wrapDateLine) {
        //                  var maxExtent = this.getMaxExtent();
        //                  bounds = bounds.clone();
        //                  while (bounds.right < bounds.left) {
        //                      bounds.right += maxExtent.getWidth();
        //                  }
        //                  center = bounds.getCenterLonLat().wrapDateLine(maxExtent);
        //              }
        //              this.setCenter(center, this.getZoomForExtent(bounds, false)-1);
        //          }).call(map)
        //      }
        //  })()
        // })(this.map);
    	this.map.zoomToExtent(bounds);//, [10, 10], [200, 200]);
	});
}

function createTableForSectorWithData(sector, data){
	var div = $("<div />", {id: 'facilities-'+sector.slug}).text(sector.name).data('sector-slug', sector.slug);
	var table = $('<table />', {'class':'facility-list'});
	var thRow = $("<tr />");
	table.append($("<thead />").html(thRow));
	var sectorData  = data.bySector[sector.slug] || data.bySector[sector.name];
	function displayOrderSort(a,b) {
		return (a.display_order > b.display_order) ? 1 : -1
	}
	if(sector.columns!==undefined && sector.columns.length>0 && sectorData!==undefined && sectorData.length>0) {
		$.each(sector.columns.sort(displayOrderSort), function(i, col){
			var th = $("<th />", {'class':'col-'+col.slug}).text(col.name).addClass(col.clickable ? "clickable" : "not-clickable");
			$(col.subgroups).each(function(i, sg){
				th.addClass('subgroup-'+sg);
			});
			col.th = th;
			col.thIndex = i;
			th.click(function(){
				$('body').trigger('select-column', {
					sector: sector,
					column: col
				});
			});
			thRow.append(th)
			});
		var tbod = $("<tbody />");
		$.each(sectorData, function(i, fUid){
			tbod.append(createRowForFacilityWithColumns(data.list[fUid], sector.columns))
		})
		table.append(tbod);
	}
	var subSectors = $("<div />").addClass("sub-sector-list");
	function createSpanForSubSector(ssName, ssSlug, url) {
	    return $("<a />", {'href': url}).text(ssName).addClass('subsector-link-'+ssSlug);
	}
	subSectors.append(createSpanForSubSector("General", 'general', [pageRootUrl, lgaId, sector.slug].join("/")));
	$.each(sector.subgroups, function(i, sg){
	    if(sg.slug!=='general') {
	        subSectors.append(createSpanForSubSector(sg.name, sg.slug, [pageRootUrl, lgaId, [sector.slug, sg.slug].join(subSectorDelimiter)].join("/")));
	    }
	})
	div.html(subSectors)
	    .append(table);
	return div;
}
function createRowForFacilityWithColumns(fpoint, cols){
	var tr = $("<tr />");
	$.each(cols, function(i, col){
		var colSlug = col.slug;
		var value = fpoint[colSlug];
		if(value===undefined) { value = '—'; }
		var td = $("<td />", {'class':'col-'+colSlug});
		if(col.display_style=="checkmark") {
		    td.addClass('checkmark')
			    .html($("<span />", {'class':'mrk'}));
			if($.type(value) === 'boolean' && !!value) {
			    td.addClass('on')
			} else if($.type(value) === 'boolean') {
			    td.addClass('off')
			} else {
			    td.addClass('null');
			}
		} else if(col.calc_action=="binarytally") {
			var cols = col.calc_columns.split(" ");
			var valx = (function calcRatio(pt, cols){
				var tot = 0;
				var yCount = 0;
				var vv = [];
				$(cols).each(function(i, slug){
					var val = pt[slug];
					if(val!==undefined && $.type(val)==='boolean') {
						if(val) {
							yCount += 1;
						}
					}
					tot += 1;
				})
				return [yCount, tot];
			})(fpoint, cols);
			td.data('decimalValue', valx[0]/valx[1]);
			td.append($("<span />", {'class':'numerator'}).text(valx[0]))
			    .append($("<span />", {'class':'div'}).text('/'))
			    .append($("<span />", {'class':'denominator'}).text(valx[1]));
		} else {
			td.text(value);
		}
		$(col.subgroups).each(function(i, sg){
			td.addClass('subgroup-'+sg);
		});
		tr.append(td);
		tr.data('facility-uid', fpoint.uid);
	});
	tr.click(function(){$(this).trigger('select-facility', {
		'uid': fpoint.uid,
		'scrollToRow': false
	})});
	fpoint.tr = tr.get(0);
	return tr;
}
var facilityDataStuff = (function(dataReq, passedData){
    if(dataReq[2].processedData !== undefined) {
	    facilityData = dataReq[2].processedData.data;
	    facilitySectors = dataReq[2].processedData.sectors;
    } else {
		var data, sectors, noLatLngs=0;
		facilitySectorSlugs = [];
		
		passedData === undefined && warn("No data was passed to the page", passedData);
		
		debugMode && (function validateSectors(s){
		    // this is called if debugMode is true.
		    // it warns us if the inputs are wrong.
		    if(s===undefined || s.length == 0) {
		        warn("data must have 'sectors' list.")
		    }
		    var _facilitySectorSlugs = [];
			$(s).each(function(){
				this.name === undefined && warn("Each sector needs a name.", this);
				this.slug === undefined && warn("Each sector needs a slug.", this);
				this.columns instanceof Array || warn("Sector columns must be an array.", this);
				(this.slug in _facilitySectorSlugs) && warn("Slugs must not be used twice", this);
				_facilitySectorSlugs.push(this.slug);
				$(this.columns).each(function(i, val){
					var name = val.name;
					var slug = val.slug;
					name === undefined && warn("Each column needs a slug", this);
					slug === undefined && warn("Each column needs a name", this);
				});
			});
			sectors = s;
		})(passedData.sectors);
		
		sectors = passedData.sectors;
		facilitySectorSlugs = (function validateSectors(s){
		    var _facilitySectorSlugs = [];
			$.each(s, function(i, t){
				_facilitySectorSlugs.push(t.slug);
			});
			return _facilitySectorSlugs;
		})(passedData.sectors);
		
		debugMode && (function validateData(d) {
		    d === undefined && warn('Data must be defined');
		    
			d.length === undefined && warn("Data must be an array", this);
			
			$(d).each(function(i, row){
				this.sector === undefined && warn("Each row must have a sector", this);
				if(this.latlng === undefined) {
					//some points don't have latlngs but should show up in tables.
					noLatLngs++;
				} else {
					(this.latlng instanceof Array) || warn("LatLng must be an array", this);
					(this.latlng.length === 2) || warn("Latlng must have length of 2", this);
				}
				
				(!!~facilitySectorSlugs.indexOf(this.sector.toLowerCase())) || warn("Sector must be in the list of sector slugs:", {
					sector: this.sector,
					sectorSlugs: facilitySectorSlugs,
					row: this
				});
			});
		})(passedData.data);
		
		(function processData(rawData){
			function makeLatLng(val) {
				if(val !== undefined) {
					var lll = val.split(" ");
					return [
						+lll[0],
						+lll[1]
						]
				} else {
					return undefined
				}
			}
			var uidCounter = 0;
			var list = {};
			var groupedList = {};
			var sectorNames = [];
			$.each(rawData, function(i, pt){
				if(pt.uid===undefined) { pt.uid = 'uid'+i; }
				pt.latlng = makeLatLng(pt.gps);
				pt.sector = pt.sector.toLowerCase();
				if(!~sectorNames.indexOf(pt.sector)) {
					sectorNames.push(pt.sector);
					groupedList[pt.sector] = [];
				}
				groupedList[pt.sector].push(pt.uid);
				list[pt.uid]=pt;
			});
			data = {
				bySector: groupedList, //sector-grouped list of IDs, for the time being
				list: list //the full list (this is actually an object where the keys are the unique IDs.)
			};
		})(passedData.data);
		
		debugMode && (function printTheDebugStats(){
			log("" + sectors.length + " sectors were loaded.");
			var placedPoints = 0;
			$(sectors).each(function(){
				if(data.bySector[this.slug] === undefined) {
					log("!->: No data loaded for "+this.name);
				} else {
					var ct = data.bySector[this.slug].length;
					placedPoints += ct;
					log("   : "+this.slug+" has "+ct+" items.", this);
				}
			});
			log(noLatLngs + " points had no coordinates")
		})();
		
		facilityData = data;
		window._facilityData = data;
    	facilitySectors = sectors;
    	//save it in the request object to avoid these checks
    	// in future requests...
    	//   (quick way to cache)
		dataReq[2].processedData = {
		    data: data,
		    sectors: sectors
		};
	}
});

function createSectorNav() {
	if($('.content-inner-wrap .sn-wrap').length==0) {
		var snWrap = $("<div />", {'class':'sn-wrap'}).appendTo($('.content-inner-wrap'));
	} else {
		var snWrap = $('.content-inner-wrap').find('.sn-wrap');
	}
	var sn = $('<div />', {'class':'sn'});
	var ul = $("<ul />");
	$(facilitySectors).each(function(i, sector){
		var name = sector.name;
		var slug = sector.slug;
		var sectorUrl = [pageRootUrl, lgaId, sector.slug].join("/");
		var l = $("<a />", {'href': sectorUrl}).text(sector.name);
		l.data('sectorSlug', sector.slug);
		l.data('subSectorSlug', 'general');
		
		var li = $("<li />").appendTo(ul)
				.html(l);
		var sul = $("<ul />").appendTo(ul);
		$(sector.subgroups).each(function(i, subgroup){
			if(subgroup.slug!=='general') {
				var li = $("<li />").appendTo(sul);
				var sectorUrl = [pageRootUrl, lgaId, [sector.slug, subgroup.slug].join(subSectorDelimiter)].join("/");
        		
				var sgLink = $("<a />", {'href':sectorUrl}).text(subgroup.name).appendTo(li);
				sgLink.data('sectorSlug', sector.slug);
				sgLink.data('subSectorSlug', subgroup.slug)
			}
		});
	});
	sn.append(ul);
	snWrap.html(sn);
	$('.content-inner-wrap').prepend()
}
return {
    loadData: loadLgaData,
    buildTable: buildFacilityTable
}
//ending "lga" wrap.
})();