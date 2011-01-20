(function($){
    var PrintableArray = function(arr){
        if(arr && $.type(arr)=='array'){ var j = new PrintableArray(); for(var z in arr) { j.push(arr[z]); }; return j; }
    };
    PrintableArray.prototype = new Array();
    PrintableArray.prototype.toString = function(){
        if(this.length==2) {
            return "<p><b>"+this[0]+"</b>: "+this[1]+"</p>";
        }
        return this.join("");
    };
    
    function Json2Array(data) {
        var val = new PrintableArray;
        $.each(data, function(k, v){
            if($.type(v)=='object') {
                var tv = new PrintableArray;
                tv.push(k);
                tv.push(Json2Array(v));
                val.push(tv);
            } else {
                val.push(new PrintableArray([k, v]))
            }
        });
        return val
    }
    
    function Json2Table(data) {
        var table = $("<table />");
        var arrayData = Json2Array(data);
        var tr, thd, td, dest;
        function array2Table(arrayData, table) {
            $(arrayData).each(function(){
                tr = $("<tr />").html($("<td />", {'class':String(this[0]), rowspan: this[1].length}).html(String(this[0])));
                $(this[1]).each(function(i){
                    dest = (i==0) ? tr : $("<tr />");
                    $(this).each(function(){
                        dest.append($("<td />", {'class':String(this)}).html(String(this)))
                    })
                    table.append(dest);
                })
            })
        }
        array2Table(arrayData, table);
        return table;
    }
    
//    $.json2array = Json2Array;
    $.json2table = Json2Table;
})(jQuery)
