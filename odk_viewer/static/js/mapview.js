var centerLatLng = new L.LatLng(!center.lat?0.0:center.lat, !center.lng?0.0:center.lng);
var defaultZoom = 8;
var mapId = 'map_canvas';
var map;
// array of mapbox maps to use as base layers - the first one will be the default map
var mapboxMaps = [
    {'label': 'Mapbox Street', 'url': 'http://a.tiles.mapbox.com/v3/modilabs.map-hgm23qjf.jsonp'},
    {'label': 'MapBox Streets Light', 'url': 'http://a.tiles.mapbox.com/v3/modilabs.map-p543gvbh.jsonp'},
    {'label': 'MapBox Streets Zenburn', 'url': 'http://a.tiles.mapbox.com/v3/modilabs.map-bjhr55gf.jsonp'}
];
var allowResetZoomLevel = true; // used to allow zooming when first loaded
var popupOffset = new L.Point(0, -10);
var notSpecifiedCaption = "Not Specified";
var colorPalette = ['#8DD3C7', '#FB8072', '#FFFFB3', '#BEBADA', '#80B1D3', '#FDB462', '#B3DE69', '#FCCDE5', '#D9D9D9',
    '#BC80BD', '#CCEBC5', '#FFED6F'];
var circleStyle = {
    color: '#fff',
    border: 8,
    fillColor: '#ff3300',
    fillOpacity: 0.9,
    radius: 8
}
// TODO: can we get the entire from mongo API
var amazonUrlPrefix = "https://formhub.s3.amazonaws.com/";
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
    this.selectOneQuestions = [];
    this.supportedLanguages = [];
    this.questions = {};
}

FormJSONManager.prototype.loadFormJSON = function()
{
    var thisManager = this;
    $.getJSON(thisManager.url, function(data){
        thisManager._parseQuestions(data.children);
        thisManager._parseSupportedLanguages();
        thisManager.callback.call(thisManager);
    })
}

FormJSONManager.prototype._parseQuestions = function(questionData, parentQuestionName)
{
    for(idx in questionData)
    {
        var question = questionData[idx];
        var questionName = question.name;
        if(parentQuestionName && parentQuestionName != "")
            questionName = parentQuestionName + "/" + questionName;
        question.name = questionName;

        if(question.type != "group")
        {
            this.questions[questionName] = question;
        }
        /// if question is a group, recurse to collect children
        else if(question.type == "group" && question.hasOwnProperty("children"))
            this._parseQuestions(question.children, question.name);

        if(question.type == "select one")
            this.selectOneQuestions.push(question);
        if(question.type == "geopoint" || question.type == "gps")
            this.geopointQuestions.push(question);
    }
}

FormJSONManager.prototype.getNumSelectOneQuestions = function()
{
    return this.selectOneQuestions.length;
}

FormJSONManager.prototype.getSelectOneQuestions = function()
{
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

FormJSONManager.prototype._parseSupportedLanguages = function()
{
    // run through question objects, stop at first question with label object and check it for multiple languages
    for(questionName in this.questions)
    {
        var question = this.questions[questionName];
        if(question.hasOwnProperty("label"))
        {
            var labelProp = question["label"];
            if(typeof(labelProp) == "string")
                this.supportedLanguages = ["default"];
            else if(typeof(labelProp) == "object")
            {
                for(key in labelProp)
                {
                    var language = {"name": encodeForCSSclass(key), "label": key}
                    this.supportedLanguages.push(language)
                }
            }
            break;
        }
    }
}

function encodeForCSSclass (str) {
    str = (str + '').toString();

    return str.replace(" ", "-");
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
    // return raw name
    return question["name"];
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
    // Make a new Leaflet map in your container div
    map = new L.Map(mapId).setView(centerLatLng, defaultZoom);

    var layersControl = new L.Control.Layers();
    map.addControl(layersControl);

    // add bing maps layer
    $.each(bingMapTypeLabels, function(type, label) {
        var bingLayer = new L.TileLayer.Bing(bingAPIKey, type); 
        layersControl.addBaseLayer(bingLayer, label);
    });

    $.each(mapboxMaps, function(idx, mapData){
        // Get metadata about the map from MapBox
        wax.tilejson(mapData.url, function(tilejson) {
            tilejson.attribution += mapBoxAdditAttribution;
            var mapboxstreet = new wax.leaf.connector(tilejson);

            layersControl.addBaseLayer(mapboxstreet, mapData.label);

            // only add default layer to map
            if(idx == 0)
                map.addLayer(mapboxstreet);
        });
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
    var paletteCounter = 0;

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
            // check if response is missing (user did not specify)
            if(!response)
                response = notSpecifiedCaption;
            var responseColor = questionColor[response];
            if(!responseColor)
            {
                // check if color palette has colors we haven't used
                if(paletteCounter < colorPalette.length)
                    responseColor = colorPalette[paletteCounter++];
                // generate a color
                else
                {
                    // number of steps is reduced by the number of colors in our palette
                    responseColor = get_random_color(randomColorStep++, (numChoices - colorPalette.length));
                }
                /// save color for this response
                questionColor[response] = responseColor;
            }
            var newStyle = {
                color: '#fff',
                border: circleStyle.border,
                fillColor: responseColor,
                fillOpacity: circleStyle.fillOpacity,
                radius: circleStyle.opacity
            }
            marker.setStyle(newStyle);
        }
        marker.on('click', function(e){
            var latLng = e.latlng;
            //var targetMarker = e.target;

            // TODO: remove hard coded url - could hack by reversing url using 0000 as instance_id then replacing with actual id
            var url = "/odk_viewer/survey/" + geoJSONEvt.id.toString() + "/";
            // open a loading popup so the user knows something is happening
            //targetMarker.bindPopup('Loading...').openPopup();

            $.getJSON(mongoAPIUrl, {"_id":geoJSONEvt.id}).done(function(data){
                var popup = new L.Popup({offset: popupOffset});
                popup.setLatLng(latLng);
                var content;
                if(data.length > 0)
                    content = JSONSurveyToHTML(data[0]);
                else
                    content = "An error occurred";
                popup.setContent(content);
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
    // don't zoom when we "view by response"
    if (latLngArray.length > 1 && allowResetZoomLevel) {
        var latlngbounds = new L.LatLngBounds(latLngArray);
        map.fitBounds(latlngbounds);
    }
}

/*
 * Format the json data to HTML for a map popup
 */
function JSONSurveyToHTML(data)
{
    var htmlContent = '<table class="table table-bordered table-striped"> <thead>\n<tr>\n<th>Question</th>\n<th>Response</th>\n</tr>\n</thead>\n<tbody>\n';

    // add images if any
    // TODO: this assumes all attachments are images
    if(data._attachments.length > 0)
    {
        var mediaContainer = '<ul class="media-grid">';
        for(idx in data._attachments)
        {
            var attachmentUrl = data._attachments[idx];
            mediaContainer += '<li><a href="#">';
            var imgSrc = amazonUrlPrefix + attachmentUrl;
            var imgTag = _createElementAndSetAttrs('img', {"class":"thumbnail", "width":"210", "src": imgSrc})
            mediaContainer += imgTag.outerHTML;
            mediaContainer += '</a></li>';

        }
        mediaContainer += '</ul>';
        htmlContent += mediaContainer;
    }

    // add language select if we have multiple languages
    if(formJSONMngr.supportedLanguages.length > 1)
    {
        var selectTag = _createElementAndSetAttrs('select', {"id":"selectLanguage"});
        for(idx in formJSONMngr.supportedLanguages)
        {
            var langauge = formJSONMngr.supportedLanguages[idx];
            var o = new Option(langauge.label, langauge.name);
            selectTag.add(o);
        }
        htmlContent += selectTag.outerHTML;
    }

    for(questionName in formJSONMngr.questions)
    {
        //if(data[questionName])
        {
            var question  = formJSONMngr.getQuestionByName(questionName);
            var response = _createElementAndSetAttrs('tr', {});
            var td = _createElementAndSetAttrs('td', {});
            // if at least one language, iterate over them and add a span for each
            if(formJSONMngr.supportedLanguages.length > 0)
            {
                for(idx in formJSONMngr.supportedLanguages)
                {
                    var language = formJSONMngr.supportedLanguages[idx];
                    var style = "";
                    if(idx > 0)
                    {
                        style = "display: none"
                    }
                    var span = _createElementAndSetAttrs('span', {"class": ("language " + language.name), "style": style}, formJSONMngr.getMultilingualLabel(question, language.label));
                    td.appendChild(span);
                }
            }
            else
            {
                var span = _createElementAndSetAttrs('span', {"class": "language"}, formJSONMngr.getMultilingualLabel(question));
                td.appendChild(span);
            }

            response.appendChild(td);
            td = _createElementAndSetAttrs('td', {}, data[questionName]);
            response.appendChild(td);
            htmlContent += response.outerHTML;
        }
    }
    htmlContent += '</tbody></table>';
    return htmlContent;
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
        var itemLabel = response;
        // check if the choices contain this response before we try to get the reponse's label
        if(choices.hasOwnProperty(response))
            itemLabel = formJSONMngr.getMultilingualLabel(choices[response]);
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
            var dropdownLink = _createElementAndSetAttrs('a', {"href": "#"}, "View By");
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
                allowResetZoomLevel = false; // disable zoom reset whenever this is clicked
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
