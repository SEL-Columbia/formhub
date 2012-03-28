var centerLatLng = new L.LatLng(center.lat, center.lng);
var defaultZoom = 8;
var mapId = 'map_canvas';
var map;
var mapMarkerIcon = L.Icon.extend({options:{
    iconUrl: '/static/images/marker-solid-24.png',
    shadowUrl: null,
    iconSize: new L.Point(24, 24),
    shadowSize: null,
    iconAnchor: new L.Point(12, 24),
    popupAnchor: new L.Point(0,-24)
}});
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
}

FormJSONManager.prototype.loadFormJSON = function()
{
    var thisManager = this;
    $.getJSON(thisManager.url, function(data){
        thisManager.questions = data.children;
        thisManager._parseQuestions();
        thisManager.callback.call(thisManager);
    })
}

FormJSONManager.prototype._parseQuestions = function()
{
    this.selectOneQuestions = [];
    for(idx in this.questions)
    {
        var question = this.questions[idx];
        if(question.type == "select one")
            this.selectOneQuestions.push(question);
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
    for(idx in this.responses)
    {
        var response = this.responses[idx];
        var gps = response.gps;
        // split gps into its parts
        var parts = gps.split(" ");
        var lng = parts[0];
        var lat = parts[1];

        var geometry = {"type":"Point", "coordinates": [lat, lng]}
        var feature = {"type": "Feature", "id": response._id, "geometry":geometry};
        features.push(feature);
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
    //formJSONMngr.loadFormJSON();

    // use this.getAsGeoJSON (essentially formResponseMngr.getAsGeoJSON) to setup points
    var geoJSON = this.getAsGeoJSON();

    _rebuildMarkerLayer(geoJSON);
}

function _rebuildMarkerLayer(geoJSON)
{
    var latLngArray = [];
    /// remove existing geoJsonLayer
    map.removeLayer(geoJsonLayer);

    geoJsonLayer = new L.GeoJSON(null, {
        pointToLayer: function (latlng){
            var marker = new L.Marker(latlng, {
                icon: new mapMarkerIcon()
            });
            return marker;
        }
    });

    geoJsonLayer.on("featureparse", function(geoJSONEvt){
        var marker = geoJSONEvt.layer;
        latLngArray.push(marker.getLatLng());
        marker.on('click', function(e){
            var targetMarker = e.target;

            // TODO: remove hard coded url - could hack by reversing url using 0000 as instance_id then replacing with actual id
            var url = "/odk_viewer/survey/" + geoJSONEvt.id.toString() + "/";
            // open a loading popup so the user knows something is happening
            targetMarker.bindPopup('Loading...').openPopup();

            $.get(url).done(function(data){
                targetMarker.bindPopup(data,{'maxWidth': 500}).openPopup();
            });
        });
    });

    /// need this here instead of the constructor so that we can catch the featureparse event
    geoJsonLayer.addGeoJSON(geoJSON);
    map.addLayer(geoJsonLayer);

    // fitting to bounds with one point will zoom too far
    if (latLngArray.length > 1) {
        var latlngbounds = new L.LatLngBounds(latLngArray);
        map.fitBounds(latlngbounds);
    }
}

/// NOTE: "this" here refers to the instance of formJSONManager that was used to load the form JSON
function loadFormJSONCallback()
{
    // just to make sure the nav container exists
    var navContainer = $(navContainerSelector);
    if(navContainer.length == 1)
    {
        // check if we have select one questions
        if(this.getNumSelectOneQuestions() > 0)
        {
            var dropdownLabel = _createElementAndSetAttrs('li');
            var dropdownLink = _createElementAndSetAttrs('a', {"href": "#"}, "Color Responses By:");
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
                colorResponsesBy(questionName);
            })
        }
    }
    else
        throw "Container '" + navContainerSelector + "' not found";
}

function _createSelectOneLi(question)
{
    var questionLi = _createElementAndSetAttrs("li", {}, "");
    var questionLink = _createElementAndSetAttrs("a", {"href":"#", "class":"select-one-anchor",
        "rel": question.name}, question.label);

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
