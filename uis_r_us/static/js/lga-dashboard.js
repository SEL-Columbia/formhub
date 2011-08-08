;
// BEGIN raphael graph wrapper
var createOurGraph = (function(pieWrap, legend, data, _opts){
    //creates a graph with some default options.
    // if we want to customize stuff (ie. have behavior that changes based on
    // different input) then we should work it into the "_opts" parameter.
    var gid = $(pieWrap).get(0).id;
    var defaultOpts = {
        x: 50,
        y: 40,
        r: 35,
        font: "12px 'Fontin Sans', Fontin-Sans, sans-serif"
    };
    var opts = $.extend({}, defaultOpts, _opts);
    var rearranged_vals = $.map(legend, function(val){
        return $.extend(val, {
            value: data[val.key]
        });
    });
    var pvals = (function(vals){
        var values = [];
    	var colors = [];
    	var legend = [];
    	vals.sort(function(a, b){ return b.value - a.value; });
    	$(vals).each(function(){
    		if(this.value > 0) {
    			values.push(this.value);
    			colors.push(this.color);
    			legend.push('%% - ' + this.legend + ' (##)');
    		}
    	});
    	return {
    		values: values,
    		colors: colors,
    		legend: legend
    	}
    })(rearranged_vals);
    // NOTE: hack to get around a graphael bug!
    // if there is only one color the chart will
    // use the default value (Raphael.fn.g.colors[0])
    // here, we will set it to whatever the highest
    // value that we have is
    Raphael.fn.g.colors[0] = pvals.colors[0];
    var r = Raphael(gid);
    r.g.txtattr.font = opts.font;
    var pie = r.g.piechart(opts.x, opts.y, opts.r,
            pvals.values, {
                    colors: pvals.colors,
                    legend: pvals.legend,
                    legendpos: "east"
                });
    pie.hover(function () {
        this.sector.stop();
        this.sector.scale(1.1, 1.1, this.cx, this.cy);
        if (this.label) {
            this.label[0].stop();
            this.label[0].scale(1.4);
            this.label[1].attr({"font-weight": 800});
        }
    }, function () {
        this.sector.animate({scale: [1, 1, this.cx, this.cy]}, 500, "bounce");
        if (this.label) {
            this.label[0].animate({scale: 1}, 500, "bounce");
            this.label[1].attr({"font-weight": 400});
        }
    });
    return r;
});
// END raphael graph wrapper

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
                            setFacility(fac.uid);
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
    overviewVariables,
    facilitySectors;


var facilityTabsSelector = 'div.lga-widget-content';

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
		if(!!lgaData.error) {
		    return $('<p />')
		        .attr('title', 'Error')
		        .text(lgaData.error)
		        .appendTo($('#map'))
		        .dialog();
		}
		var facilityData = lgaData.facilities;
		var varDataReq = varQ[0];
		var facilityDataARr = [];
		$.each(facilityData, function(k, v){
			v.uid = k;
			facilityDataARr.push(v);
		});
		
        buildLgaProfileBox(lgaData, variableDictionary.profile_variables);
//		buildGapAnalysisTable(lgaData);
		processFacilityDataRequests(lgaQ, {
		    sectors: varDataReq.sectors,
		    overview: varDataReq.overview,
		    data: facilityDataARr
		});
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
		    !FACILITY_TABLE_BUILT && buildFacilityTable(
		                $('#lga-widget-wrap'),
		                facilityData, facilitySectors, lgaData);
			onLoadCallback.call(context);
			if(context.triggers.length===0) {
			    //set up default page mode
//			    setSector(defaultSectorSlug);
//			    $('body').trigger('select-sector', {
//            	        fullSectorId: defaultSectorSlug,
//            	        viewLevel: 'facility'
//            	        });
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
function getBoxOrCreateDiv(container, selector, creator) {
    var d = $(container).find(selector)
    if(d.length===0) {
        d = $.apply($, creator)
                .appendTo(container);
    }
    return d
}


function buildLgaProfileBox(lga, dictionary) {
    var oWrap = getBoxOrCreateDiv('.content-inner-wrap', '.profile-data-wrap', ['<div />', {'class':'profile-data-wrap'}])
    var wrap = $("<div />", {'class':'profile-data'})
        .append($("<h3 />").text(lga.stateName))
        .append($("<h2 />").text(lga.lgaName))
        .append($("<hr />"));

	$('.map-key-w').find('.profile-toggle').addClass('active-button');

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

// BEGIN page mode setters.
//  --ie. a bunch of methods to set various page states.
//    eg. setSector setViewMode setFacility setColumn
(function(){
    var nav;
    window.getNav = function(){
        if(nav===undefined || nav.length===0) { nav = $('.map-key-w'); }
        return nav;
    }
})();
function getColDataDiv() {
	var colData,
	    colDataWrap = $('.widget-outer-wrap').find('div.column-data-wrap');
	if(colDataWrap.length===0) {
		colDataWrap = $("<div />", {'class': 'column-data-wrap'});
		$('<a />', {'href': '#', 'class': 'close-col-data'})
		    .text('X')
		    .click(function(){
		        colDataWrap.hide();
		    })
		    .appendTo(colDataWrap);
		colData = $('<div />', {'class': 'column-data'})
		    .appendTo(colDataWrap);
		$('.widget-outer-wrap').prepend(colDataWrap);
	} else {
	    colData = colDataWrap.find('.column-data');
	}
	colDataWrap.show();
	return colData;
}

(function(){
    // BEGIN SETTER: sector
    var sectors = 'overview health education water'.split(' ');
    var _sector, _prevSector,
        _fullSectorId, _prevFullSectorId;
    window._sectorOnLeave = null;
    //right now, some things need access to the current sector slug,
    //  but I'm not sure if/how to expose it to the global scope yet.
    window.__sector = null;

    function subSectorExists(){return true;/*-- TODO: fix this --*/}

    window.setSector = function(s, ss){
        var curSectorObj = $(facilitySectors).filter(function(){return this.slug==s}).get(0);
        var fsid,
            stabWrap,
            changeSector = false
            changeSubSector = false;
        if(~sectors.indexOf(s)) { if(_sector !== s) {_prevSector = _sector; __sector = _sector = s; changeSector = true;} } else { warn("sector doesn't exist", s); }
        if(changeSector) {
//            ensureValidSectorLevel(__viewMode, s);
            // if a "leave" function is defined, it is executed and removed
            if(typeof _sectorOnLeave ==='function') {_sectorOnLeave(); _sectorOnLeave = null;}

            var nav = getNav();
            nav.find('.active-button.sector-button').removeClass('active-button');
            nav.find('.sector-'+s).addClass('active-button');

            //remove all TD filtering classes
            var ftabs = $(facilityTabsSelector);
            ftabs.find('.'+specialClasses.showTd).removeClass(specialClasses.showTd);
            ftabs.removeClass(specialClasses.tableHideTd);

            ftabs.find('.modeswitch').addClass('fl-hidden-sector')
                    .filter(function(){
                        if($(this).data('sectorSlug')===_sector) { return true; }
//                        if(this.id == "facilities-"+_sector) { return true; }
                    }).removeClass('fl-hidden-sector');
		    (typeof(filterPointsBySector)==='function') && filterPointsBySector(_sector);

            log("changing sector to", _sector);
        }

        if(curSectorObj===undefined) { return; }
        if(curSectorObj.subgroups===undefined) { return; }
        if(!curSectorObj.subgroups.length===0) { return; }
        if(ss===undefined) {
            ss = curSectorObj.subgroups[0].slug;
        }

        fsid = s + ':' + ss;
        if(subSectorExists(fsid)) { if(_fullSectorId !== fsid) { _prevFullSectorId = _fullSectorId; _fullSectorId = fsid; changeSubSector = true; }}
        if(changeSubSector) {
            var ftabs = $(facilityTabsSelector);
            
            (function markSubsectorLinkSelected(stabWrap){
                var ssList = stabWrap.find('.sub-sector-list');
                ssList.find('.selected')
                    .removeClass('selected');
                ssList.find('.subsector-link-'+ss)
                    .addClass('selected');
            })(ftabs.find('.mode-facility.sector-'+s))
            ftabs.find('.'+specialClasses.showTd).removeClass(specialClasses.showTd)
            ftabs.find('.row-num, .subgroup-'+ss)
                .addClass(specialClasses.showTd);
            ftabs.addClass(specialClasses.tableHideTd);
//            var nav = getNav();
//            nav.find('.sector-notes').text('subsector: '+ss);
        }
        return changeSubSector;
    }
    // END SETTER: sector
})();

(function(){
    // BEGIN SETTER: viewMode
    var viewModes = 'facility lga'.split(' ');
    var _viewMode, _prevViewMode;
    
    window.__viewMode = null;
    window.setViewMode = function SetViewMode(s){
        var change = false;
        if(~viewModes.indexOf(s)) { if(_viewMode !== s) {_prevViewMode = _viewMode; __viewMode = _viewMode = s; change = true;} } else { warn("viewMode doesn't exist", s); }
        if(change) {
//            ensureValidSectorLevel(s, );
            var nav = getNav();
            nav.find('.active-button.view-mode-button').removeClass('active-button');
            nav.find('.view-mode-'+s).addClass('active-button');

            var ftabs = $(facilityTabsSelector);
            ftabs.find('.modeswitch').addClass('fl-hidden-view-mode');
            ftabs.find('.modeswitch.mode-'+_viewMode).removeClass('fl-hidden-view-mode');
            log("changing view mode to", _viewMode);
        }
        return change;
    }
    // END SETTER: viewMode
})();

function imageUrls(imageSizes, imgId) {
    return {
        small: ["/survey_photos", imageSizes.small, imgId].join("/"),
        large: ["/survey_photos", imageSizes.large, imgId].join("/"),
        original: ["/survey_photos", 'original', imgId].join("/")
    }
}

(function(){
    // BEGIN SETTER: facility
    var _facility, _previousFacility;

    window.setFacility = function(fId){
        var facility = facilityData.list[fId];
        if(facility!==undefined) {
            facility.tr === undefined || $(facility.tr).addClass('selected-facility');
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
            		            value: displayValue(facility[col.slug])
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
        		pdiv.find('select').trigger('change');
                popup.append(pdiv);
                popup.attr('title', name);
                var pdWidth = 600;
                var pdRight = ($(window).width() - pdWidth) / 2;
                popup.dialog({
                    width: pdWidth,
                    resizable: false,
                    position: [pdRight, 106],
                    close: function(){
                        setFacility();
                    }
                });
            });
        	/*-
        	TODO: reimplement "scrollTo"
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
        	-*/
        	$.each(facilityData.list, function(i, fdp){
        	    olStyling.markIcon(fdp, facility===fdp ? 'showing' : 'hidden');
        	});
        } else {
            //unselect facility
            $.each(facilityData.list, function(i, fdp){
                if(selectedSector=="all" || fdp.sectorSlug === __sector) {
                    olStyling.markIcon(fdp, 'showing');
                } else {
                    olStyling.markIcon(fdp, 'hidden');
                }
        	});
            $('tr.selected-facility').removeClass('selected-facility');
        }
    }
    // END SETTER: facility
})();

function getTabulations(sector, col, keysArray) {
	var sList = facilityData.bySector[sector];
	var valueCounts = {};
	// if we specify a "keysArray", then the returned valueCounts will include zero values
	// for those keys.
	if(keysArray!==undefined) { $.each(keysArray, function(i, val){valueCounts[val]=0;}) }
	$(sList).each(function(i, id){
	    var fac = facilityData.list[id];
		var val = fac[col];
		if(val === undefined) {val = 'undefined'}
	    if(valueCounts[val] === undefined) { valueCounts[val] = 0; }
		valueCounts[val]++;
	});
	return valueCounts;
}

(function(){
    var _selectedColumn;

    window.unsetColumn = function(){
        $('.selected-column').removeClass('selected-column');
        selectedColumn = undefined;
    	getColDataDiv().empty().css({'height':0});
    }
    window.setColumn = function(sector, column){
        var wrapElement = $('#lga-widget-wrap');
        if(_selectedColumn !== column) {
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
    		var hasPieChart = hasClickAction(column, 'piechart_truefalse');
        	if(hasClickAction(column, 'tabulate') || hasPieChart) {
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
                    var cdd = getColDataDiv()
                            .html(Mustache.to_html(this.template, data))
                            .css({'height':110});

                    if(hasClickAction(column, 'piechart_truefalse')) {
                        log(cdd);
            		    var pcWrap = cdd.find('.content').eq(0)
            		        .attr('id', 'pie-chart')
            		        .empty();
                        log(pcWrap);
            		    var pieChartDisplayDefinitions = [
                            {'legend':'No', 'color':'#ff5555', 'key': 'false'},
                            {'legend':'Yes','color':'#21c406','key': 'true'},
                            {'legend':'Undefined','color':'#999','key': 'undefined'}];

            		    createOurGraph(pcWrap,
            		                    pieChartDisplayDefinitions,
            		                    getTabulations(sector.slug, column.slug, 'true false undefined'.split(' ')),
            		                    {});

                        var cdiv = $("<div />", {'class':'col-info'}).html($("<h2 />").text(column.name));
            			if(column.description!==undefined) {
            				cdiv.append($("<h3 />", {'class':'description'}).text(column.description));
            			}
                    }
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
    		_selectedColumn = column;
        }
    }
})();
// END page mode binders

// BEGIN facility table builder
//   -- facility table builder receives the facility data
//      and builds a table for each sector. The rows of the
//      table correspond to the facilities.
var filterPointsBySector;
var FACILITY_TABLE_BUILT = false;

function setSummaryHtml(html) {
    return $('.summary-p').html(html);
}

function buildFacilityTable(outerWrap, data, sectors, lgaData){
    function _buildOverview(){
        var div = $('<div />');
        getMustacheTemplate('lga_overview', function(){
            var sectors = [];
            var varsBySector = {};
            $.each(overviewVariables, function(i, variable){
                if(variable.sector!==undefined) {
                    if(varsBySector[variable.sector]==undefined) {varsBySector[variable.sector] = [];}
                    variable.value = displayValue(lgaData.profileData[variable.slug]);
                    if(!!variable.in_overview) {
                        varsBySector[variable.sector].push(variable);
                    }
                }
            });
            $.each(varsBySector, function(sectorSlug, variables){
                sectors.push({
                    name: sectorSlug,
                    slug: sectorSlug,
                    variables: variables
                });
            });
            var overviewTabs = Mustache.to_html(this.template, {
                sectors: sectors
            });
            div.append($(overviewTabs).tabs());
        });
        return div;
    }
    function _buildSectorOverview(s){
        var div = $('<div />');
        getMustacheTemplate('lga_sector_overview', function(){
            var data = {
                variables: []
            };
            $.each(overviewVariables, function(i, variable){
                if(!variable.in_overview && !!variable.in_sector && variable.sector == s) {
                    data.variables.push({
                        name: variable.name,
                        value: displayValue(lgaData.profileData[variable.slug])
                    });
                }
            });
            var overviewTabs = Mustache.to_html(this.template, data);
            div.append(overviewTabs);
        });
        return div;
    }
    
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
	$('<div />', {'id': 'toggle-updown-bar'}).html($('<span />', {'class':'icon'}))
	    .appendTo(outerWrap)
	    .click(function(){ outerWrap.toggleClass('closed'); });
	var lgaContent = $('<div />')
	        .addClass('lga-widget-content')
	        .appendTo(outerWrap);
	var ftabs = lgaContent;
	$.each(facilitySectors, function(i, sector){
	    createTableForSectorWithData(sector, facilityData)
	        .addClass('modeswitch') //possibly redundant.
	        .appendTo(ftabs);
	    
	    $('<div />')
	        .addClass('mode-lga')
	        .addClass('modeswitch')
	        .html(_buildSectorOverview(sector.slug))
	        .addClass('sector-'+sector.slug)
    	    .data('sectorSlug', sector.slug)
    	    .data('viewModeSlug', 'facility')
    	    .appendTo(ftabs);
	});
	$('<div />')
	    .addClass('modeswitch')
	    .addClass('mode-facility')
	    .addClass('sector-overview')
	    .text('THIS IS THE OVERVIEW at the FACILITY LEVEL')
	    .data('sectorSlug', 'overview')
	    .data('viewModeSlug', 'facility')
	    .appendTo(ftabs);
	$('<div />')
	    .addClass('modeswitch')
	    .addClass('mode-lga')
	    .addClass('sector-overview')
	    .html(_buildOverview())
	    .data('sectorSlug', 'overview')
	    .data('viewModeSlug', 'lga')
	    .appendTo(ftabs);
	ftabs.height(220);
	ftabs.find('.ui-tabs-panel').css({'overflow':'auto','height':'75%'});
	lgaContent.addClass('ready');
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
function displayValue(val) {
    if($.type(val)==='boolean') {
        return val ? 'Yes' : 'No'
    }
    return roundDownValueIfNumber(val);
}
function roundDownValueIfNumber(val) {
    if(val===undefined) { return 'n/a'; }
    if($.type(val)==='object') {val = val.value;}
    if($.type(val)==='number' && (''+val).length>5) {
        return Math.floor(Math.pow(10, decimalCount)* val)/Math.pow(10, decimalCount);
    } else if($.type(val)==='string') {
        return splitAndCapitalizeString(val);
//    } else if($.type(val)==='boolean') {
//        return val ? 'Yes' : 'No';
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
//		            setSector(sector.slug);
// TODO: implement select column
		            setColumn(sector, col);
		        })
		        .appendTo(thRow);

		$.extend(col, { th: th, thIndex: i+1 });
	});

	var tbod = $("<tbody />");
	$.each(sectorData, function(i, fUid){
		tbod.append(createRowForFacilityWithColumns(data.list[fUid], sector.columns, i+1))
	});
	function defaultSubSector(sector) {
	    if(sector.subgroups instanceof Array
	            && sector.subgroups.length > 0) {
    	    return sector.subgroups[0].slug;
	    }
	    return 'general';
	}
	function subSectorLink(ssName, subSectorSlug) {
	    var fullSectorSlug = sector.slug + subSectorDelimiter + subSectorSlug;
	    return $('<a />', {'href': '#', 'class': 'subsector-link-'+subSectorSlug})
	                .text(ssName)
	                .click(function(evt){
	                    setSector(sector.slug, subSectorSlug);
	                    evt.preventDefault();
	                });
	}
	var subSectors = (function(subSectors, splitter){
	    $.each(sector.subgroups, function(i, sg){
	        i !== 0 && subSectors.append(splitter.clone());
	        subSectors.append(subSectorLink(sg.name, sg.slug));
    	});
    	return subSectors;
	})($('<div />', {'class': 'sub-sector-list no-select'}), $("<span />").text(" | "));

    var table = $('<table />')
                    .addClass('facility-list')
                    .append($('<thead />').html(thRow))
                    .append(tbod);
    return $('<div />')
//	    .addClass('facility-list-wrap')
	    .addClass('modeswitch')
	    .addClass('mode-facility')
	    .addClass('sector-'+sector.slug)
	    .data('sectorSlug', sector.slug)
	    .append(subSectors)
	    .append(table);
}

function createRowForFacilityWithColumns(fpoint, cols, rowNum){
    //creates a row for the facility table. (only used in "createTableForSectorWithData")
	var tr = $("<tr />")
	        .data('facility-uid', fpoint.uid)
	        .click(function(){
	            //clicking a row triggers global event 'select-facility'
	            setFacility(fpoint.uid);
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
	    overviewVariables = dataReq[2].processedData.overview;
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
		overviewVariables = passedData.overview;
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
