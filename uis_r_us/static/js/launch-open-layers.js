var launchOpenLayers = (function(_opts){
    var scriptsStarted = false, scriptsFinished = false;
    var mapElem;
    var opts;
    var context = {};
    var loadingMessageElement = false;
    var defaultOpts = {
        elem: '#map',
        centroid: {
              lat: 0.000068698255561324,
              lng: 0.000083908685869343
        },
        olImgPath: "/static/openlayers/default/img/",
        tileUrl: "http://tilestream.openmangrove.org:8888/",
        layers: [
            ["Nigeria", "nigeria_base"]
        ],
        overlays: [],
        defaultLayer: 'google',
        layerSwitcher: true,
        loadingElem: false,
        loadingMessage: false,
        zoom: 6,
        maxExtent: [-20037500, -20037500, 20037500, 20037500],
        restrictedExtent: [-4783.9396188051, 463514.13943762, 1707405.4936624, 1625356.9691642]
    }
    var onScriptLoadFns = [];
    function loadScripts() {
        var openlayers = $.ajax({
            url: '/static/js/libs/OpenLayers.js',
            dataType: 'script',
            cache: false
        }).done(function(){
            $.ajax({
                url: '/static/js/libs/wax.ol.min.js',
                dataType: 'script',
                cache: false
                }).done(scriptsAreLoaded);
        });
        function scriptsAreLoaded(){
            if(!!loadingMessageElement) {
                loadingMessageElement.hide();
            }
            OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
            OpenLayers.ImgPath = opts.olImgPath;
            var ob = opts.maxExtent, re = opts.restrictedExtent;
            var options = {
                projection: new OpenLayers.Projection("EPSG:900913"),
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                units: "m",
                maxResolution: 156543.0339,
                restrictedExtent: new OpenLayers.Bounds(re[0], re[1], re[2], re[3]),
                maxExtent: new OpenLayers.Bounds(ob[0], ob[1], ob[2], ob[3])
              };
            var mapId = mapElem.get(0).id;
            var mapserver = opts.tileUrl;
            var mapLayerArray = [];
            var interactionArray = [];
            context.mapLayers = {};
            $.each(opts.overlays, function(k, ldata){
                var ml = new OpenLayers.Layer.TMS(ldata[0], [mapserver],
                    {
                        layername: ldata[1],
                        'type': 'png',
                        transparent: "true",
                        isBaseLayer: false
                    });
                mapLayerArray.push(ml);
                context.mapLayers[ldata[1]] = ml;
                });
            $.each(opts.layers, function(k, ldata){
                var ml = new OpenLayers.Layer.TMS(ldata[0], [mapserver],
                    {
                        layername: ldata[1],
                        'type': 'png'
                    });
                mapLayerArray.push(ml);
                context.mapLayers[ldata[1]] = ml;
                });
            $.each(opts.layers, function(k, ldata){
                if(ldata[2] != undefined && ldata[2] != '' && ldata[3] != undefined && ldata[3] != '') {
                    base_url = mapserver + '1.0.0/' + ldata[1] + '/{z}/{x}/{y}';
                    interaction = new wax.ol.Interaction({
                        tilejson: '1.0.0',
                        scheme: 'tms',
                        tiles: [base_url + '.png'],
                        grids: [base_url + '.grid.json'],
                        formatter: function(options, data) { log(data); return data; }
                        });
                    interactionArray.push(interaction);
                }
            });
            if(!mapId) {mapId = mapElem.get(0).id= "-openlayers-map-elem"}
            context.map = new OpenLayers.Map(mapId, options);
            var googleSat = new OpenLayers.Layer.Google( "Google", {type: 'satellite'});
            mapLayerArray.push(googleSat);
            context.map.addLayers(mapLayerArray);
            context.map.addControls(interactionArray);
            if(opts.defaultLayer==='google') {
                context.map.setBaseLayer(googleSat);
            }
            if(opts.layerSwitcher) {
                context.map.addControl(new OpenLayers.Control.LayerSwitcher());
            }
//            context.map.setCenter(new OpenLayers.LonLat(opts.centroid.lng, opts.centroid.lat), opts.zoom);
            $.each(onScriptLoadFns, function(i, fn){fn.call(context);})
            scriptsFinished = true;
        }
    }
    function loadGoogleMaps() {
        $('body').append($("<script />", {src: "http://maps.google.com/maps/api/js?sensor=false&callback=loadOpenLayers"}));
    }
    window.loadOpenLayers = loadScripts;
    
    function launch(_opts){
        if(typeof(_opts)==='function') {var passedCb = _opts; _opts = {}}
        if(opts===undefined) {opts = $.extend({}, defaultOpts, _opts);}
        if(mapElem===undefined) {mapElem = $(opts.elem);}
        if(!!opts.loadingElem && !!opts.loadingMessage) {
            loadingMessageElement = $(opts.loadingElem)
                .text(opts.loadingMessage)
                .show();
        }
        if(!scriptsStarted) { loadGoogleMaps(); scriptsStarted=true;}
        function cbExecuter(cb){
            if(typeof(cb)==='function'){if(!scriptsFinished) {onScriptLoadFns.push(cb)} else {cb.call(context);}
            }
        }
        if(passedCb!==undefined){cbExecuter(passedCb)}
        return cbExecuter;
    }
    return launch;
})(jQuery)

// var defaultLayers = [
//     ["Nigeria", "nigeria_base"],
//     ["Nigeria health workers per thousand people", "nigeria_healthworkers_per_thousand"],
//     ["Nigeria Health Facilities with Institutional Deliveries", "pct_healthfacilities_with_institutional_delivery"],
//     ["Nigeria No Stockouts of Bednets or Malaria Medicine", "nigeria_pct_no_bednet_malmeds_oneweek"],
//     ["Nigeria Classrooms That Need Repair", "nigeria_pct_classroom_need_repair"],
//     ["Nigeria classrooms with proportion student to teacher ratio > 40", "nigeria_prop_ratio_greater_than_40"],
//     ["Nigeria Immunization Rate", "nigearia_immunization_rate"],
//     ["Nigeria Under 5 Mortality Rate", "nigeria_under5_mortality_rate"],
//     ["Nigeria Child Wasting", "nigeria_wasting"],
//     ["Nigeria Child Health", "nigeria_child_health"],
//     ["Nigeria Child Nutrition", "nigeria_child_nutrition"],
//     ["Nigeria Maternal Health", "nigeria_maternal_health"],
//     ["Nigeria Primary Education Enrollment", "nigeria_primary_education_enrollment"]
//   ];
// 
// var LaunchOpenLayers = (function (wrapId, _opts) { 
//   var wrap = $('#'+wrapId);
//   var defaultOpts = {
//       centroid: {          
//           lat: 0.000068698255561324,
//           lng: 0.000083908685869343
//       },
//       centroidGoogleLatLng: false,
//       points: false,
//       latLngs: false,
//       boundingBox: false,
//       mapHeight: 475,
//       transparentIconOpacity: 0,
//       localTiles: false,
//       layerSelector: '#layer-select',
//       tileUrl: "http://tilestream.openmangrove.org:8888/",
//       tileCache: "http://localhost:8000/tiles/",
//       layers: defaultLayers,
//       zoom: 6
//   }
//   var opts = $.extend({}, defaultOpts, _opts);
// 
//   if(opts.centroidGoogleLatLng !== false) {
//       function convertDamnCentroid(fromCoord) {
//                 // convert standard lat long measurements to google projection
//                 //convert from EPSG:900913 to EPSG:4326
//                 var point = new OpenLayers.LonLat(fromCoord.lng, fromCoord.lat);
//                 return point.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
//         }
//       opts.centroid = convertDamnCentroid(opts.centroidGoogleLatLng);
//   }
//   wrap.css({'height':opts.mapHeight});
//   OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
//   
//   OpenLayers.ImgPath = "/static/openlayers/default/img/";
//   
//   map = new OpenLayers.Map(wrapId, options);
//   var mapserver = !!opts.localTiles ? 
//                     opts.tileCache : opts.tileUrl;
//                 
//   var mapLayers = $.map(opts.layers, function(ldata, i){
//       return new OpenLayers.Layer.TMS(ldata[0], [mapserver], 
//           {
//               layername: ldata[1],
//               'type': 'png'
//           });
//   });
//   if(typeof(google)!=='undefined') {
//         mapLayers.push(new OpenLayers.Layer.Google(
//             "Google Satellite",
//             {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
//             ));
//         mapLayers.push(new OpenLayers.Layer.Google(
//             "Google Physical",
//             {type: google.maps.MapTypeId.TERRAIN}
//             ));
//   }
// });
