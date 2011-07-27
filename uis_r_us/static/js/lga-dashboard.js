;
// BEGIN temporary side-div jquery wrapper
//   -- trying to keep the right-div popup logic separate form the rest
//    of the application logic.
(function($){
	var overMapContent;
	var rightDiv, rdNav;
	var mapContent;
	$.fn._showSideDiv = function(opts){
	    if(opts===undefined) { opts={}; }
		if(mapContent===undefined) { mapContent = $('.content-inner-wrap'); }
		if(rightDiv===undefined) {
			var rightDiv = $("<div />", {'class':'rd-wrap'}).appendTo(mapContent);
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
		rightDiv
		    .html(this.eq(0))
		    .show();
	}
})(jQuery);
// END temporary side-div jquery wrapper

// BEGIN custom openlayers icon functionality
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
                        fac.mrkr.events.register('click', fac.mrkr, function(){
                            $('body').trigger('select-facility', {
                                'uid': fac.uid,
                                'scrollToRow': true
                            })
                        });
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
// END custom openlayers icon functionality

// BEGIN CLOSURE: LGA object
//   --wraps everything to keep it out of the global scope.
var lga = (function(){

// BEGIN closure scope variable declaration
//   --marking which variables are going to be reused between functions
var selectedSubSector,
    selectedSector,
    selectedFacility,
    selectedColumn,
    facilitySectorSlugs,
    facilityData,
    facilitySectors;


var facilityTabsSelector = 'div#facility-tabs';

var specialClasses = {
    showTd: 'show-me',
    tableHideTd: 'hide-tds'
};
var urls = {
    variables: '/facility_variables',
    lgaSpecific: '/facilities/site/'
};

var subSectorDelimiter = '-';
var defaultSubSector = 'general';
// END closure scope variable declaration

// BEGIN load lga data via ajax
function loadLgaData(lgaUniqueId, onLoadCallback) {
    var siteDataUrl = urls.lgaSpecific + lgaUniqueId;
    var variablesUrl = urls.variables;
	var fv1 = $.getCacheJSON(siteDataUrl);
	var fvDefs = $.getCacheJSON(variablesUrl);
	var fvDict = $.getCacheJSON("/static/json/variable_dictionary.json");
	$.when(fv1, fvDefs, fvDict).then(function(lgaQ, varQ, varDict){
	    var variableDictionary = varDict[0];
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
		
//		buildLgaProfileBox(lgaData, variableDictionary.profile_variables);
//		buildGapAnalysisTable(lgaData);
		processFacilityDataRequests(lgaQ, {sectors: variableDefs, data: facilityDataARr});
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
	}, function dataLoadFail(){
		log("Data failed to load");
	});
};
(function($){
    //a quick ajax cache, merely trying to prevent multiple
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
// END load lga data via ajax

// BEGIN lga-wide profile boxes
function buildLgaProfileBox(lga, dictionary) {
    var oWrap = $('.content-inner-wrap').find('.profile-data-wrap');
    if(oWrap.length===0) {
        oWrap = $("<div />", {'class':'profile-data-wrap'}).appendTo($('.content-inner-wrap'));
    } else {
        oWrap.empty();
    }
    var wrap = $("<div />", {'class':'profile-data'})
        .append($("<h3 />").text(lga.stateName))
        .append($("<h2 />").text(lga.lgaName))
        .append($("<hr />"));
    
    $("<table />").append((function(tbody, pdata){
        $.each(dictionary, function(k, val){
            var name = val.name;
            var value = pdata[k];
            var tr = $("<tr />")
                .append($("<td />").text(name))
                .append($("<td />").text(value));
            tbody.append(tr);
        });
        return tbody;
    })($('<tbody />'), lga.profileData))
        .appendTo(wrap);
    oWrap.html(wrap);
}


function getGaTable(){
    var gt = $('.widget-outer-wrap').find('div.gap-analysis-table');
	if(gt.length===0) {
		gt = $("<div />", {'class': 'gap-analysis-table'});
		$('.widget-outer-wrap').prepend($('<div />', {'class':'gap-analysis-table-wrap'}).html(gt));
	}
	return gt;
}

function buildGapAnalysisTable(lgaData){
    var data = lgaData.profileData;
    var gaTableWrap = getGaTable();
    var table = $('#gap-analysis-table-template').children().eq(0).clone();
    table.find('.fill-me').each(function(){
        var slug = $(this).data('variableSlug');
        $(this).text(roundDownValueIfNumber(data[slug]))
    });
    //hiding gap analysis table by default for now.
    gaTableWrap.parents().eq(0)
            .addClass('toggleable')
            .addClass('hidden')
    return gaTableWrap.html(table);
}
// END lga-wide profile boxes


// BEGIN page mode binders
//  -- These 6 "bind" methods define global event listeners which trigger behavior
//     in individual dashboard featured. (the table, the map, etc.)
//     The global events are "select-" and "unselect-" each of the following:
//        * sector
//        * column
//        * facility
//     All functions accessed in this file are defined elsewhere in the file.
//     (Except jquery stuff and LaunchOpenLayers)
$('body').bind('select-sector', function(evt, edata){
	if(edata===undefined) {edata = {};}
    var sector, subSector, fullSectorId;
    
    if(edata.fullSectorId !== undefined) {
        (function(lsid){
            var lids = lsid.split(subSectorDelimiter);
            sector = lids[0];
            if(lids.length > 1) {
                subSector = lids[1];
            } else {
                subSector = undefined;
            }

            if(subSector===undefined) {
                subSector = defaultSubSector;
            }
            //would be good to confirm that sector &/or
            // subsector exist

            fullSectorId = [sector, subSector].join(subSectorDelimiter);
        })(edata.fullSectorId);
    }
	
	var ftabs = $(facilityTabsSelector);
	ftabs.find('.'+specialClasses.showTd).removeClass(specialClasses.showTd);
	ftabs.removeClass(specialClasses.tableHideTd);
	if(sector !== undefined) {
		//fullSectorId is needed to distinguish between 
		// health:general  and  education:general (for example)
		
		if(selectedSector !== sector) {
		    $('body').trigger('unselect-facility');
		    $('body').trigger('unselect-column');
		    selectedSector = sector;
            ftabs.find('.facility-list-wrap').hide()
                    .filter(function(){
                        if(this.id == "facilities-"+selectedSector) { return true; }
                    }).show();
		    (typeof(filterPointsBySector)==='function') && filterPointsBySector(selectedSector);
		}

		var sectorObj = $(facilitySectors).filter(function(){return this.slug==sector}).get(0);
		setSummaryHtml(sectorObj.name + " Facilities");
		if(selectedSubSector!==fullSectorId) {
			$('body').trigger('unselect-sector');
			var tabWrap = $('#facilities-'+sector, ftabs);
			tabWrap.find('.subgroup-'+subSector).addClass(specialClasses.showTd);
			tabWrap.find('.row-num').addClass(specialClasses.showTd);
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

function imageUrls(imageSizes, imgId) {
    return {
        small: ["/survey_photos", imageSizes.small, imgId].join("/"),
        large: ["/survey_photos", imageSizes.large, imgId].join("/"),
        original: ["/survey_photos", 'original', imgId].join("/")
    }
}

$('body').bind('select-facility', function(evt, edata){
	var facility = facilityData.list[edata.uid];
	if(facility === selectedFacility) {
		return false;
	}
	
	selectedFacility === undefined || $('body').trigger('unselect-facility', {uid: selectedFacility.uid});
	selectedFacility = facility;
	
	facility.tr === undefined || $(facility.tr).addClass('selected-facility');

    // if (edata.scrollToRow === undefined) { edata.scrollToRow = true; }

	edata.scrollToRow && false && (function scrollToTheFacilitysTr(){
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
	var name = facility.name || facility.facility_name || facility.school_name;
    getMustacheTemplate('facility_popup', function(){
        var data = {sector_data: []};
        data.name = name || sector.name + ' Facility';
		data.image_url = "http://nmis.mvpafrica.org/site-media/attachments/" +
		        (facility.photo || "image_not_found.jpg");
		var subgroups = {};
		$(sector.columns).each(function(i, col){
		    $(col.subgroups).each(function(i, val){
		        if(val!=="") {
		            if(!subgroups[val]) { subgroups[val] = []; }
    		        subgroups[val].push({
    		            name: col.name,
    		            slug: col.slug,
    		            value: facility[col.slug]
    		        });
		        }
		    });
		});
		$(sector.subgroups).each(function(i, val){
            subgroups[this.slug] !== undefined &&
		        data.sector_data.push($.extend({}, val, { variables: subgroups[this.slug] }));
		});
		var pdiv = $(Mustache.to_html(this.template, data));
		pdiv.delegate('select', 'change', function(){
		    var selectedSector = $(this).val();
		    pdiv.find('div.facility-sector-select-box')
		        .removeClass('selected')
		        .filter(function(){
    		        if($(this).data('sectorSlug')===selectedSector) {
    		            return true;
    		        }
    		    })
    		    .addClass('selected');
		});
        popup.append(pdiv);
    });
	popup._showSideDiv({
	    title: name,
		close: function(){
		    $('body').trigger('unselect-facility');
		}
	});
});

$('body').bind('unselect-facility', function(){
    $.each(facilityData.list, function(i, fdp){
        if(selectedSector=="all" || fdp.sectorSlug === selectedSector) {
            olStyling.markIcon(fdp, 'showing');
        } else {
            olStyling.markIcon(fdp, 'hidden');
        }
	});
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
	$('body').trigger('unselect-column', {column:selectedColumn, nextColumn: edata.column});
	if(selectedColumn!==edata.column) {
		if(column.clickable) {
			$('.selected-column', wrapElement).removeClass('selected-column');
			(function highlightTheColumn(column){
				var columnIndex = column.thIndex;
				var table = column.th.parents('table');
				column.th.addClass('selected-column');
				table.find('tr').each(function(){
					$(this).find('td').eq(columnIndex).addClass('selected-column');
				})
			})(column);
		}
		function hasClickAction(col, str) {
		    return col.click_actions !== undefined && ~column.click_actions.indexOf(str);
		}
		if(hasClickAction(column, 'piechart')) {
		    var colDataDiv = getColDataDiv();
			var cdiv = $("<div />", {'class':'col-info'}).html($("<h2 />").text(column.name));
			cdiv.append($("<h2>").text("PIE CHART!!"))
			if(column.description!==undefined) {
				cdiv.append($("<h3 />", {'class':'description'}).text(column.description));
			}
			var tabulations = getTabulations(sector.slug, column.slug);
			cdiv.append($("<p>").text(JSON.stringify(tabulations)))
			colDataDiv.html(cdiv)
					.css({'height':120});
    	} else if(hasClickAction(column, 'tabulate')) {
    	    var tabulations = $.map(getTabulations(sector.slug, column.slug), function(k, val){
                return { 'value': k, 'occurrences': val }
            });
            getMustacheTemplate('facility_column_description', function(){
                var data = {
                    tabulations: tabulations,
                    sectorName: sector.name,
                    name: column.name,
                    descriptive_name: column.descriptive_name,
                    description: column.description
                };
                getColDataDiv()
                        .html(Mustache.to_html(this.template, data))
                        .css({'height':110});
            });
		}
		var columnMode = "view_column_"+column.slug;
		if(hasClickAction(column, 'iconify') && column.iconify_png_url !== undefined) {
		    var t=0, z=0;
		    var iconStrings = [];
		    $.each(facilityData.list, function(i, fdp){
		        if(fdp.sectorSlug===sector.slug) {
		            var iconUrl = column.iconify_png_url + fdp[column.slug] + '.png';
		            olStyling.addIcon(fdp, columnMode, {
		                url: iconUrl,
		                size: [34, 20]
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
    $('.selected-column').removeClass('selected-column');
    selectedColumn = undefined;
	getColDataDiv().empty().css({'height':0});
});
// END page mode binders

// BEGIN facility table builder
//   -- facility table builder receives the facility data
//      and builds a table for each sector. The rows of the
//      table correspond to the facilities.
var filterPointsBySector;
var FACILITY_TABLE_BUILT = false;

function setSummaryHtml(html) {
    return $('#summary-p').html(html);
}

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
	var facilityTableWrap = $('#lga-facilities-table');
	$('<div />', {'id': 'toggle-updown-bar'}).html($('<span />', {'class':'icon'}))
	    .appendTo(facilityTableWrap)
	    .click(function(){
	        facilityTableWrap.toggleClass('closed');
	    });
	$('<div />', {'id': 'facility-tabs'})
	    .appendTo(facilityTableWrap);
	$('<p />', {'id': 'summary-p'})
	    .appendTo(facilityTableWrap);
	var ftabs = $(facilityTabsSelector, facilityTableWrap).css({'padding-bottom':18});
	$.each(facilitySectors, function(i, sector){
		ftabs.append(createTableForSectorWithData(sector, facilityData));
	});
	ftabs.height(220);
	ftabs.find('.ui-tabs-panel').css({'overflow':'auto','height':'75%'});
	facilityTableWrap.addClass('ready');
	loadMap && launchOpenLayers({
		centroid: {
			lat: 649256.11813719,
			lng: 738031.10112355
		},
		layers: [
		    ["Nigeria", "nigeria_base"]
		],
		overlays: [
		    ["Boundaries", "nigeria_overlays_white"]
		]
	})(function(){
	    function urlForSectorIcon(s) {
	        var surveyTypeColors = {
        		water: "water_small",
        		health: "clinic_s",
        		education: "school_w"
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
                d.openLayersLatLng = new OpenLayers.LonLat(ll[1], ll[0])
                    .transform(new OpenLayers.Projection("EPSG:4326"),
                                new OpenLayers.Projection("EPSG:900913"));
                bounds.extend(d.openLayersLatLng);
            }
    	});
    	olStyling.setMarkerLayer(markers);
    	this.map.addLayer(markers);
    	olStyling.setMode(facilityData, 'main');
//		this.map.addLayers([tilesat, markers]);
    	this.map.zoomToExtent(bounds);
	});
}

var decimalCount = 2;
function roundDownValueIfNumber(val) {
    if(val===undefined) { return 'n/a'; }
    if($.type(val)==='object') {val = val.value;}
    if($.type(val)==='number' && (''+val).length>5) {
        return Math.floor(Math.pow(10, decimalCount)* val)/Math.pow(10, decimalCount);
    } else if($.type(val)==='string') {
        return splitAndCapitalizeString(val);
    }
    return val;
}
function capitalizeString(str) {
    var strstart = str.slice(0, 1);
    var strend = str.slice(1);
    return strstart.toUpperCase() + strend;
}
function splitAndCapitalizeString(str) { return $.map(str.split('_'), capitalizeString).join(' '); }

function createTableForSectorWithData(sector, data){
    var sectorData = data.bySector[sector.slug] || data.bySector[sector.name];
	if(!sector.columns instanceof Array || !sectorData instanceof Array) {
	    return;
    }
    
    var thRow = $('<tr />')
                .append($('<th />', {
                    'text': '#',
                    'class': 'row-num no-select'
                }));
    function displayOrderSort(a,b) { return (a.display_order > b.display_order) ? 1 : -1 }
	$.each(sector.columns.sort(displayOrderSort), function(i, col){
	    var thClasses = ['col-'+col.slug, 'no-select'];
		col.clickable && thClasses.push('clickable');

		$(col.subgroups).each(function(i, sg){
			thClasses.push('subgroup-'+sg);
		});

		var th = $('<th />', {
		            'class': thClasses.join(' '),
		            'text': col.name
		        })
		        .click(function(){
		            $('body').trigger('select-column', {sector: sector, column: col});
		        })
		        .appendTo(thRow);

		$.extend(col, { th: th, thIndex: i+1 });
	});

	var tbod = $("<tbody />");
	$.each(sectorData, function(i, fUid){
		tbod.append(createRowForFacilityWithColumns(data.list[fUid], sector.columns, i+1))
	});
	function subSectorLink(ssName, ssslug) {
	    var fullSectorSlug = sector.slug + (ssslug===defaultSubSector ? '' : subSectorDelimiter + ssslug)
	    return $('<a />', {'href': '#', 'class': 'subsector-link-'+ssslug})
	                .text(ssName)
	                .click(function(evt){
	                    $('body').trigger('select-sector', {fullSectorId: fullSectorSlug})
	                    evt.preventDefault();
	                });
	}
	var subSectors = (function(subSectors, splitter){
	    $.each(sector.subgroups, function(i, sg){
    	    sg.slug !== defaultSubSector &&
    	        subSectors.append(splitter.clone())
    	                .append(subSectorLink(sg.name, sg.slug));
    	});
    	return subSectors;
	})($('<div />', {'class': 'sub-sector-list no-select'}), $("<span />").text(" | "))
	    .prepend(subSectorLink("General", defaultSubSector));

    var table = $('<table />')
                    .addClass('facility-list')
                    .append($('<thead />').html(thRow))
                    .append(tbod);
    
	return $('<div />')
	    .attr('id', 'facilities-'+sector.slug)
	    .addClass('facility-list-wrap')
	    .data('sector-slug', sector.slug)
	    .append(subSectors)
	    .append(table);
}

function createRowForFacilityWithColumns(fpoint, cols, rowNum){
    //creates a row for the facility table. (only used in "createTableForSectorWithData")
	var tr = $("<tr />")
	        .data('facility-uid', fpoint.uid)
	        .click(function(){
	            //clicking a row triggers global event 'select-facility'
	            $(this).trigger('select-facility', {
        		    'uid': fpoint.uid,
        		    'scrollToRow': false
        	    })
        	})
        	.append($('<td />', {'class':'row-num', 'text': rowNum}));

	$.each(cols, function(i, col){
		var value = roundDownValueIfNumber(fpoint[col.slug]);
		var td = $('<td />')
		        .addClass('col-'+col.slug)
		        .appendTo(tr);
		if(col.display_style == "checkmark") {
			if($.type(value) === 'boolean') {
			    td.addClass(!!value ? 'on' : 'off')
			} else {
			    td.addClass('null');
			}
			td.addClass('checkmark')
			    .html($("<span />").addClass('mrk'));
		} else if(col.calc_action === "binarytally") {
		    //I think binarytally is no longer used.
			var cols = col.calc_columns.split(" ");
			var valx = (function calcRatio(pt, cols){
				var tot = 0;
				var num = 0;
				$(cols).each(function(i, slug){
					var val = pt[slug];
					num += ($.type(val) === 'boolean' && !!val) ? 1 : 0;
					tot += 1;
				});
				return [num, tot];
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
	});
	fpoint.tr = tr.get(0);
	return tr;
}
// END facility table builder

// BEGIN data processing:
//  -- data processing step receives the json data and 
//     processes it into the json format that is needed for the
//     page to function.
//     Note: in debug mode, it will give detailed descriptions of
//     the data is not in the correct format.
var processFacilityDataRequests = (function(dataReq, passedData){
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
		
		sectors = [];
		facilitySectorSlugs = [];
		
		(function(s){
		    //processing passed sector data.
		    var slugs = [];
		    var _s = [];
		    $.each(s, function(i, ss){
		        if(!~slugs.indexOf(ss.slug)) { slugs.push(ss.slug); }
		        _s.push(ss);
		    });
		    facilitySectorSlugs = slugs;
		    sectors = _s;
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
			$.each(sectors, function(i, s){
                if(!groupedList[s.slug]) {
                    groupedList[s.slug] = [];
                }
            });
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
// END data processing

return {
    loadData: loadLgaData
}
})();
// END CLOSURE: LGA object
