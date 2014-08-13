// STRINGS
var _rebuildHexLegend__p_str = gettext('Proportion of surveys with response(s): ');
var getBootstrapFields__str = gettext("ERROR: constants not found; please include main/static/js/formManagers.js");
var JSONSurveyToHTML__q_str = gettext("Question");
var JSONSurveyToHTML__r_str = gettext("Response");
var hideZeroedValues_str = gettext("Hide options without data");
var displayZeroedValues_str = gettext("Display options without data");

// Global toggle on whether to display question values which have 0 submissions
var displayZeroedValues = false;

var centerLatLng = new L.LatLng(0, 0);
var defaultZoom = 3;
var mapId = 'map_canvas';
var map;
var layersControl;
var languageBasedLayers = {
  fr: {label: "Mapbox Streets (Français)", url: 'http://a.tiles.mapbox.com/v3/modilabs.map-vdpjhtgz.json'},
  es: {label: "Mapbox Streets (Español)", url: 'http://a.tiles.mapbox.com/v3/modilabs.map-5gjzjlah.json'}
};
// array of mapbox maps to use as base layers - the first one will be the default map unless a langauge is specified, in which case that languages, map will be the default
var mapboxMaps = [
    {label: gettext('Mapbox Streets'), url: 'http://a.tiles.mapbox.com/v3/modilabs.map-iuetkf9u.json'},
    {label: gettext('MapBox Streets Light'), url: 'http://a.tiles.mapbox.com/v3/modilabs.map-p543gvbh.json'},
    {label: gettext('MapBox Streets Zenburn'), url: 'http://a.tiles.mapbox.com/v3/modilabs.map-bjhr55gf.json'},
    {label: gettext('Cloudless Earth'), url: 'http://a.tiles.mapbox.com/v3/modilabs.map-aef58tqo.json'}
];
var sslUrlPerfix = 'https://dnv9my2eseobd.cloudfront.net/'; // add trailing slash since its expected function that uses this
var allowResetZoomLevel = true; // used to allow zooming when first loaded
var popupOffset = new L.Point(0, -10);
var notSpecifiedCaption = gettext("Not Specified");
var colorPalette = ['#8DD3C7', '#FB8072', '#FFFFB3', '#BEBADA', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5', '#D9D9D9',
    '#BC80BD', '#CCEBC5', '#FFED6F'];
var circleStyle = {
    color: '#fff',
    border: 8,
    fillColor: '#ff3300',
    fillOpacity: 0.9,
    radius: 8,
    opacity: 0.5
};
// TODO: can we get the entire URL from mongo API
var amazonUrlPrefix = "https://formhub.s3.amazonaws.com/";
var markerLayerGroup = new L.LayerGroup();
var markerLayerGroupActive = false;
var hexbinLayerGroupActive = false;
var hexbinLayerGroup = new L.LayerGroup();
var hexbinData = null;
var markerLayerLabel = gettext("Marker Layer");
var hexbinLayerLabel = "Hexbin Layer";
// TODO: generate new api key for formhub at https://www.bingmapsportal.com/application/index/1121012?status=NoStatus
var bingAPIKey = 'AtyTytHaexsLBZRFM6xu9DGevbYyVPykavcwVWG6wk24jYiEO9JJSmZmLuekkywR';
var bingMapTypeLabels = {'AerialWithLabels': gettext('Bing Satellite Map'), 'Road': gettext('Bing Road Map')}; //Road, Aerial or AerialWithLabels
var mapBoxAdditAttribution = gettext(" Map data (c) OpenStreetMap contributors, CC-BY-SA");

// map filter vars
var navContainerSelector = ".nav.pull-right";
var leafletControlSelector = ".leaflet-control-container";
var legendContainerId = "legend";
var formJSONMngr = new FormJSONManager(formJSONUrl, loadFormJSONCallback);
var formResponseMngr = new FormResponseManager(mongoAPIUrl, loadResponseDataCallback);
var currentLanguageIdx = -1;
var customMapBoxTileLayer;
var legendsContainer;

var mapview = function() {
    return {
        isHttps: function(){
            return location.protocol == 'https:';
        }
    };
}();

/**
 *  for a url http://a.tiles.mapbox.com/v3/modilabs.map-iuetkf9u/{z}/{x}/{y}.png
 *  return v3/modilabs.map-iuetkf9u/{z}/{x}/{y}.png,
 *  is a regex that strips gets everything after the domain name
 */
mapview.getMapboxMapname = function(mapUrl) {
    var matches = mapUrl.match(/(^.+?\..+?\/)(.+)/);
    if(matches.length > 0)
    {
        return matches[2];
    }
    return null;
};

function initialize() {
    // Make a new Leaflet map in your container div
    map = new L.Map(mapId).setView(centerLatLng, defaultZoom);

    map.on('layeradd', function(layerEvent){
        if(layerEvent.layer == hexbinLayerGroup)
        {
            hexbinLayerAdded(layerEvent.layer);
        }
        else if(layerEvent.layer == markerLayerGroup)
        {
            markerLayerAdded(layerEvent.layer);
        }
    });

    map.on('layerremove', function(layerEvent){
        if(layerEvent.layer == hexbinLayerGroup)
        {
            hexbinLayerRemoved(layerEvent.layer);
        }
        else if(layerEvent.layer == markerLayerGroup)
        {
            markerLayerRemoved(layerEvent.layer);
        }
    });

    var hexButton = function () {
        if(!map.hasLayer(hexbinLayerGroup)) {
            $('div.layer-hexbinButton').toggleClass('layer-hexbinButton-active');
            return map.addLayer(hexbinLayerGroup);
        }
        else if (map.hasLayer(hexbinLayerGroup)) {
            $('div.layer-hexbinButton').toggleClass('layer-hexbinButton-active');
            return map.removeLayer(hexbinLayerGroup);
        }
    };

    var markerButton = function () {
        if(!map.hasLayer(markerLayerGroup)) {
            $('div.layer-markerButton').toggleClass('layer-markerButton-active');
            return map.addLayer(markerLayerGroup);
        }
        else{
            $('div.layer-markerButton').toggleClass('layer-markerButton-active');
            return map.removeLayer(markerLayerGroup);
        }
    };

    map.addControl(layerButtonControl(markerButton, hexButton));
    layersControl = new L.Control.Layers();
    map.addControl(layersControl);

    //show marker layer by default
    map.addLayer(markerLayerGroup);
    $('div.layer-markerButton').addClass('layer-markerButton-active');

    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    var drawControl = new L.Control.Draw({
        draw: {
            polyline: false,
            polygon: false,
            rectangle: false,
            circle: false,
            marker: {
                title: "Add a submission on a specific location"
            }
        },
        edit: {
            featureGroup: drawnItems,
            remove: false,
            edit: false
        }
    });
    map.addControl(drawControl);

    map.on('draw:created', function (e) {
        var type = e.layerType,
            layer = e.layer;

        if (type === 'marker') {
            // fire the modal
            var url = getAddUrl(e.layer._latlng);
            displayEnketoModal(url, true);
        }

        // keep the icon on the map.
        map.addLayer(layer);
    });

    // // add bing maps layer
    // * $.each(bingMapTypeLabels, function(type, label) {
    //     var bingLayer = new L.TileLayer.Bing(bingAPIKey, type);
    //     layersControl.addBaseLayer(bingLayer, label);
    // });

    // add google sat layer
    var ggl = new L.Google('HYBRID');
    layersControl.addBaseLayer(ggl, gettext("Google Satellite Map"));

    // Get metadata about the map from MapBox
    var tileJSONAddFn = function(mapData, addToMap) {
        var innerFn = function(tilejson) {
            var tileLayer, mapName;

            tilejson.attribution = tilejson.attribution?tilejson.attribution +
                mapBoxAdditAttribution:mapBoxAdditAttribution;
            // check if https and change tile array appropriately
            if(mapview.isHttps())
            {
                /// get map url
                mapName = mapview.getMapboxMapname(tilejson.tiles[0]);
                /// replace our tile url with this
                tilejson.tiles = [sslUrlPerfix + mapName];
            }
            // Changed this to mapbox.tileLayer since it doesn't
            // seem to work on Leaflet 0.6.2.
            // tileLayer = new wax.leaf.connector(tilejson);
            tileLayer = L.mapbox.tileLayer(mapData.url);

            layersControl.addBaseLayer(tileLayer, mapData.label);
            if(addToMap) {
                map.addLayer(tileLayer);
                // and radio box for this layer (last = just added)
                $('input[name=leaflet-base-layers]:last').attr('checked',true);
            }
        };
        return innerFn;
    };
    var defaultMap;
    // add langauge based maps
    _.each(languageBasedLayers, function(mapData, language){
      mapboxMaps.push(mapData);
      if(language_code === language)
      {
        defaultMap = mapData;
      }
    });
    if (customMapBoxTileLayer) {
        mapboxMaps = _.union([customMapBoxTileLayer], mapboxMaps);
        defaultMap = customMapBoxTileLayer;
    }
    if(defaultMap === undefined)
    {
      defaultMap = mapboxMaps[0];
    }
    _.each(mapboxMaps, function(mapData, idx) {
        // if https,
        if(mapview.isHttps())
        {
            // change to ssl url
            mapData.url = sslUrlPerfix + mapview.getMapboxMapname(mapData.url);
        }
        wax.tilejson(mapData.url, tileJSONAddFn(mapData, defaultMap == mapData)); //ie, only add the default
    });

    // create legend container
    $(leafletControlSelector).append('<div class="legends-container"></div>');
    legendsContainer = $($(leafletControlSelector).children('div.legends-container')[0]);

    // load form structure/questions
    formJSONMngr.loadFormJSON();
}

function hexbinLayerAdded(layer)
{
    var elm = $('#hex-legend');
    hexbinLayerGroupActive = true;
    if(elm.length > 0)
        elm.show();
    refreshHexOverLay();
}

function hexbinLayerRemoved(layer)
{
    var elm = $('#hex-legend');
    hexbinLayerGroupActive = false;
    if(elm.length > 0)
        elm.hide();
}

function markerLayerAdded(layer)
{
    var elm = $('#legend');
    markerLayerGroupActive = true;
    if(elm.length > 0)
        elm.show();
}

function markerLayerRemoved(layer)
{
    var elm = $('#legend');
    markerLayerGroupActive = false;
    if(elm.length > 0)
        elm.hide();
}

// callback called after form's structure has been loaded from form json url
function loadFormJSONCallback()
{
    // we only want to load gps and select one data to begin with
    var fields = getBootstrapFields();
    var geoField = formJSONMngr.getGeoPointQuestion()[constants.NAME];

    // load responses
    formResponseMngr.loadResponseData({}, 0, null, geoField, fields);
}

// update the number of geo-coded submissions in the top-bar based on geoJSON
function _updateGeoCodedCount(geoJSON) {
   var geoCount = geoJSON.features.length;
   var countDiv = $('#submission_count');
   var newText = geoCount + " / " + countDiv.text();
   var newTitle = _.template(countDiv.attr('title'),
   	{geocoded_submission_count: geoCount})
   countDiv.attr('title', newTitle);
   countDiv.text(newText);
}

// callback called after response data has been loaded via the mongo form API
function loadResponseDataCallback()
{
    formResponseMngr.callback = null;// initial callback is for setup, subsequent reloads must set desired callback
    var dropdownLabel, dropdownLink, dropDownContainer, dropDownCaret, dropDownCaretLink, idx;

    // get geoJSON data to setup points - relies on questions having been parsed
    var geoJSON = formResponseMngr.getAsGeoJSON();

    _buildMarkerLayer(geoJSON);
    _updateGeoCodedCount(geoJSON);

    // just to make sure the nav container exists
    var navContainer = $(navContainerSelector);
    if(navContainer.length == 1)
    {
        // add language selector
        if(formJSONMngr.supportedLanguages.length > 1)
        {
            $('<li />').html(
                $('<a />', { text: gettext("Language"), href: '#'}).addClass("language-label")
            ).appendTo(navContainer);

            dropDownContainer = _createElementAndSetAttrs('li', {"class":"dropdown language-picker"});
            dropdownCaretLink = _createElementAndSetAttrs('a', {"href":"#", "class":"dropdown-toggle",
                "data-toggle":"dropdown"});
            dropdownCaret = _createElementAndSetAttrs('b', {"class":"caret"});
            dropdownCaretLink.appendChild(dropdownCaret);
            dropDownContainer.appendChild(dropdownCaretLink);

            var languageUlContainer = _createElementAndSetAttrs("ul", {"class":"dropdown-menu"});

            // create links for select one questions
            selectOneQuestions = formJSONMngr.getSelectOneQuestions();
            for(idx in formJSONMngr.supportedLanguages)
            {
                var language = getLanguageAt(idx);
                var languageAnchor = _createElementAndSetAttrs('a', {"class":"language", "data":idx.toString()}, language);
                var languageLi = _createElementAndSetAttrs('li');
                languageLi.appendChild(languageAnchor);
                languageUlContainer.appendChild(languageLi);
            }
            dropDownContainer.appendChild(languageUlContainer);

            navContainer.append(dropDownContainer);

            // attach callbacks
            $('.language-picker a.language').click(function(){
                var languageIdx = parseInt($(this).attr('data'), 10);
                setLanguage(languageIdx);
            });

            // set default language
            setLanguage(0);
        } else {
            currentLanguageIdx = 0;// needed for non-multilingual forms
        }

        // check if we have select one questions
        if(formJSONMngr.getNumSelectOneQuestions() > 0)
        {
            $('<li />').html(
                $('<a />', { text: gettext("View By"), href: '#'})
            ).appendTo(navContainer);

            dropDownContainer = _createElementAndSetAttrs('li', {"class":"dropdown"});
            dropdownCaretLink = _createElementAndSetAttrs('a', {"href":"#", "class":"dropdown-toggle",
                "data-toggle":"dropdown"});
            dropdownCaret = _createElementAndSetAttrs('b', {"class":"caret"});
            dropdownCaretLink.appendChild(dropdownCaret);
            dropDownContainer.appendChild(dropdownCaretLink);

            var questionUlContainer = _createElementAndSetAttrs("ul", {"class":"dropdown-menu questions"});

            // create an "All" link to reset the map
            var questionLi = _createSelectOneLi({"name":"", "label": gettext("None")});
            questionUlContainer.appendChild(questionLi);

            // create links for select one questions
            selectOneQuestions = formJSONMngr.getSelectOneQuestions();
            for(idx in selectOneQuestions)
            {
                var question = selectOneQuestions[idx];
                questionLi = _createSelectOneLi(question);
                questionUlContainer.appendChild(questionLi);
            }
            dropDownContainer.appendChild(questionUlContainer);

            navContainer.append(dropDownContainer);
            /*$('.select-one-anchor').click(function(){
             // rel contains the question's unique name
             var questionName = $(this).attr("rel");
             viewByChanged(questionName);
             })*/
        }
    }
    else
        throw interpolate(gettext("Container %(cont)s not found"), {cont: navContainerSelector}, true);

    // Bind a callback that executes when document.location.hash changes.
    $(window).bind( "hashchange", function(e) {
        var hash = e.fragment;
        viewByChanged(hash);
    });

    // Since the event is only triggered when the hash changes, we need
    // to trigger the event now, to handle the hash the page may have
    // loaded with.
    $(window).trigger( "hashchange" );
}

function setLanguage(idx)
{
    if(idx != currentLanguageIdx)
    {
        var newLanguage = getLanguageAt(idx);
        $('a.language-label').html(newLanguage);
        currentLanguageIdx = idx;
        /// hide all language spans
        $('span.language').hide();
        $(('span.language-'+idx)).show();
    }
}

function _buildMarkerLayer(geoJSON)
{
    var latLngArray = [];

    L.geoJson(geoJSON, {
        pointToLayer: function(feature, latlng) {
            var marker = L.circleMarker(latlng, circleStyle);
            latLngArray.push(latlng);
            marker.on('click', function(e) {

                displayDataModal(feature.id);

                // var popup = L.popup({offset: popupOffset})
                //     .setContent("Loading...").setLatLng(latlng).openOn(map);
                // $.getJSON(mongoAPIUrl, {'query': '{"_id":' + feature.id + '}'})
                //     .done(function(data){
                //         var content;
                //         if(data.length > 0)
                //             content = JSONSurveyToHTML(data[0]);
                //         else
                //             content = "An unexpected error occurred";
                //         popup.setContent(content);

                //         // click on the Edit button
                //         $('button.edit-submission').click(function () {
                //             var data_id = $(this).data('id');
                //             var url = enketoEditUrl + data_id;
                //             displayEnketoModal(url);
                //         });
                //     });
            });
            return marker;
        }
    }).addTo(markerLayerGroup);

    _.defer(refreshHexOverLay); // TODO: add a toggle to do this only if hexOn = true;

    // fitting to bounds with one point will zoom too far
    // don't zoom when we "view by response"
    var latlngbounds = new L.LatLngBounds(latLngArray);
    map.fitBounds(latlngbounds);
}

function _recolorMarkerLayer(questionName, responseFilterList)
{
    var latLngArray = [];
    var questionColorMap = {};
    var randomColorStep = 0;
    var paletteCounter = 0;
    var responseCountValid = false;

    if(questionName)
    {
        var question = formJSONMngr.getQuestionByName(questionName);

        // figure out the response counts
        var dvCounts = formResponseMngr.dvQuery({dims:[questionName], vals:[dv.count()]});
        var responseCounts = _.object(dvCounts[0], dvCounts[1]);
        responseCounts[notSpecifiedCaption] = responseCounts[undefined]; //undefined = special case
        // and make sure every response has a count
        var choiceNames = _.union(_.pluck(question.children, 'name'), [notSpecifiedCaption]);
        var zeroCounts = _.object(_.map(choiceNames, function(choice) { return [choice, 0]; }));
        question.responseCounts = _.defaults(responseCounts, zeroCounts);

        // TODO: put the following for loop in the colors module
        for(i=0;i < choiceNames.length;i++)
        {
            var choiceName = choiceNames[i];
            var choiceColor = null;
            // check if color palette has colors we haven't used
            if(paletteCounter < colorPalette.length)
                choiceColor = colorPalette[paletteCounter++];
            else
            {
                // number of steps is reduced by the number of colors in our palette
                choiceColor = get_random_color(randomColorStep++, (choiceNames.length - colorPalette.length));
            }
            /// save color for this choice
            questionColorMap[choiceName] = choiceColor;
        }

        // re-color the icons
        markerLayerGroup.eachLayer(function(geoJSONLayer) {
            geoJSONLayer.setStyle(function(feature) {
                var response = feature.properties[questionName] || notSpecifiedCaption;

                if (responseFilterList.length > 0 && _.indexOf(responseFilterList, response) === -1) {
                    return _.defaults({fillOpacity: 0, opacity:0}, circleStyle);
                } else {
                    return _.defaults({fillColor: questionColorMap[response]}, circleStyle);
                }
            });
        });

        // build the legend
        rebuildLegend(questionName, questionColorMap);
    } else {
        markerLayerGroup.eachLayer(function(geoJSONLayer) {
            geoJSONLayer.setStyle(circleStyle);
        });
        clearLegend();
    }
    _.defer(refreshHexOverLay); // TODO: add a toggle to do this only if hexOn = true;
}

function _reStyleAndBindPopupsToHexOverLay(newHexStylesByID, newHexPopupsByID) {
    _(hexbinLayerGroup._layers).each(function(hexbinLPolygon) {
        hexID = hexbinLPolygon.options.id;
        if (newHexStylesByID[hexID])
            hexbinLPolygon.setStyle(newHexStylesByID[hexID]);
        if (newHexPopupsByID[hexID])
            hexbinLPolygon.bindPopup(newHexPopupsByID[hexID], {offset: L.point(20,0)});
    });
}

function constructHexBinOverLay() {
    hexbinData = formResponseMngr.getAsHexbinGeoJSON();
    var arr_to_latlng = function(arr) { return new L.LatLng(arr[0], arr[1]); };
    var hex_feature_to_polygon_fn = function(el) {
        return new L.Polygon(_(el.geometry.coordinates).map(arr_to_latlng),
            {"id": el.properties.id});
    };
    var lazyClose = _.debounce(function() {map.closePopup();}, 3000);
    _(hexbinData.features).each( function(x, idx) {
        var hexLayer = hex_feature_to_polygon_fn(x);
        var lazyPopup = _.debounce(
            function() {
                hexLayer.openPopup();
                lazyClose();
            }, 1500, true);
        hexLayer.on('mouseover', lazyPopup);
        hexbinLayerGroup.addLayer(hexLayer);
    });
}



function _recomputeHexColorsByRatio(questionName, responseNames) {
    var newHexStyles = {};
    var newPopupTexts = {};
    var myResponseNames = _.clone(responseNames);
    if (_(myResponseNames).contains(notSpecifiedCaption))
        myResponseNames.push(undefined); // hack? if notSpeciedCaption is in repsonseNames, then need to
    // count when instance.response[questionName] doesn't exist, and is therefore ``undefined''

    var hexAndCountArrayNum = formResponseMngr.dvQuery({dims: ['hexID'], vals:[dv.count()], where:
        function(table, row) { return _.contains(myResponseNames, table.get(questionName, row)); }});
    var hexAndCountArrayDenom = formResponseMngr.dvQuery({dims:['hexID'], vals:[dv.count()]});

    _(hexAndCountArrayDenom[0]).each( function(hexID, idx) {
        // note both are dense queries on datavore, the idx's match exactly
        var ratio = hexAndCountArrayNum[1][idx] / hexAndCountArrayDenom[1][idx];
        newHexStyles[hexID] = {  fillColor: colors.getProportional(ratio, "Set2"), fillOpacity: 0.9, color:'grey', weight: 1 };
        newPopupTexts[hexID] = hexAndCountArrayNum[1][idx] + " / " + hexAndCountArrayDenom[1][idx] + " (" + Math.round(ratio*100) + "%)";
    });
    _reStyleAndBindPopupsToHexOverLay(newHexStyles, newPopupTexts);
    _rebuildHexLegend('proportion', questionName, myResponseNames);
}

function _hexOverLayByCount()
{
    var newHexStyles = {};
    var newPopupTexts = {};
    var hexAndCountArray = formResponseMngr.dvQuery({dims:['hexID'], vals:[dv.count()]});
    var totalCount = _.max(hexAndCountArray[1]);
    _(hexAndCountArray[0]).each( function(hexID, idx) {
        var color = colors.getProportional(hexAndCountArray[1][idx] / totalCount);
        newHexStyles[hexID] = {fillColor: color, fillOpacity: 0.9, color:'grey', weight: 1};
        newPopupTexts[hexID] = hexAndCountArray[1][idx] + " submissions.";

    });
    _reStyleAndBindPopupsToHexOverLay(newHexStyles, newPopupTexts);
    _rebuildHexLegend('count');
}

function refreshHexOverLay() { // refresh hex overlay, in any map state
    // IF we have already calculated hex bin data, and have a filtration active, recomputer colors;
    if (!hexbinData) constructHexBinOverLay();
    if (formResponseMngr._currentSelectOneQuestionName && formResponseMngr._select_one_filters.length)
        _recomputeHexColorsByRatio(formResponseMngr._currentSelectOneQuestionName,
            formResponseMngr._select_one_filters);
    else
        _hexOverLayByCount();
}

function removeHexOverLay()
{
    hexbinLayerGroup.clearLayers();
}

function toggleHexOverLay()
{
    if(map.hasLayer(hexbinLayerGroup)) removeHexOverLay();
    else refreshHexOverLay();
}

/*
 * Format the json data to HTML for a map popup
 */
function JSONSurveyToHTML(data)
{
    var idx, dummyContainer, questionName, span;
    var htmlContent = '<div class="inner-modal"><ul><li><button class="edit-submission btn" data-id="' + data._id + '">Edit Submission Data</button></li>';
    htmlContent += '<li><button class="del-submission btn btn-danger" data-id="' + data._id + '">Delete Submission</button></li></ul>';
    htmlContent += '<table class="table table-bordered table-striped"> <thead>\n<tr>\n<th>' + JSONSurveyToHTML__q_str + '</th>\n<th>' + JSONSurveyToHTML__r_str + '</th>\n</tr>\n</thead>\n<tbody>\n';

    // add images if any
    // TODO: this assumes all attachments are images
    if(data._attachments && data._attachments.length > 0)
    {
        var mediaContainer = '<ul class="media-grid">';
        for(idx in data._attachments)
        {
            var attachmentUrl = data._attachments[idx];
            var imgSrc = attachmentsBaseUrl + '?media_file=' + encodeURIComponent(attachmentUrl);
            mediaContainer += '<li><a href="'+imgSrc+'" target="_blank">';
            var imgTag = _createElementAndSetAttrs('img', {"class":"thumbnail", "width":"210", "src": imgSrc});
            dummyContainer = _createElementAndSetAttrs('div', {});
            dummyContainer.appendChild(imgTag);
            mediaContainer += dummyContainer.innerHTML;
            mediaContainer += '</a></li>';

        }
        mediaContainer += '</ul>';
        htmlContent += mediaContainer;
    }

    for(questionName in formJSONMngr.questions)
    {
        if(data[questionName])
        {
            var question  = formJSONMngr.getQuestionByName(questionName);
            var response = _createElementAndSetAttrs('tr', {});
            var td = _createElementAndSetAttrs('td', {});

            for(idx in formJSONMngr.supportedLanguages)
            {
                var language = getLanguageAt(idx);
                var style = "";
                if(idx != currentLanguageIdx)
                {
                    style = "display: none";
                }
                span = _createElementAndSetAttrs('span', {"class": ("language language-" + idx), "style": style}, formJSONMngr.getMultilingualLabel(question, language));
                td.appendChild(span);
            }
            response.appendChild(td);

            if(formJSONMngr.getTypeOfQuestion(questionName) === 'repeat') {
                var repeatList = data[questionName];
                td = $('<td></td>').appendTo(response);
                _.each(repeatList, function (repeatEl, idx) {
                    var thisID = questionName.replace(/\//g,'-') + "-" + idx;
                    var collapseButton = $('<a>Child ' + (idx+1) + '</a>') // 1-indexed
                                         .addClass('btn')
                                         .attr('id', 'collapse-' + thisID)
                                         .appendTo(td);
                    var collapseDiv = $('<div></div>')
                                          .attr('id', thisID)
                                          .hide()
                                          .appendTo(td);
                    var table = $(JSONSurveyToHTML(repeatEl)).appendTo(collapseDiv);
                    $('.leaflet-popup-content')
                        .on('click',
                            '#collapse-' + thisID,
                            function() {$('#' + thisID).toggle();}
                        );
                });
            } else {
                td = _createElementAndSetAttrs('td', {}, data[questionName]);
                response.appendChild(td);
            }
            dummyContainer = _createElementAndSetAttrs('div', {});
            dummyContainer.appendChild(response);
            htmlContent += dummyContainer.innerHTML;
        }
    }
    htmlContent += '</tbody></table></div>';
    return htmlContent;
}

function getLanguageAt(idx)
{
    return formJSONMngr.supportedLanguages[idx];
}

function _rebuildHexLegend(countOrProportion, questionName, responseNames)
{

    var legendTemplate =
        '<div id="hex-legend" style="display:block">\n' +
            '  <h4><%= title %> </h4>\n' +
            '  <div class="scale">\n' +
            '  <ul class="labels">\n' +
            '<% _.each(hexes, function(hex) { %>' +
            '    <li> <span style="background-color: <%= hex.color %>" />' +
            '         <%= hex.text %> </li>\n<% }); %>' +
            '  </div>\n  </ul>\n<div style="clear:both"></div>\n</div>';

    var proportionString = _rebuildHexLegend__p_str +
        (responseNames && (responseNames.length == 1 ? responseNames[0] :
            _.reduce(responseNames,
                function(a,b) { return (a && a + ", or ") + b; }, '')));
    var maxHexCount = _.max(formResponseMngr.dvQuery({dims:['hexID'], vals:[dv.count()]})[1]);
    var interval = function(scheme) {
        var len = colors.getNumProportional(scheme);
        return _.map(_.range(1,len+1), function (v) { return v / len; });
    };
    var templateFiller = {
        count: { title : gettext('Number of submissions'),
            hexes : _.map(interval("Set1"), function (i) {
                return  {color: colors.getProportional(i),
                    text: '<' + Math.ceil(i * maxHexCount)}; })
        },
        proportion: { title : proportionString,
            hexes : _.map(interval("Set2"), function (i) {
                return {color: colors.getProportional(i, "Set2"),
                    text: '<' + Math.ceil(i * 100) + '%'}; })
        }
    };
    $('#hex-legend').remove();
    $(_.template(legendTemplate, templateFiller[countOrProportion]))
        .appendTo(legendsContainer);
    if(!hexbinLayerGroupActive) $('#hex-legend').hide();
}

function rebuildLegend(questionName, questionColorMap)
{
    var i, response, spanAttrs, language;
    var question = formJSONMngr.getQuestionByName(questionName);
    var choices = formJSONMngr.getChoices(question);
    var legendElement, legendTitle, legendUl;
    formResponseMngr._currentSelectOneQuestionName = questionName; //TODO: this should be done somewhere else?

    $('#legend').remove();

    legendElement = $('<div></div>').attr('id', 'legend');
    legendTitle = $('<h3></h3>');

    for(i=0;i<formJSONMngr.supportedLanguages.length;i++)
    {
        var titleSpan;

        language = getLanguageAt(i);
        titleSpan = $('<span></span>').addClass('language').addClass('language-' + i)
            .html(formJSONMngr.getMultilingualLabel(question, language));
        if(i != currentLanguageIdx)
            titleSpan.css('display', 'none');
        legendTitle.append(titleSpan);
    }
    legendElement.append(legendTitle);

    legendUl = $('<ul></ul>').addClass('nav nav-pills nav-stacked');
    legendElement.append(legendUl);

    for(response in questionColorMap)
    {
        var color = questionColorMap[response];
        var responseLi = $('<li></li>');
        var numResponses = question.responseCounts[response];

        if (numResponses == 0 && !displayZeroedValues) {
            continue;
        }

        // create the anchor
        var legendAnchor = $('<a></a>').addClass('legend-label').attr('href', 'javascript:;').attr('rel',response);
        if(formResponseMngr._select_one_filters.indexOf(response) > -1)
            legendAnchor.addClass('active');
        else if(numResponses > 0)
            legendAnchor.addClass('normal');
        else
            legendAnchor.addClass('inactive');

        var legendIcon = $('<span></span>').addClass('legend-bullet').css('background-color', color);
        legendAnchor.append(legendIcon);

        var responseCountSpan = $('<span></span>').addClass('legend-response-count').html(numResponses.toString());
        legendAnchor.append(responseCountSpan);

        // add a language span for each language
        for(i=0;i<formJSONMngr.supportedLanguages.length;i++)
        {
            var itemLabel = response;
            language = getLanguageAt(i);
            // check if the choices contain this response before we try to get the reponse's label
            if(choices.hasOwnProperty(response))
                itemLabel = formJSONMngr.getMultilingualLabel(choices[response], language);
            var responseText = $('<span></span>').addClass(('item-label language language-' + i)).html(itemLabel);
            if(i != currentLanguageIdx)
                responseText.css('display', 'none');
            legendAnchor.append(responseText);
        }

        responseLi.append(legendAnchor);
        legendUl.append(responseLi);
    }

    var toggleZeroedValuesLi = $('<li />');
    var toggleZeroedValuesA = $('<a />');
    toggleZeroedValuesA.addClass('legend-label');
    toggleZeroedValuesA.addClass(displayZeroedValues ? 'active' : 'inactive');
    toggleZeroedValuesA.html(displayZeroedValues ? hideZeroedValues_str : displayZeroedValues_str);
    toggleZeroedValuesLi.append(toggleZeroedValuesA);
    legendUl.append(toggleZeroedValuesLi);
    toggleZeroedValuesA.click(function () {
        displayZeroedValues = !displayZeroedValues;
        rebuildLegend(questionName, questionColorMap);
    });


    // add as the first element always
    legendsContainer.prepend(legendElement);

    // bind legend click event
    $('a.legend-label').on('click', function(){
        var elm = $(this);
        var responseName = elm.attr('rel');
        // if element class is normal add response other wise, remove
        if(elm.hasClass('normal'))
            formResponseMngr.addResponseToSelectOneFilter(responseName);
        else
            formResponseMngr.removeResponseFromSelectOneFilter(responseName);
        _recolorMarkerLayer(formResponseMngr._currentSelectOneQuestionName, formResponseMngr._select_one_filters);
        refreshHexOverLay();
    });
}

/**
 * Get fields we deem nesseceary to display map/legend
 * TODO: cache bootstrap fields
 */
function getBootstrapFields()
{
    // we only want to load gps and select one data to begin with
    var fields = ['_id', constants.GEOLOCATION];
    var idx, question;
    if(!constants) throw getBootstrapFields__str;
    for(idx in formJSONMngr.selectOneQuestions)
    {
        question = formJSONMngr.selectOneQuestions[idx];
        fields.push(question[constants.NAME]);
    }

    return fields;
}

function clearLegend()
{
    $('#legend').remove();
}

function viewByChanged(questionName)
{
    allowResetZoomLevel = false; // disable zoom reset whenever this is clicked
    // update question name
    formResponseMngr.setCurrentSelectOneQuestionName(questionName);
    formResponseMngr.clearSelectOneFilterResponses();

    _recolorMarkerLayer(questionName, formResponseMngr._select_one_filters);
}

function _createSelectOneLi(question)
{
    var questionLi = _createElementAndSetAttrs("li", {}, "");
    var questionLink = _createElementAndSetAttrs("a", {"href":("#" + question.name), "class":"select-one-anchor",
        "rel": question.name});
    var i;
    for(i=0;i<formJSONMngr.supportedLanguages.length;i++)
    {
        var language = getLanguageAt(i);
        var questionLabel = formJSONMngr.getMultilingualLabel(question, language);
        var spanAttrs = {"class":("language language-" + i)};
        if(i != currentLanguageIdx)
            spanAttrs.style = "display:none";
        var languageSpan = _createElementAndSetAttrs("span", spanAttrs, questionLabel);
        questionLink.appendChild(languageSpan);
    }

    questionLi.appendChild(questionLink);
    return questionLi;
}

function _createElementAndSetAttrs(tag, attributes, text)
{
    var attr;
    var el = document.createElement(tag);
    for(attr in attributes)
    {
        el.setAttribute(attr, attributes[attr]);
    }

    if(text)
    {
        el.appendChild(document.createTextNode(text));
    }
    return el;
}

function get_random_color(step, numOfSteps) {
    // This function generates vibrant, "evenly spaced" colours (i.e. no clustering). This is ideal for creating easily distiguishable vibrant markers in Google Maps and other apps.
    // Adam Cole, 2011-Sept-14
    // HSV to RBG adapted from: http://mjijackson.com/2008/02/rgb-to-hsl-and-rgb-to-hsv-color-model-conversion-algorithms-in-javascript
    var r, g, b;
    var h = step / numOfSteps;
    var i = ~~(h * 6);
    var f = h * 6 - i;
    var q = 1 - f;
    switch(i % 6){
        case 0: r = 1, g = f, b = 0; break;
        case 1: r = q, g = 1, b = 0; break;
        case 2: r = 0, g = 1, b = f; break;
        case 3: r = 0, g = q, b = 1; break;
        case 4: r = f, g = 0, b = 1; break;
        case 5: r = 1, g = 0, b = q; break;
    }
    var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
    return (c);
}

// COLORS MODULE
var colors = (function() {
    var colors = {};
    var colorschemes = {proportional: {
        // http://colorbrewer2.org/index.php?type=sequential
        "Set1": ["#EFEDF5", "#DADAEB", "#BCBDDC", "#9E9AC8", "#807DBA", "#6A51A3", "#54278F", "#3F007D"],
        "Set2": ["#DEEBF7", "#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B"]
    }};
    var defaultColorScheme = "Set1";
    function select_from_colors(type, colorscheme, zero_to_one_inclusive) {
        var epsilon = 0.00001;
        colorscheme = colorscheme || defaultColorScheme;
        var colorsArr = colorschemes[type][colorscheme];
        return colorsArr[Math.floor(zero_to_one_inclusive * (colorsArr.length - epsilon))];
    }

    // METHODS FOR EXPORT
    colors.getNumProportional = function(colorscheme) {
        colorscheme = colorscheme || defaultColorScheme;
        return colorschemes.proportional[colorscheme].length;
    };
    colors.getProportional = function(zero_to_one, colorscheme) {
        return select_from_colors('proportional', colorscheme, zero_to_one);
    };

    return colors;
}());
