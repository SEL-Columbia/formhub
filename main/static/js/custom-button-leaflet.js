var layerButtonControl = function(markerLayer, hexLayer) {
    var control = new (L.Control.extend({
        options: { position: 'topright' },

        onAdd: function (map) {
            var container = L.DomUtil.create('div', 'layer-button-container');
            this._createButton('layer-markerButton', markerLayer, container);
            this._createButton('layer-hexbinButton', hexLayer, container);
            return container;
        },

        _createButton: function (className, fn, container) {
            var button = L.DomUtil.create('div', className, container);
            L.DomEvent
                .on(button, 'click', L.DomEvent.stopPropagation)
                .on(button, 'click', L.DomEvent.preventDefault)
                .on(button, 'click', fn)
                .on(button, 'dblclick', L.DomEvent.stopPropagation);
            return button;
        }

    }));

    return control;
};