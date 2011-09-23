var latlng = new google.maps.LatLng(center.lat, center.lng);
function initialize() {
    var myOptions = {
        zoom: 8,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

    var open_window;
    for (var i=0; i<points.length; i=i+1) {
        // use a self executing function to create a new scope in each
        // iteration of the loop.
        (function(){
            var point = new google.maps.LatLng(points[i].lat, points[i].lng);
            // create a marker on the map for this point
            var marker = new google.maps.Marker({
                position: point,
                map: map, 
            });

            // create an info window that opens this marker is clicked
            var infowindow = new google.maps.InfoWindow({
                content: points[i].info
            });
            google.maps.event.addListener(marker, 'click', function(){
                if(!!open_window) {
                    open_window.close();
                }
                infowindow.open(map, marker);
                open_window = infowindow;
            });
        })()
    }
}
