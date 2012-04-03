var centerLatLng = new L.LatLng(!center.lat?0.0:center.lat, !center.lng?0.0:center.lng);
var defaultZoom = 8;
var mapId = 'map_canvas';
var map;
var popupOffset = new L.Point(0, -10);
var circleStyle = {
    color: '#fff',
    border: 5,
    fillColor: '#cc3333',
    fillOpacity: 0.9,
    radius: 8
}
var geoJsonLayer = new L.GeoJSON(null);
// TODO: generate new api key for formhub at https://www.bingmapsportal.com/application/index/1121012?status=NoStatus
var bingAPIKey = 'AtyTytHaexsLBZRFM6xu9DGevbYyVPykavcwVWG6wk24jYiEO9JJSmZmLuekkywR';
var bingMapTypeLabels = {'AerialWithLabels': 'Bing Satellite Map', 'Road': 'Bing Road Map'}; //Road, Aerial or AerialWithLabels
var mapBoxAdditAttribution = " Map data (c) OpenStreetMap contributors, CC-BY-SA";

// TODO: Consider moving to a separate file
// used to load and manage form questions
FormJSONManager = function(url, callback)
{
    this.url = url;
    this.callback = callback;
    this.geopointQuestions = [];
}

FormJSONManager.prototype.loadFormJSON = function()
{
    var thisManager = this;
    $.getJSON(thisManager.url, function(data){
        thisManager._parseQuestions(data.children);
        thisManager.callback.call(thisManager);
    })
}

FormJSONManager.prototype._parseQuestions = function(questionData)
{
    this.selectOneQuestions = [];
    this.questions = {};
    for(idx in questionData)
    {
        var question = questionData[idx];
        this.questions[question.name] = question;
        if(question.type == "select one")
            this.selectOneQuestions.push(question);
        if(question.type == "geopoint")
            this.geopointQuestions.push(question)
    }
}

FormJSONManager.prototype.getNumSelectOneQuestions = function()
{
    if(!this.selectOneQuestions)
        this._parseQuestions();

    return this.selectOneQuestions.length;
}

FormJSONManager.prototype.getSelectOneQuestions = function()
{
    if(!this.selectOneQuestions)
        this._parseQuestions();

    return this.selectOneQuestions;
}

// TODO: This picks the first geopoint question regardless if there are multiple
FormJSONManager.prototype.getGeoPointQuestion = function()
{
    if(this.geopointQuestions.length > 0)
        return this.geopointQuestions[0];
   return null;
}

FormJSONManager.prototype.getQuestionByName = function(name)
{
    return this.questions[name];
}

FormJSONManager.prototype.getChoices = function(question)
{
    var choices = {};
    for(idx in question.children)
    {
        var choice = question.children[idx];
        choices[choice.name] =  choice;
    }
    return choices;
}

/// pass a question object and get its label, if language is specified, try get label for that otherwise return the first label
FormJSONManager.prototype.getMultilingualLabel = function(question, language)
{
    var labelProp = question["label"];

    /// if plain string, return
    if(typeof(labelProp) == "string")
        return labelProp;
    else if(typeof(labelProp) == "object")
    {
        if(language && labelProp.hasOwnProperty(language))
            return labelProp[language];
        else
        {
            var label = null;
            for(key in labelProp)
            {
                label = labelProp[key];
                break;// break at first instance and return that
            }
            return label;
        }

    }
    return null;
}

// used to manage response data loaded via ajax
FormResponseManager = function(url, callback)
{
    this.url = url;
    this.callback = callback;
}

FormResponseManager.prototype.loadResponseData = function(params)
{
    var thisFormResponseMngr = this;
    $.getJSON(thisFormResponseMngr.url, params, function(data){
        thisFormResponseMngr.responses = data;
        thisFormResponseMngr.callback.call(thisFormResponseMngr);
    })
}

FormResponseManager.prototype._toGeoJSON = function()
{
    var features = [];
    var geopointQuestionName = null;
    var geopointQuestion = formJSONMngr.getGeoPointQuestion()
    if(geopointQuestion)
        geopointQuestionName = geopointQuestion["name"];
    for(idx in this.responses)
    {
        var response = this.responses[idx];
        var gps = response[geopointQuestionName];
        if(gps)
        {
            // split gps into its parts
            var parts = gps.split(" ");
            if(parts.length > 1)
            {
                var lng = parts[0];
                var lat = parts[1];

                var geometry = {"type":"Point", "coordinates": [lat, lng]}
                var feature = {"type": "Feature", "id": response._id, "geometry":geometry, "properties":response};
                features.push(feature);
            }
        }
    }

    this.geoJSON = {"type":"FeatureCollection", "features":features};
}

FormResponseManager.prototype.getAsGeoJSON = function()
{
    if(!this.geoJSON)
        this._toGeoJSON();

    return this.geoJSON;
}

// map filter vars
var navContainerSelector = ".nav.pull-right";
var legendParentSelector = ".leaflet-control-container";
var legendContainerId = "legend";
var formJSONMngr = new FormJSONManager(formJSONUrl, loadFormJSONCallback);
var formResponseMngr = new FormResponseManager(mongoAPIUrl, loadResponseDataCallback);

function initialize() {
    // mapbox streets formhub tiles
    var url = 'http://a.tiles.mapbox.com/v3/modilabs.map-hgm23qjf.jsonp';

    // Make a new Leaflet map in your container div
    map = new L.Map(mapId).setView(centerLatLng, defaultZoom);

    var layersControl = new L.Control.Layers();
    map.addControl(layersControl);

    // add bing maps layer
    $.each(bingMapTypeLabels, function(type, label) {
        var bingLayer = new L.TileLayer.Bing(bingAPIKey, type); 
        layersControl.addBaseLayer(bingLayer, label);
    });

    // Get metadata about the map from MapBox
    wax.tilejson(url, function(tilejson) {
        tilejson.attribution += mapBoxAdditAttribution;
        var mapboxstreet = new wax.leaf.connector(tilejson);

        // add mapbox as default base layer
        map.addLayer(mapboxstreet);
        layersControl.addBaseLayer(mapboxstreet, 'MapBox Streets');
    });

    formResponseMngr.loadResponseData({});
}

// callback called after form data has been loaded via the mongo form API
function loadResponseDataCallback()
{
    // load form structure/questions here since we now have some data
    formJSONMngr.loadFormJSON();
}

function _rebuildMarkerLayer(geoJSON, questionName)
{
    var latLngArray = [];
    var questionColor = {};
    var numChoices = 0;
    var randomColorStep = 0;

    if(questionName)
    {
        var question = formJSONMngr.getQuestionByName(questionName);
        var numChoices = question.children.length;
    }

    /// remove existing geoJsonLayer
    map.removeLayer(geoJsonLayer);

    geoJsonLayer = new L.GeoJSON(null, {
        pointToLayer: function (latlng){
            var marker = new L.CircleMarker(latlng, circleStyle);
            return marker;
        }
    });

    geoJsonLayer.on("featureparse", function(geoJSONEvt){
        var marker = geoJSONEvt.layer;
        var latLng = marker._latlng;
        latLngArray.push(latLng);

        /// check if questionName is set
        if(questionName)
        {
            var response = geoJSONEvt.properties[questionName];
            var responseColor = questionColor[response];
            if(!responseColor)
            {
                // generate a color
                responseColor = get_random_color(randomColorStep++, numChoices);
                /// save color for this response
                questionColor[response] = responseColor;
            }
            //circleStyle.color = responseColor;
	    circleStyle.color = '#fff';
            circleStyle.fillColor = responseColor;
            marker.setStyle(circleStyle);
        }
        marker.on('click', function(e){
            var latLng = e.latlng;
            //var targetMarker = e.target;

            // TODO: remove hard coded url - could hack by reversing url using 0000 as instance_id then replacing with actual id
            var url = "/odk_viewer/survey/" + geoJSONEvt.id.toString() + "/";
            // open a loading popup so the user knows something is happening
            //targetMarker.bindPopup('Loading...').openPopup();

            $.get(url).done(function(data){
                var popup = new L.Popup({offset: popupOffset});
                popup.setLatLng(latLng);
                popup.setContent(data);
                //targetMarker.bindPopup(data,{'maxWidth': 500}).openPopup();
                map.openPopup(popup);
            });
        });
    });

    /// need this here instead of the constructor so that we can catch the featureparse event
    geoJsonLayer.addGeoJSON(geoJSON);
    map.addLayer(geoJsonLayer);

    if(questionName)
        rebuildLegend(questionName, questionColor);
    else
        clearLegend();

    // fitting to bounds with one point will zoom too far
    if (latLngArray.length > 1) {
        var latlngbounds = new L.LatLngBounds(latLngArray);
        map.fitBounds(latlngbounds);
    }
}

function rebuildLegend(questionName, questionColor)
{
    // TODO: consider creating container once and keeping a variable reference
    var question = formJSONMngr.getQuestionByName(questionName);
    var choices = formJSONMngr.getChoices(question);
    var questionLabel = formJSONMngr.getMultilingualLabel(question);

    // try find existing legend and destroy
    var legendContainer = $(("#"+legendContainerId));
    if(legendContainer.length > 0)
        legendContainer.empty();
    else
    {
        var container = _createElementAndSetAttrs('div', {"id":legendContainerId});
        var legendParent = $(legendParentSelector);
        legendParent.prepend(container);
        legendContainer = $(container);
    }

    legendContainer.attr("style", "diplay:block");
    var legendTitle = _createElementAndSetAttrs('h3', {}, questionLabel);
    var legendUl = _createElementAndSetAttrs('ul');
    legendContainer.append(legendTitle);
    legendContainer.append(legendUl);
    for(response in questionColor)
    {
        var color = questionColor[response];
        var responseLi = _createElementAndSetAttrs('li');
        var itemLabel = formJSONMngr.getMultilingualLabel(choices[response]);
        var legendIcon = _createElementAndSetAttrs('span', {"class": "legend-bullet", "style": "background-color: " + color});
        var responseText = _createElementAndSetAttrs('span', {}, itemLabel);

        responseLi.appendChild(legendIcon);
        responseLi.appendChild(responseText);

        legendUl.appendChild(responseLi);
    }
}

function clearLegend()
{
    var legendContainer = $(("#"+legendContainerId));
    if(legendContainer.length > 0)
    {
        legendContainer.empty();
        legendContainer.attr("style", "display:none")
    }
}

function loadFormJSONCallback()
{
    // get geoJSON data to setup points - relies on questions having been parsed so has to be in/after the callback
    var geoJSON = formResponseMngr.getAsGeoJSON();

    _rebuildMarkerLayer(geoJSON);

    // just to make sure the nav container exists
    var navContainer = $(navContainerSelector);
    if(navContainer.length == 1)
    {
        // check if we have select one questions
        if(formJSONMngr.getNumSelectOneQuestions() > 0)
        {
            var dropdownLabel = _createElementAndSetAttrs('li');
            var dropdownLink = _createElementAndSetAttrs('a', {"href": "#"}, "Color Responses By");
            dropdownLabel.appendChild(dropdownLink);
            navContainer.append(dropdownLabel);

            var dropDownContainer = _createElementAndSetAttrs('li', {"class":"dropdown"});
            var dropdownCaretLink = _createElementAndSetAttrs('a', {"href":"#", "class":"dropdown-toggle",
                "data-toggle":"dropdown"});
            var dropdownCaret = _createElementAndSetAttrs('b', {"class":"caret"});
            dropdownCaretLink.appendChild(dropdownCaret);
            dropDownContainer.appendChild(dropdownCaretLink);

            var questionUlContainer = _createElementAndSetAttrs("ul", {"class":"dropdown-menu"});

            // create an "All" link to reset the map
            var questionLi = _createSelectOneLi({"name":"", "label":"None"});
            questionUlContainer.appendChild(questionLi);

            // create links for select one questions
            selectOneQuestions = this.getSelectOneQuestions();
            for(idx in selectOneQuestions)
            {
                var question = selectOneQuestions[idx];
                questionLi = _createSelectOneLi(question);
                questionUlContainer.appendChild(questionLi);
            }
            dropDownContainer.appendChild(questionUlContainer);

            navContainer.append(dropDownContainer);
            $('.select-one-anchor').click(function(){
                // rel contains the question's unique name
                var questionName = $(this).attr("rel");
                // get geoJSON data to setup points
                var geoJSON = formResponseMngr.getAsGeoJSON();

                _rebuildMarkerLayer(geoJSON, questionName);
            })
        }
    }
    else
        throw "Container '" + navContainerSelector + "' not found";
}

function _createSelectOneLi(question)
{
    var questionLi = _createElementAndSetAttrs("li", {}, "");
    var questionLabel = formJSONMngr.getMultilingualLabel(question);
    var questionLink = _createElementAndSetAttrs("a", {"href":"#", "class":"select-one-anchor",
        "rel": question.name}, questionLabel);

    questionLi.appendChild(questionLink);
    return questionLi;
}

function _createElementAndSetAttrs(tag, attributes, text)
{
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
