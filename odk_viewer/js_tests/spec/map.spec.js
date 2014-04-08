describe("Formhub Map", function () {

    /*var map_el;
     beforeEach(function(){
     $('body').append($('<div id="map"></div>'));
     });

     it("creates a map on init", function() {
     FHMap.init('map');
     });*/

    describe("determineDefaultLayer", function () {
        var predefined_layer_configs = [
            {label: 'Mapbox Streets', user: 'modilabs', map: 'map-iuetkf9u'},
            {label: 'MapBox Streets Light', user: 'modilabs', map: 'map-p543gvbh'},
            {label: 'MapBox Streets Zenburn', user: 'modilabs', map: 'map-bjhr55gf'},
            {label: 'Cloudless Earth', user: 'modilabs', map: 'map-aef58tqo'},
            {label: 'Mapbox Streets (Français)', user: 'modilabs', map: 'map-vdpjhtgz', lang: 'fr'},
            {label: 'Mapbox Streets (Español)', user: 'modilabs', map: 'map-5gjzjlah', lang: 'es'}
        ];
        var customMapBoxTileLayer = {
            url: 'http://a.tiles.mapbox.com/v3/modilabs.map-iuetkf9u.json',
            label: 'Mapbox Street Custom',
            attribution: '&copy; Me'
        };

        var base_layers = [];

        beforeEach(function () {
            base_layers = [];
            predefined_layer_configs.forEach(function (layer_config) {
                var layer = new L.TileLayer.MapBox({user: layer_config.user, map: layer_config.map});
                base_layers.push({
                    title: layer_config.label,
                    layer: layer,
                    lang: layer_config.lang,
                    is_custom: false
                });
            });
        });

        it("sets the custom layer as the default if its defined", function () {
            // add the custom layer
            base_layers.push({
                title: customMapBoxTileLayer.label,
                layer: L.tileLayer(customMapBoxTileLayer.url, {attribution: customMapBoxTileLayer.attribution}),
                lang: customMapBoxTileLayer.lang,
                is_custom: true
            });
            FHMap.determineDefaultLayer(base_layers, 'en');
            var default_layer = _.find(base_layers, function (layer) {
                return layer.is_default === true;
            });
            expect(default_layer).toBeDefined();
            expect(default_layer.title).toEqual(customMapBoxTileLayer.label);
        });

        it("sets the layer matching the language code as the default if no custom layer is defined", function () {
            FHMap.determineDefaultLayer(base_layers, 'fr');
            var default_layer = _.find(base_layers, function (layer) {
                return layer.is_default === true;
            });
            expect(default_layer).toBeDefined();
            expect(default_layer.title).toEqual('Mapbox Streets (Français)');
        });

        it("sets the first defined layer as the default if no custom or language layer is found", function () {
            FHMap.determineDefaultLayer(base_layers, 'en');
            var default_layer = _.find(base_layers, function (layer) {
                return layer.is_default === true;
            });
            expect(default_layer).toBeDefined();
            expect(default_layer.title).toEqual('Mapbox Streets');
        });
    });
});