var latlng = new google.maps.LatLng(center.lat, center.lng);
var map;
var defaultZoom = 8;
function initialize() {
    var myOptions = {
        zoom: defaultZoom,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    var open_window;
    var latLngArray = new Array();
    for (var i=0; i<points.length; i=i+1) {
        // use a self executing function to create a new scope in each
        // iteration of the loop.
        latLngArray.push((function(){
            var point = new google.maps.LatLng(points[i].lat, points[i].lng);
            // create a marker on the map for this point
            var marker = new google.maps.Marker({
                position: point,
                map: map
            });
            var instance = points[i].instance;

            // create an info window that opens this marker is clicked
            var infowindow = new google.maps.InfoWindow();
            google.maps.event.addListener(marker, 'click', function(){
                if (!!open_window) {
                    open_window.close();
                }
                // todo: remove hard coded url
                var url = "/odk_viewer/survey/" + instance.toString() + "/";
                $.get(url).done(function(data){
                    infowindow.setContent(data);
                });
                infowindow.open(map, marker);
                open_window = infowindow;
            });
            return point;
        })());
    }
    // fitting to bounds with one point will zoom too far
    if (latLngArray.length > 1) {
        var latlngbounds = new google.maps.LatLngBounds();
        for (var i=0; i<latLngArray.length; i++) {
            latlngbounds.extend(latLngArray[i]);
        }
        map.fitBounds(latlngbounds);
   }
}
