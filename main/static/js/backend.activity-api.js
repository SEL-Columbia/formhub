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