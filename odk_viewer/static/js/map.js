// Leaflet shortcuts for common tile providers - is it worth adding such 1.5kb to Leaflet core?
// https://gist.github.com/mourner/1804938
L.TileLayer.Common = L.TileLayer.extend({
	initialize: function (options) {
		L.TileLayer.prototype.initialize.call(this, this.url, options);
	}
});

(function () {

	var osmAttr = '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>';

	L.TileLayer.CloudMade = L.TileLayer.Common.extend({
		url: 'http://{s}.tile.cloudmade.com/{key}/{styleId}/256/{z}/{x}/{y}.png',
		options: {
			attribution: 'Map data ' + osmAttr + ', Imagery &copy; <a href="http://cloudmade.com">CloudMade</a>',
			styleId: 997
		}
	});

	L.TileLayer.OpenStreetMap = L.TileLayer.Common.extend({
		url: 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
		options: {attribution: osmAttr}
	});

	L.TileLayer.OpenCycleMap = L.TileLayer.Common.extend({
		url: 'http://{s}.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png',
		options: {
			attribution: '&copy; OpenCycleMap, ' + 'Map data ' + osmAttr
		}
	});

	L.TileLayer.MapBox = L.TileLayer.Common.extend({
		url: 'https://{s}.tiles.mapbox.com/v3/{user}.{map}/{z}/{x}/{y}.png'
	});

}());

var FHMap = (function () {
    var map, layers_control;

    var defaults = {
        zoom: 8,
        center: [0, 0]
    };

    return {
        leaflet_map: map,

        init: function (el, options){
            options = _.extend(defaults, options)
            map = L.map(el, {
                zoom: options.zoom,
                center: options.center
            });

            layers_control = new L.Control.Layers();
            map.addControl(layers_control);
        },

        determineDefaultLayer: function(base_layers, language_code){
            var custom_layer = _.find(base_layers, function(layer){
               return layer.is_custom === true;
            });

            if(custom_layer)
            {
                custom_layer.is_default = true;
                return;
            }

            var lang_specific_layer = _.find(base_layers, function(layer){
               return layer.lang === language_code;
            });

            if(lang_specific_layer)
            {
                lang_specific_layer.is_default = true;
                return;
            }

            // were still here pick the first base layer as the default
            var first = _.findWhere(base_layers, {is_custom: false, lang: undefined});
            first.is_default = true;
        },

        addBaseLayer: function(layer, title, is_default){
            layers_control.addBaseLayer(layer, title);
            if(is_default !== undefined && is_default === true)
            {
                map.addLayer(layer);
            }
        },

        addForm: function(form_url, data_url){
            var form = new FHForm({}, {url: form_url});
            form.init();
            form.on('load', function(){
                // get lat/lng fields
                var geo_questions = form.questionsByType(FHForm.types.GEOLOCATION);
            });
        }
    }
})();