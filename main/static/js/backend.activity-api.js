this.recline = this.recline || {};
this.recline.Backend = this.recline.Backend || {};
this.recline.Backend.ActivityAPI = this.recline.Backend.ActivityAPI || {};

(function($, my) {
    my.__type__ = 'ActivityAPI';

    var fields = [
        {
            id: 'created_on',
            label: 'Performed On',
            type: 'datetime'
        },
        {
            id: 'action',
            label: 'Action',
            type: 'string'
        },
        {
            id: 'user',
            label: 'Performed By',
            type: 'string'
        },
        {
            id: 'msg',
            label: 'Description',
            type: 'string'
        }
    ];

    my.fetch = function(dataset){
        var deferred = $.Deferred();
        deferred.resolve({
            fields: fields
        });
        return deferred.promise();
    };

    my.query = function(queryObj, dataset){
        var deferred, jqXHR, params;
        deferred = $.Deferred();
        params = {
            count: 1
        };
        jqXHR = $.getJSON(dataset.url, params);
        jqXHR.done(function(data) {
            var total;
            total = data[0].count;
            params = {
                start: queryObj.from,
                limit: queryObj.size
            };
            // query params
            var queryParam = {'$and': []};
            if(queryObj.q){
                var qParam = {$or: []};
                _.each(fields, function(field){
                    var reParam = {};
                    reParam[field.id] = {$regex: queryObj.q, $options: "i"};
                    qParam['$or'].push(reParam);
                });
                //params['query'] = JSON.stringify(qParam);
                queryParam['$and'].push(qParam);
            }
            // filters
            if(queryObj.filters.length > 0)
            {
                var filterParam = {$and: []};
                _.each(queryObj.filters, function(filter){
                    if(filter.type === "term")
                    {
                        var filterObj = {};
                        filterObj[filter.field] = filter.term;
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
            var sort = {field: "created_on", order: "desc"};
            var sortDirs = {asc: 1, desc: -1};
            if(queryObj.sort && queryObj.sort.length > 0)
            {
                var sort = queryObj.sort[0];
            }
            var sortParam = {};
            sortParam[sort.field] = sortDirs[sort.order];
            params['sort'] = JSON.stringify(sortParam);
            jqXHR = $.getJSON(dataset.url, params);
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
}(jQuery, this.recline.Backend.ActivityAPI));