var constants = {
    //pyxform constants
    NAME: "name", LABEL: "label", TYPE: "type", CHILDREN: "children",
    //formhub query syntax constants
    START: "start", LIMIT: "limit", COUNT: "count", FIELDS: "fields",
    //
    GEOLOCATION: "_geolocation"
};

// used to load and manage form questions
FormJSONManager = function(url, callback)
{
    this.url = url;
    this.callback = callback;
    this.geopointQuestions = [];
    this.selectOneQuestions = [];
    this.supportedLanguages = [];
    this.questions = {};
};

// batch api loads into this batchsize
FormJSONManager.BATCH_SIZE = 1000;

FormJSONManager.prototype.loadFormJSON = function()
{
    var thisManager = this;
    $.getJSON(thisManager.url, function(data){
        thisManager._init(data);
    });
};

FormJSONManager.prototype._init = function(data)
{
    var thisManager = this;
    thisManager.supportedLanguages = [];
    thisManager._parseQuestions(data[constants.CHILDREN]);
    if(this.supportedLanguages.length == 0)
    {
        this.supportedLanguages.push("default");
    }
    if (thisManager.callback) thisManager.callback.call(thisManager);
};

FormJSONManager.prototype._parseQuestions = function(questionData, parentQuestionName)
{
    var idx;
    for(idx in questionData)
    {
        var question = questionData[idx];
        var questionName = question[constants.NAME];
        if(parentQuestionName && parentQuestionName !== "")
            questionName = parentQuestionName + "/" + questionName;
        question[constants.NAME] = questionName;

        if(question[constants.TYPE] != "group")
        {
            this.questions[questionName] = question;
            // check language label and add to list of languages
            this._parseSupportedLanguages(question);
        }
        /// if question is a group, recurse to collect children
        if((question[constants.TYPE] == "group" || question[constants.TYPE] == "repeat") && question.hasOwnProperty(constants.CHILDREN))
            this._parseQuestions(question[constants.CHILDREN], question[constants.NAME]);

        if(question[constants.TYPE] == "select one")
            this.selectOneQuestions.push(question);
        if(question[constants.TYPE] == "geopoint" || question[constants.TYPE] == "gps")
            this.geopointQuestions.push(question);
    }
};


FormJSONManager.prototype.getTypeOfQuestion = function(questionName) {
    var question = _(this.questions).find(function(q) {
        return q.name===questionName;
    });
    return question.type;
};

FormJSONManager.prototype.getQuestionsOfType = function(type) {
    return _(this.questions).filter(function(q) {
        return q.type===type;
    });
};

FormJSONManager.prototype.getNumSelectOneQuestions = function()
{
    return this.selectOneQuestions.length;
};

FormJSONManager.prototype.getSelectOneQuestions = function()
{
    return this.selectOneQuestions;
};

// TODO: This picks the first geopoint question regardless if there are multiple
FormJSONManager.prototype.getGeoPointQuestion = function()
{
    if(this.geopointQuestions.length > 0)
        return this.geopointQuestions[0];
    return null;
};

FormJSONManager.prototype.getQuestionByName = function(name)
{
    return this.questions[name];
};

FormJSONManager.prototype.getChoices = function(question)
{
    var choices = {};
    for(i=0;i<question[constants.CHILDREN].length;i++)
    {
        var choice = question[constants.CHILDREN][i];
        choices[choice[constants.NAME]] =  choice;
    }
    return choices;
};

FormJSONManager.prototype._parseSupportedLanguages = function(question)
{

    if(question.hasOwnProperty(constants.LABEL))
    {
        var labelProp = question[constants.LABEL];
        if(typeof(labelProp) == "object")
        {
            for(key in labelProp)
            {
                if(this.supportedLanguages.indexOf(key) == -1)
                {
                    this.supportedLanguages.push(key);
                }
            }
        }
    }
};

/// pass a question object and get its label, if language is specified, try get label for that otherwise return the first label
FormJSONManager.prototype.getMultilingualLabel = function(question, language)
{
    var key;
    var labelProp = question[constants.LABEL];

    // if plain string, its a "label" already, return
    if(typeof(labelProp) == "string")
        return labelProp;
    // else pick out the right language if it exists
    else if(typeof(labelProp) == "object")
        if(language && labelProp.hasOwnProperty(language))
            return labelProp[language];
        else // and if the given language isn't present, return the first label
            return _.values(labelProp)[0];
    // fallback (ie, no label) -- return raw name
    return question[constants.NAME];
};

// used to manage response data loaded via ajax
FormResponseManager = function(url, callback)
{
    this.url = url;
    this.callback = callback;
    this._select_one_filters = [];
    this._currentSelectOneQuestionName = null; // name of the currently selected "View By Question if any"
};

FormResponseManager.prototype.loadResponseData = function(params, start, limit, geoPointField, otherFieldsToLoad, rebuildFlag)
{
    var thisFormResponseMngr = this;
    var urlParams = params, geoParams = {};
    var all_data = [];
    var totalCount, progress = 0;
    var $progressElm = $('#progress-modal');
    if (rebuildFlag !== true)
        rebuildFlag = false;

    start = parseInt(start,10);
    limit = parseInt(limit, 10);
    // cap limit to BATCH_SIZE
    limit = limit?Math.min(limit, FormJSONManager.BATCH_SIZE):FormJSONManager.BATCH_SIZE;
    // use !isNaN so we also have zeros
    if(!isNaN(start)) urlParams[constants.START] = start;
    if(!isNaN(limit)) urlParams[constants.LIMIT] = limit;

    /* TODO: re-enable geo-point pre-population once we work out making the rest of
             the load happen after an asynchronous wait.
       TODO: also make sure that if geoPointField is null / undefined, the call doesn't happen*/
    // query the geo-data and queue the querying of all the data
    // make the callback before the full data is loaded
    if(otherFieldsToLoad && otherFieldsToLoad.length > 0)
        urlParams[constants.FIELDS] = JSON.stringify(otherFieldsToLoad);
    // TODO: make the full data load asynchronous

    var successFnc = function(data){
        // id data is an empty array, we are done
        if(data.length === 0)
        {
            if($progressElm.length > 0)
            {
                $progressElm.modal('hide');
            }
            thisFormResponseMngr.responses = all_data;
            thisFormResponseMngr.responseCount = data.length;
            thisFormResponseMngr._toDatavore(rebuildFlag);
            thisFormResponseMngr.callback.call(thisFormResponseMngr);
        }
        else
        {
            // append data
            all_data = all_data.concat(data);
            // update progress bar
            progress = Math.round((all_data.length / totalCount) * 100);
            if($progressElm.length > 0)
            {
                $progressElm.find('.progress .bar').css('width', (progress + '%'));
            }
            // calculate a new start position
            urlParams[constants.START] += data.length;
            loadFnc(thisFormResponseMngr.url, urlParams);
        }
    };

    var loadFnc = function(url, params)
    {
        var jqXHR = $.getJSON(url, params);
        jqXHR.success(successFnc);
        jqXHR.error(function(e){
            // remove the fields param if we get an error and try again
            params[constants.FIELDS] = undefined;
            // change global urlParams as well for additional calls
            urlParams[constants.FIELDS] = undefined;
            // in case of failure - to avoid a loop lets call getJSON ourselves
            $.getJSON(url, params)
                .success(successFnc)
                .error(function(e){
                    // cut the limit in half and re-try
                    params[constants.LIMIT] = Math.max(1, Math.round(params[constants.LIMIT]/2));
                    // apply to global params for subsequent calls
                    urlParams[constants.LIMIT] = params[constants.LIMIT];
                    loadFnc(url, params);
                });
        });
        return jqXHR;
    };

    // load the count
    var countParams = _.clone(params);
    countParams['count'] = 1;
    if(countParams.hasOwnProperty(constants.FIELDS))
    {
        delete(countParams[constants.FIELDS])
    }
    $.getJSON(thisFormResponseMngr.url, countParams)
        .success(function(data){
            totalCount = data[0].count;
            // show the modal
            if($progressElm.length > 0)
            {
                $progressElm.modal('show');
            }
            // start loading
            loadFnc(thisFormResponseMngr.url, urlParams);
        });
};

FormResponseManager.prototype.setCurrentSelectOneQuestionName = function(name)
{
    this._currentSelectOneQuestionName = name;
};

FormResponseManager.prototype.addResponseToSelectOneFilter = function(name)
{
    if(this._select_one_filters.indexOf(name) == -1)
        this._select_one_filters.push(name);
};

FormResponseManager.prototype.removeResponseFromSelectOneFilter = function(name)
{
    var idx = this._select_one_filters.indexOf(name);
    if(idx > -1)
        this._select_one_filters.splice(idx, 1);
};

FormResponseManager.prototype.clearSelectOneFilterResponses = function(name)
{
    this._select_one_filters = [];
};

/// this cannot be called before the form is loaded as we rely on the form to determine the gps field
FormResponseManager.prototype._toGeoJSON = function()
{
    var features = [];
    var geopointQuestionName = constants.GEOLOCATION;
    _(this.responses).each(function (response) {
        var gps = response[geopointQuestionName];
        if(gps && gps[0] && gps[1])
        {
            var lat = gps[0];
            var lng = gps[1];

            var geometry = {"type":"Point", "coordinates": [lng, lat]};
            var feature = {"type": "Feature", "id": response._id, "geometry":geometry, "properties":response};
            features.push(feature);
        }
    });

    this.geoJSON = {"type":"FeatureCollection", "features":features};
};

/// this cannot be called before the form is loaded as we rely on the form to determine the gps field
FormResponseManager.prototype._toHexbinGeoJSON = function(latLongFilter)
{
    var features = [];
    var latLngArray = [];
    var geopointQuestionName = constants.GEOLOCATION;
    // The following functions needed hexbin-js doesn't deal well with negatives
    function fixlng(n) { n = parseFloat(n); return (n < 0 ? 360 + n : n); }
    function fixlnginv(n) { n = parseFloat(n); return (n > 180 ? n - 360 : n); }
    function fixlat(n) { n = parseFloat(n); return (n < 0 ? 90 + n : 90 + n); }
    function fixlatinv(n) { n = parseFloat(n); return (n > 90 ? n - 90 : n - 90); }
    _(this.responses).each(function(response) {
        var gps = response[geopointQuestionName];
        if(gps && gps[0] && gps[1])
        {
            var lat = gps[0];
            var lng = gps[1];
            if(latLongFilter===undefined || latLongFilter(lat, lng)) {
                latLngArray.push({ lat: fixlat(lat), lng: fixlng(lng), response_id: response._id});
            }
        }
    });
    try {
        hexset = d3.layout.hexbin()
                .xValue( function(d) { return d.lng; } )
                .yValue( function(d) { return d.lat; } )
                ( latLngArray );
    } catch (err) {
        this.hexGeoJSON = {"type": "FeatureCollection", "features": []};
        this._addMetadataColumn("_id", "hexID", dv.type.nominal, _.map(latLngArray, function(x) { return undefined; }));
        return;
    };
    var hexOfResponseID = {}, responseIDs = [], hexID = '';
    _.each(hexset, function(hex, idx) {
        if(hex.data.length) {
            hexID = 'HEX: ' + idx;
            var geometry = {"type":"Polygon",
                            "coordinates": _(hex.points).map(function(d) {
                                    return [fixlatinv(d.y), fixlnginv(d.x)];
                                    })
                            };
            responseIDs = [];
            _(hex.data).each(function(d) {
                responseIDs.push(d.response_id);
                hexOfResponseID[d.response_id] = hexID;
            });
            features.push({"type": "Feature",
                           "geometry":geometry,
                           "properties": { "id" : hexID, "responseIDs" : responseIDs }
                           });
        }
    });
    this.hexGeoJSON = {"type":"FeatureCollection", "features":features};
    this._addMetadataColumn("_id", "hexID", dv.type.nominal, hexOfResponseID);
};
FormResponseManager.prototype.getAsGeoJSON = function(rebuildFlag)
{
    if(!this.geoJSON || rebuildFlag)
        this._toGeoJSON();

    return this.geoJSON;
};

FormResponseManager.prototype.getAsHexbinGeoJSON = function(latLongFilter)
{
    if(!this.hexGeoJSON)
        this._toHexbinGeoJSON(latLongFilter);

    return this.hexGeoJSON;
};

FormResponseManager.prototype.dvQuery = function(dvQueryObj, rebuildFlag)
{
    this._toDatavore(rebuildFlag);
    return this.dvResponseTable.query(dvQueryObj);
};

FormResponseManager.prototype._toDatavore = function(rebuildFlag)
{
    // Datavore table should only be built once, unless rebuildFlag is passed in
    if (this.dvResponseTable && !rebuildFlag) {
        return;
    }
    var dvData = {}, qName = '';
    var questions = formJSONMngr.questions;
    var responses = this.responses;
    // CREATE A Datavore table here; the mapping from form types to datavore types
    var typeMap = {"integer" : dv.type.numeric, "decimal" : dv.type.numeric,
                   "select one" : dv.type.nominal,
                   "text" : dv.type.unknown, "select multiple" : dv.type.unknown,
                   "_id" : dv.type.unknown };
    // chuck all questions whose type isn't in typeMap; add an _id "question"
    // TODO: if datavore is our only datastore, this chucking can be removed (with care)
    questions = _(questions).filter(function(q) { return typeMap[q[constants.TYPE]]; });
    questions.push({'name' : "_id", 'type' : "_id"});
    _(questions).each(function(question) {
        qName = question[constants.NAME];
        dvData[qName] = [];
        _(responses).each( function (response) {
            dvData[qName].push(response[qName]);
        });
    });
    var dvTable = dv.table();
    _(questions).each(function(question) {
        qName = question[constants.NAME];
        dvTable.addColumn(qName, dvData[qName], typeMap[question[constants.TYPE]]);
    });
    this.dvResponseTable = dvTable;
};

FormResponseManager.prototype._addMetadataColumn = function(keyName, metaColumnName, metaColumnType, metaData)
{
    // Adds a metadata column, after aligning values according to keyName
    if (!this.dvResponseTable) this._toDatavore();
    var columnOfKeys = this.dvResponseTable[keyName];
    if (!columnOfKeys ) { throw "No data for key " + keyName + " in dvReponseTable"; }
    // question: Some of these are undefined; is that okay?
    var colToAdd = _(columnOfKeys).map(function(key) { return metaData[key]; });
    this.dvResponseTable.addColumn(metaColumnName, colToAdd, metaColumnType);
};

FormResponseManager.prototype._toPivotJs = function(fields)
{
    this.pivotJsData = null;
    var pivotData = [];

    // first row is the titles
    var titles = [];
    for(i=0;i<fields.length;i++)
    {
        titles.push(fields[i][constants.NAME]);
    }
    pivotData.push(titles);

    // now we do the data making sure its in the same order as the titles above
    _(this.responses).each(function (response) {
        var row = [];

        for(i=0;i<fields.length;i++)
        {
            var field = fields[i];
            var title = field[constants.NAME];
            var pivotType = field[constants.TYPE];
            var data = "";
            /// check if we have a response in for this title
            if(response.hasOwnProperty(title))
            {
                data = response[title];
                /// if this is time(date + time) data remove the T inside datetime data
                if(pivotType == "time")
                {
                    data = fhUtils.DateTimeToISOString(data);
                }
            }
            row.push(data);
        }
        pivotData.push(row);
    });

    this.pivotJsData = JSON.stringify(pivotData);
};

/**
 * Return an object in the data Array
 * @param fields
 */
FormResponseManager.prototype._toDataTables = function(fields)
{
    this.dtData = null;
    var aaData = [];

    // now we do the data making sure its in the same order as the titles above
    _(this.responses).each(function (response) {
        var row = [];

        for(i=0;i<fields.length;i++)
        {
            var field = fields[i];
            var title = field[constants.NAME];
            var pivotType = field[constants.TYPE];
            var data = "";
            /// check if we have a response in for this title
            if(response.hasOwnProperty(title))
            {
                data = response[title];
                /// if this is time(date + time) data remove the T inside datetime data
                if(pivotType == "time")
                {
                    data = fhUtils.DateTimeToISOString(data);
                }
            }
            row.push(data);
        }
        aaData.push(row);
    });

    this.dtData = aaData;
};

FormResponseManager.prototype.getAsPivotJs = function(fields)
{
    if(!this.pivotJsData)
        this._toPivotJs(fields);
    return this.pivotJsData;
};

FormResponseManager.prototype.getAsDataTables =  function(fields)
{
    if(!this.dtData)
        this._toDataTables(fields);
    return this.dtData;
};

function encodeForCSSclass (str) {
    str = (str + '').toString();

    return str.replace(" ", "-");
}
