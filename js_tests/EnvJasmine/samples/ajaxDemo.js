// This is the contents of ajaxDemo.js, the file to test.
var TwitterWidget = {
    makeRequest: function() {
        var self = this;
        
        $.ajax({
            method: "GET",
            url: "http://api.twitter.com/1/statuses/show/trevmex.json",
            datatype: "json",
            success: function (data) {
                self.addDataToDOM(data);
            }
        });
    },

    addDataToDOM: function(data) {
        // does something
        // We will mock this behavior with a spy.
        
        return data;
    }
};
