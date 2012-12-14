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