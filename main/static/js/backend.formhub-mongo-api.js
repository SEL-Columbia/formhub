this.recline = this.recline || {};
this.recline.Backend = this.recline.Backend || {};
this.recline.Backend.FormhubMongoAPI = this.recline.Backend.FormhubMongoAPI || {};
this.fh = this.fh || {};
this.fh.constants = {
    //pyxform constants
    NAME: "name", LABEL: "label", TYPE: "type", CHILDREN: "children",
    //formhub query syntax constants
    START: "start", LIMIT: "limit", COUNT: "count", FIELDS: "fields",
    // types
    TEXT: "text", INTEGER: "integer", FLOAT: "float", DATE: "date",
    TIME: "time", DATETIME: "datetime", GROUP: "group", NOTE: "note",
    GEOPOINT: "geopoint", GPS: "gps", SELECT_ONE: "select_one"
};

(function($, my) {
    my.__type__ = 'Formhub';

    my.fhReclineTypeMap = {};
    my.fhReclineTypeMap[fh.constants.TEXT] = "string";
    my.fhReclineTypeMap[fh.constants.INTEGER] = "integer";
    my.fhReclineTypeMap[fh.constants.FLOAT] = "number";
    my.fhReclineTypeMap[fh.constants.DATE] = "date";
    my.fhReclineTypeMap[fh.constants.TIME] = "time";
    my.fhReclineTypeMap[fh.constants.DATETIME] = "date-time";
    my.fhReclineTypeMap[fh.constants.GEOPOINT] = "geo_point";
    my.fhReclineTypeMap[fh.constants.GPS] = "geo_point";
    my.fhReclineTypeMap[fh.constants.SELECT_ONE] = "string";
    my.fhReclineTypeMap["select one"] = "string";
    my.fhReclineTypeMap["select multiple"] = "string";
    my.fhReclineTypeMap["select all that apply"] = "string";

    my._fhToReclineType = function(fhType)
    {
        if(my.fhReclineTypeMap.hasOwnProperty(fhType))
        {
            return my.fhReclineTypeMap[fhType.toLowerCase()];
        }
        return fhType;
    };

    my._parseFields = function(fhFields, parentXPath)
    {
        var fields = [];
        _.each(fhFields, function(fhField, index){
            var newXPath = [];
            if(parentXPath)
                newXPath.push(parentXPath);
            if(_.indexOf([fh.constants.GROUP, fh.constants.NOTE], fhField.type) > -1)
            {

                // only add if we have children - notes dont have children
                if(fhField.children)
                {
                    newXPath.push(fhField.name);
                    newXPath = newXPath.join("/");
                    _.each(my._parseFields(fhField.children, newXPath), function(field, index){
                        fields.push(field);
                    });
                }
            }
            else
            {
                var field = {};
                newXPath.push(fhField.name);
                field.id = newXPath.join("/");
                //@todo: using the fhType we can setup custom formatters here e.g. for photos and videos
                field.type = my._fhToReclineType(fhField.type);
                //@todo: check for multi-lang labels
                field.label = fhField.label?fhField.label:fhField.name; // some fields like start/end only have a name but no label
                fields.push(field);
            }
        });
        return fields;
    };

    my._parseSchema = function(data)
    {
        var schema = {metadata: {}, fields: []};
        var self = this;
        _.each(data, function(val, key){
            if(key == fh.constants.CHILDREN)
            {
                schema.fields = self._parseFields(data.children);
            }
            else
            {
                schema.metadata[key] = val;
            }
        });
        return schema;
    };

    my.fetch = function(dataset){
        var deferred = $.Deferred();
        var jqXHR = $.getJSON(dataset.formUrl);
        var self = this;
        jqXHR.done(function(data){
            var schema = self._parseSchema(data);
            deferred.resolve({
                fields: schema.fields,
                metadata: schema.metadata
            });
        });
        jqXHR.fail(function(e){
            deferred.reject(e);
        });
        return deferred.promise();
    };

    my.query = function(queryObj, dataset){
        var deferred, jqXHR, params = {};
        deferred = $.Deferred();
        // query params
        var queryParam = {'$and': []};
        if(queryObj.q){
            // @todo: need to know the list of fields to query
            /*
            var qParam = {$or: []};
            _.each(this._fields, function(field){
                var reParam = {};
                if(field.searchable){
                    reParam[field.id] = {$regex: queryObj.q, $options: "i"};
                    qParam['$or'].push(reParam);
                }
            });
            //params['query'] = JSON.stringify(qParam);
            queryParam['$and'].push(qParam);
            */
        }
        // filters
        if(queryObj.filters.length > 0)
        {
            var filterParam = {$and: []};
            _.each(queryObj.filters, function(filter){
                if(filter.type === "term" || filter.type === "select_one")
                {
                    var filterObj = {};
                    filterObj[filter.field] ={$regex: filter.term, $options: "i"};
                    filterParam.$and.push(filterObj);
                }
                else if(filter.type === "range")
                {
                    var filterObj = {};
                    filterObj[filter.field] = {$gte: filter.start, $lte: filter.stop};
                    filterParam.$and.push(filterObj);
                }
            });
            // make sure we have some filters before we add to our array
            if(filterParam.$and.length > 0)
            {
                queryParam['$and'].push(filterParam.$and.length > 1?filterParam:filterParam.$and[0]);
            }
        }
        if(queryParam.$and && queryParam.$and.length > 0)
        {
            params['query'] = queryParam.$and.length > 1?JSON.stringify(queryParam):JSON.stringify(queryParam.$and[0]);
        }
        // default sort
        var sort = {field: "_submission_time", order: "desc"};
        var sortDirs = {asc: 1, desc: -1};
        if(queryObj.sort && queryObj.sort.length > 0)
        {
            sort = queryObj.sort[0];
        }
        var sortParam = {};
        sortParam[sort.field] = sortDirs[sort.order];
        params['sort'] = JSON.stringify(sortParam);
        // do a count first
        params['count'] = 1;
        jqXHR = $.getJSON(dataset.dataUrl, params);
        jqXHR.done(function(data) {
            var total;
            total = data[0].count;
            // stop counting
            delete(params.count);
            // todo: check for fields
            if(queryObj.fields){

            }
            params.start = queryObj.from;
            params.limit = queryObj.size;
            jqXHR = $.getJSON(dataset.dataUrl, params);
            return jqXHR.done(function(data) {
                return deferred.resolve({
                    total: total,
                    hits: data
                });
            });
        });
        jqXHR.fail(function(e) {
            return deferred.reject(e);
        });
        return deferred.promise();
    };
}(jQuery, this.recline.Backend.FormhubMongoAPI));