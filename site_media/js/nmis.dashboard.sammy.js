(function($) {
  Sammy = Sammy || {};
  Sammy.Title = function() {
    this.setTitle = function(title) {
      if (!$.isFunction(title)) {
        this.title_function = function(additional_title) {
          return [title, additional_title].join(' ');
        }
      } else {
        this.title_function = title;
      }
    };
    this.helper('title', function() {
      var new_title, 
            o_title = $.makeArray(arguments).join(' ');
      if (this.app.title_function) {
        new_title = this.app.title_function(new_title);
      }
      document.title = new_title;
      $('#page-title').text(o_title);
    });
  };
})(jQuery);



var urls = {
    activity: '#/activity',
    freqTables: '#/frequency-tables',
    map: '#/map'
}
var dashboard = (function($){
    $(function(){
        var menu = $('#menu .fwidth').empty();
        menu.append($('<li />').html($("<a />", {href:urls.activity}).html("Activity")))
        menu.append($('<li />').html($("<a />", {href:urls.freqTables}).html("Frequency Tables")))
        menu.append($('<li />').html($("<a />", {href:urls.map}).html("Map")))
    })
    
    var dashboard = $.sammy("#main-content", function(){
        this.use(Sammy.Title);
//        this.use('Storage');
//        var store = new Sammy.Store({name: 'mystore', element: '#element', type: 'local'});
        this.setTitle(function(title){
            return ["Baseline Data Collection: ", title].join("");
        })
//        this.store('mystore', {type: 'cookie'});
        this.get(urls.activity, function(context){
            context.app.swap('');
            context.$element().append("<h1>Activity</h1>");
            this.title("Activity");
//            console.log(this.store('mystore'));
        });
        this.get(urls.freqTables, function(context){
            context.app.swap('');
            context.$element().append("<h2>Frequency Tables</h1>");
            this.title("Frequency Tables");
        });
        this.get(urls.map, function(context){
            context.app.swap('');
            context.$element().append($('#map').html());
            this.title("Map");
        });
    });
    $(function(){
        dashboard.run();
    });
    return dashboard;
})(jQuery)
