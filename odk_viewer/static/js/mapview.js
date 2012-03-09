var centerLatlng = new L.LatLng(center.lat, center.lng);
var map;
var defaultZoom = 8;
function initialize() {
    map = new L.Map('map_canvas');
    var cloudmadeTileLayer = new L.TileLayer('http://{s}.tile.cloudmade.com/b1e5699de0e74928959c89bf0f777a5b/997/256/{z}/{x}/{y}.png', {
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
            var marker = new L.CircleMarker(point, {
                'radius': 8 
            });
            var instance = points[i].instance;

            // TODO: remove hard coded url
            var url = "/odk_viewer/survey/" + instance.toString() + "/";
            // open a loading popup so the user knows something is happening
            //a = marker.bindPopup('Loading...');//.openPopup();

            // bind open popup to marker's click event
            marker.on('click', function(e){
                var targetMarker = e.target;
                var popup = new L.Popup({
                    'maxWidth': 500,
                });
                latlng = e.latlng;
                latlng.lat += 1;
                popup.setLatLng(latlng);
                $.get(url).done(function(data){
                    popup.setContent(data);
                    map.openPopup(popup);
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
