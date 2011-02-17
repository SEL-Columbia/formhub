var ActivityList, ActivityPoint;
(function($){
	function _ActivityList(arr){
		if(arr){
			this.addPoints(arr)
		}
	}
	_ActivityList.prototype = new Array();
	$.extend(_ActivityList.prototype, {
		find: function(id){
			var i = 0, l=this.length;
			for(;i<l;i++) {
				if(id==this[i].id) {
					return this[i];
				}
			}
			return false;
		},
		filter: function(k, v){
			var subList = new _ActivityList([]);
			if($.type(v)=='string') {
				v=v.toLowerCase();
			}
			$(this).each(function(){
				if($.type(this[k])==='string') {
					if(this[k].toLowerCase()===v) {
						subList.addPoint(this);
					}
				} else {
					if(this[k]===v) {
						subList.addPoint(this)
					}
				}
			});
			return subList;
		},
		addPoint: function(point){
			this.push(new _ActivityPoint(point))
		},
		addPoints: function(points){
			var _Sl = this;
			$(points).each(function(){_Sl.addPoint(this)});
		},
		latLngWindow: function(){
			var lats = [], lngs = [];
			$.each(this, function(){
				if(this.gps && this.gps.lat) {
					lats.push(this.gps.lat);
					lngs.push(this.gps.lng);
				}
			});
			if(lats.length == 0 || lngs.length==0) {
				return null;
			}
			var llRange = {
				lat: {
					min: Math.min.apply(this, lats),
					max: Math.max.apply(this, lats)
				},
				lng: {
					min: Math.min.apply(this, lngs),
					max: Math.max.apply(this, lngs)
				}
			}
			llRange.lat.avg = (llRange.lat.min + llRange.lat.max)/2
			llRange.lng.avg = (llRange.lng.min + llRange.lng.max)/2
			return {
				lat: llRange.lat.avg,
				lng: llRange.lng.avg,
				range: llRange
			}
		},
		getVarieties: function(){
			var survey_types = [], dates = [], surveyors = [];
			$(this).each(function(){
				if(survey_types.indexOf(this.survey_type)==-1) { survey_types.push(this.survey_type); }
				if(dates.indexOf(this.date)==-1) { dates.push(this.date); }
				if(surveyors.indexOf(this.surveyor)==-1) { surveyors.push(this.surveyor); }
			});
			return {
				surveyor: surveyors,
				date: dates,
				survey: survey_types
			}
		}
	})

    var months = "Jan Feb Mar Apr May June July Aug Sept Oct Nov Dec".split(" ");
	function _ActivityPoint(o){
		if(o instanceof _ActivityPoint) {return o}
		this.id = o._id;
		this.survey_type = o._instance_doc_name;
		this.surveyor = o._surveyor_name;
		if(this.surveyor===null) {
		    this.surveyor = o.device_id;
		}

        this.image_url = "/survey/"+this.id+"/";
        
        if(o.geopoint) {
            this.gps = {
                'lat': o.geopoint.latitude,
                'lng': o.geopoint.longitude,
                'alt': o.geopoint.altitude,
                'acc': o.geopoint.accuracy
            }
        }
        
        this.district_id = o._district_id;
        if(o.start && o.start['$date']) {
            this.dateObj = new Date(o.start['$date']);
        }
        this.date = ""+this.dateObj.getDay()+"-"+months[this.dateObj.getMonth()]+"-"+(1900+this.dateObj.getYear());
        this.time = ""+this.dateObj.getHours()+":"+ (this.dateObj.getMinutes() < 10 ? "0" : "") + this.dateObj.getMinutes();
        this.datetime = this.time + "-" + this.date
        
		this.survey = this.survey_type; //can't pick a consistent name here...
	}
	_ActivityPoint.prototype = new Mappable();
    _ActivityPoint.prototype.mapPointListener = function(){
		var dest = $('<div />', {'class':'survey-content'});
		$.get(baseUrl+'survey/'+this.id+'/', function(data){
			dest.append(data);
		});
		MapPopup(dest);
    }
	_ActivityPoint.prototype.district=function(){
		var result, district_id = this.district_id;
		if(this.district_id) {
			$(districts).each(function(){ if(this.id==district_id) {result = this} })
		}
		return result;
	}
	window.ActivityList = _ActivityList;
})(jQuery);

/*  WithActivityList is a structure that executes a callback in the context of a
-   the global "ActivityCaller" object, which has methods for handling the activity
-   data.
*/
var cachedAt = false;
(function($){
    var dataUrl = baseUrl + "data/map_data/",
        callbacks = [],
        listCaller = {},
        activityList = [];
    
    function WithActivityList(cb, opts){
        if (Modernizr.localStorage) {
            if(!cachedAt) {
                callbacks.push(cb);
                $.retrieveJSON(dataUrl, function(data, status, cacheStatus){
                    cachedAt = cacheStatus;
                    if(cacheStatus && cacheStatus.retrievedAt) {
                        //bury
                    } else {
                        // storage.set('activity_stamp', [data.stamp]);
                        listCaller.list = new ActivityList(data);
                        window.__list = listCaller.list;
                        $(callbacks).each(function(){
                            this.call(listCaller, listCaller.list);
                        });
                        callbacks = [];
                    }
                });
            } else {
                cb.call(listCaller, listCaller.list);
            }
        } else {
            callbacks.push(cb);
            $.getJSON(dataUrl, function(data, status){
                listCaller.list = new ActivityList(data);
                window.__list = listCaller.list;
                $(callbacks).each(function(){
                    this.call(listCaller, listCaller.list);
                });
                callbacks = [];
            });
        }
    }
    window.WithActivityList = WithActivityList;
})(jQuery);
