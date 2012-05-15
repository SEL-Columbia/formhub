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
    for(i=0;i<question.children.length;i++)
    {
        var choice = question.children[i];
        choices[choice.name] =  choice;
    }
    return choices;
}

FormJSONManager.prototype.setCurrentSelectOneQuestionName = function(name)
{
    this._currentSelectOneQuestionName = name;
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
    this._select_one_filters = [];
    this._currentSelectOneQuestionName = null; // name of the currently selected "View By Question if any"
}

FormResponseManager.prototype.loadResponseData = function(params, start, limit)
{
    var thisFormResponseMngr = this;

    /// invalidate geoJSON data
    this.geoJSON = null;
    this.dtData = null;

    /// append select-one filters to params
    if(formJSONMngr._currentSelectOneQuestionName)
    {
        var questionName = formJSONMngr._currentSelectOneQuestionName;
        var orFilters = [];
        for(idx in this._select_one_filters)
        {
            var responseName =  this._select_one_filters[idx];
            if(responseName == notSpecifiedCaption)
                orFilters.push(null);
            else
                orFilters.push(responseName);
        }
        if(orFilters.length > 0)
        {
            var inParam = {'$in': orFilters};
            params[questionName] = inParam;
        }
    }
    var urlParams = {'query':JSON.stringify(params)};
    start = parseInt(start)
        // use !isNaN so we also have zeros
    if(!isNaN(start))
        urlParams['start'] = start
    limit = parseInt(limit)
    if(!isNaN(limit))
        urlParams['limit'] = limit
    // first do the count
    urlParams['count'] = 1
    $.getJSON(thisFormResponseMngr.url, urlParams).success(function(data){
            thisFormResponseMngr.responseCount = data[0]['count']
            urlParams['count'] = 0
            $.getJSON(thisFormResponseMngr.url, urlParams, function(data){
                thisFormResponseMngr.responses = data;
                thisFormResponseMngr.callback.call(thisFormResponseMngr);
            })
        })
}

FormResponseManager.prototype.addResponseToSelectOneFilter = function(name)
{
    if(this._select_one_filters.indexOf(name) == -1)
        this._select_one_filters.push(name);
}

FormResponseManager.prototype.removeResponseFromSelectOneFilter = function(name)
{
    var idx = this._select_one_filters.indexOf(name);
    if(idx > -1)
        this._select_one_filters.splice(idx, 1);
}

FormResponseManager.prototype.clearSelectOneFilterResponses = function(name)
{
    this._select_one_filters = [];
}

/// this cannot be called before the form is loaded as we rely on the form to determine the gps field
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

/// this cannot be called before the form is loaded as we rely on the form to determine the gps field
FormResponseManager.prototype._toHexbinGeoJSON = function()
{
    var responses = this.responses;
    var features = [];
    var latLngArray = [];
    var geopointQuestionName = null;
    var geopointQuestion = formJSONMngr.getGeoPointQuestion()
    function fixlng(n) { return (n < 0 ? 90 - n : n); };
    function fixlnginv(n) { return (n > 90 ? 90 - n : n); };
    if(geopointQuestion)
        geopointQuestionName = geopointQuestion["name"];
    for(idx in responses)
    {
        var response = responses[idx];
        var gps = response[geopointQuestionName];
        if(gps)
        {
            // split gps into its parts
            var parts = gps.split(" ");
            if(parts.length > 1)
            {
                var lat = parseFloat(parts[0]);
                var lng = parseFloat(parts[1]);
                latLngArray.push({ lat: lat, 
                                   lng: fixlng(lng)});
                //if(latLongFilter(lat, lng))
            }
        }
    }
    hexset = d3.layout.hexbin()
                .xValue( function(d) { return d.lng; } )
                .yValue( function(d) { return d.lat; } )
                ( latLngArray );
    countMax = d3.max( hexset, function(d) { return d.data.length; } );
    for(idx in hexset) { 
        hex = hexset[idx];
        if(!hex.data.length) continue; // No need to put in polygons without points inside of them
        var geometry = {"type":"Polygon", 
                        "coordinates": _(hex.points).map(function(d) {
                                        return [d.y, fixlnginv(d.x)];
                                        })
                        };
        var feature = {"type": "Feature", 
                        "geometry":geometry, 
                        "properties": {"rawdata" :_(hex.data).map(function(d) {
                                        return {lat: d.lat, lng: fixlnginv(d.lng)}; }),
                                       "count" : hex.data.length,
                                       "countMax" : countMax
                                      }
                      };
        features.push(feature);
    } 

    this.hexGeoJSON = {"type":"FeatureCollection", "features":features};
}
FormResponseManager.prototype.getAsGeoJSON = function()
{
    if(!this.geoJSON)
        this._toGeoJSON();

    return this.geoJSON;
}
FormResponseManager.prototype.getAsHexbinGeoJSON = function()
{
    if(!this.hexGeoJSON)
        this._toHexbinGeoJSON();

    return this.hexGeoJSON;
}



FormResponseManager.prototype._toPivotJs = function(fields)
{
    this.pivotJsData = null;
    var pivotData = [];

    // first row is the titles
    var titles = [];
    for(i=0;i<fields.length;i++)
    {
        titles.push(fields[i]["name"]);
    }
    pivotData.push(titles);

    // now we do the data making sure its in the same order as the titles above
    for(idx in this.responses)
    {
        var response = this.responses[idx];
        var row = [];

        for(i=0;i<fields.length;i++)
        {
            var field = fields[i]
            var title = field["name"];
            var pivotType = field["type"];
            var data = "";
            /// check if we have a response in for this title
            if(response.hasOwnProperty(title))
            {
                data = response[title];
                /// if this is time(date + time) data remove the T inside datetime data
                if(pivotType == "time")
                {
                    var pattern = /^\d{4}\-\d{2}\-\d{2}T/;
                    if(pattern.test(data))
                    {
                        data = data.replace("T", " ");
                    }
                }
            }
            row.push(data);
        }
        pivotData.push(row);
    }

    this.pivotJsData = JSON.stringify(pivotData);
}

/**
 * Return an object in the data Array
 * @param fields
 */
FormResponseManager.prototype._toDataTables = function(fields)
{
    this.dtData = null;
    var aaData = [];

    // now we do the data making sure its in the same order as the titles above
    for(idx in this.responses)
    {
        var response = this.responses[idx];
        var row = [];

        for(i=0;i<fields.length;i++)
        {
            var field = fields[i]
            var title = field["name"];
            var pivotType = field["type"];
            var data = "";
            /// check if we have a response in for this title
            if(response.hasOwnProperty(title))
            {
                data = response[title];
                /// if this is time(date + time) data remove the T inside datetime data
                if(pivotType == "time")
                {
                    var pattern = /^\d{4}\-\d{2}\-\d{2}T/;
                    if(pattern.test(data))
                    {
                        data = data.replace("T", " ");
                    }
                }
            }
            row.push(data);
        }
        aaData.push(row);
    }

    this.dtData = aaData;
}

FormResponseManager.prototype.getAsPivotJs = function(fields)
{
    if(!this.pivotJsData)
        this._toPivotJs(fields);
    return this.pivotJsData;
}

FormResponseManager.prototype.getAsDataTables =  function(fields)
{
    if(!this.dtData)
        this._toDataTables(fields);
    return this.dtData;
}

function encodeForCSSclass (str) {
    str = (str + '').toString();

    return str.replace(" ", "-");
}
