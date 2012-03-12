var centerLatLng = new L.LatLng(center.lat, center.lng);
var map;
var defaultZoom = 8;

function initialize() {

    // mapbox streets formhub tiles
    var url = 'http://a.tiles.mapbox.com/v3/modilabs.map-hgm23qjf.jsonp';

    var mapMarkerIcon = L.Icon.extend({
	iconUrl: '/static/images/marker-solid-24.png',
	shadowUrl: null,
	iconSize: new L.Point(24, 24),
	shadowSize: null,
	iconAnchor: new L.Point(12, 24),
	popupAnchor: new L.Point(0,-24)
    });

    // Get metadata about the map from MapBox
    wax.tilejson(url,function(tilejson) {

	var mapboxstreet = new wax.leaf.connector(tilejson);          

      // Make a new Leaflet map in your container div
        var map = new L.Map('map_canvas')  // container's id="mapbox"
          
            .setView(centerLatLng, defaultZoom)

        // Add MapBox Streets as a base layer
	
            //.addLayer(new wax.leaf.connector(tilejson));      
	    .addLayer(mapboxstreet);

	//	var googleSat = new L.Google();
	//	map.addLayer(googleSat);

	map.addControl(new L.Control.Layers({'MapBox Streets':mapboxstreet}))

/*

Definetly the better way to do this is via GeoJSON in the future


// Define a geojson data layer
    var geojsonLayer = new L.GeoJSON(data, {
	pointToLayer: function (latlng) {
	    return new L.Marker(latlng, {
		icon: new mapMarkerIcon()
	    });
	}      
    });
*/


    var latLngArray = new Array();
    for (var i=0; i<points.length; i=i+1) {
        // use a self executing function to create a new scope in each
        // iteration of the loop.
        latLngArray.push((function(){

            var point = new L.LatLng(points[i].lat, points[i].lng);

	    // for marker
            //var marker = new L.CircleMarker(point, {
            //    'radius': 6 
            //});
	    var marker = new L.Marker(point, {icon: new mapMarkerIcon()});

            var instance = points[i].instance;

            // TODO: remove hard coded url
            var url = "/odk_viewer/survey/" + instance.toString() + "/";
            // open a loading popup so the user knows something is happening
            //a = marker.bindPopup('Loading...');//.openPopup();

           // bind open popup to marker's click event


            marker.on('click', function(e){
                var targetMarker = e.target;

		/*  for marker logic
                var popup = new L.Popup({
                    'maxWidth': 500,
                });
                latlng = e.latlng;
                latlng.lat += 1;
                popup.setLatLng(latlng);
		*/

 
               $.get(url).done(function(data){
		   targetMarker.bindPopup(data,{'maxWidth': 500}).openPopup();
		   // popup.setContent(data);
		   //  map.openPopup(popup);
                });
            });

            map.addLayer(marker);
            return point;
        })());
    }
    // fitting to bounds with one point will zoom too far
    if (latLngArray.length > 1) {
        var latlngbounds = new L.LatLngBounds(latLngArray);
        map.fitBounds(latlngbounds);
   }

    });
}
