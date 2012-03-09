var centerLatlng = new L.LatLng(center.lat, center.lng);
var map;
var defaultZoom = 8;
function initialize() {
    map = new L.Map('map_canvas');
    // todo: change cloudmade api key i.e. /398a...81/ to a modilabs one
    var cloudmadeTileLayer = new L.TileLayer('http://{s}.tile.cloudmade.com/398a8a41acd34d688dde441c60edfd81/997/256/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
        maxZoom: 18
    });
    map.setView(centerLatlng, defaultZoom).addLayer(cloudmadeTileLayer);
    var latLngArray = new Array();
    for (var i=0; i<points.length; i=i+1) {
        // use a self executing function to create a new scope in each
        // iteration of the loop.
        latLngArray.push((function(){
            // create a marker on the map for this point
            var point = new L.LatLng(points[i].lat, points[i].lng);
            var marker = new L.Marker(point);
            var instance = points[i].instance;

            // todo: remove hard coded url
            var url = "/odk_viewer/survey/" + instance.toString() + "/";
            // bind open popup to marker's click event
            marker.on('click', function(evt){
                var targetMarker = evt.target;
                // open a loading popup so the user knows something is happening
                targetMarker.bindPopup('Loading...').openPopup();
                $.get(url).done(function(data){
                    targetMarker.bindPopup(data).openPopup();
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
}
