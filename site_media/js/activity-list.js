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
			var i = 0; l = this.length;
			for(;i<l;i++) {
				if(id==this[i].id) {
					return this[i];
				}
			}
		},
		filter: function(k, v){
			var subList = new _ActivityList([]);
			if($.type(v)=='string') {
				v=v.toLowerCase();
			}
			$(this).each(function(){
				if($.type(this[k])=='string') {
					if(this[k].toLowerCase()==v) {
						subList.addPoint(this);
					}
				} else {
					if(this[k]==v) {
						subList.addPoint(this)
					}
				}
			});
			return subList;
		},
		addPoint: function(point){
			if(point instanceof _ActivityPoint) {
				this.push(point)
			} else {
				this.push(new _ActivityPoint(point))
			}
		},
		addPoints: function(points){
			var _Sl = this;
			$(points).each(function(){_Sl.addPoint(this)})
            // DashboardDebug.listInfo(this);
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
				return null
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

	function _ActivityPoint(o){
		if(o instanceof _ActivityPoint) {return o}
		$.extend(this, o);
		if(this.gps && this.gps.district_id) {
			this.district_id=this.gps.district_id
		}
		if(this.datetime) {
		  this.processDateTime();
		}
		this.survey = this.survey_type; //can't pick a consistent name here...
		
	}
	_ActivityPoint.prototype = new Mappable();
	_ActivityPoint.prototype.district=function(){
		var result, district_id = this.district_id;
		if(this.district_id) {
			$(districts).each(function(){ if(this.id==district_id) {result = this} })
		}
		return result;
	}
	_ActivityPoint.prototype.processDateTime = function(){
	    this.dateObj = (function(dt){
	        var date = dt.split(" ")[0];
	        var time = dt.split(" ")[1];
	        var year = +(date.split("-")[0]);
	        var month = +(date.split("-")[1]);
	        var day = +(date.split("-")[2]);
	        var hour = +(time.split(":")[0]);
	        var minute = +(time.split(":")[1]);
	        return new Date(year, month-1, day, hour, minute);
	    })(this.datetime);
	    this.date = this.datetime.split(" ")[0]
	    this.time = this.datetime.split(" ")[0]
	}
	
	window.ActivityList = _ActivityList;
})(jQuery);

/*  WithActivityList is a structure that executes a callback in the context of a
-   the global "ActivityCaller" object, which has methods for handling the activity
-   data.
*/

(function($){
    var callbacks = [],
        alreadyCalledBack = false,
        activityCaller;
    function ActivityCaller(){
        if(!storage) {console.err("Storage object can't be found.");}
        
        if(!storage.exists('activity')){
          var url = "/data/activity/";
          $.getJSON(url, function(data){
              storage.set('activity_stamp', [data.stamp]);
              storage.set('activity', data.data);
              activityCaller.list = new ActivityList(data.data);
              window.__list = activityCaller.list;
              $(callbacks).each(function(){
                  this.call(activityCaller, activityCaller.list);
              });
              alreadyCalledBack=true;
          });
        } else if(storage.get('activity').length && storage.get('activity').length > 0) {
            this.list = new ActivityList(storage.get('activity'));
            window.__list = this.list;
            $(callbacks).each(function(){
                this.call(activityCaller, activityCaller.list);
            });
            alreadyCalledBack=true;
        } else {
            //temporary fix to the problem of no activities in the system.
            var url = "/data/activity/";
            $.getJSON(url, function(data){
                storage.set('activity_stamp', [data.stamp]);
                storage.set('activity', data.data);
                activityCaller.list = new ActivityList(data.data);
                window.__list = activityCaller.list;
                $(callbacks).each(function(){
                    this.call(activityCaller, activityCaller.list);
                });
                alreadyCalledBack=true;
            });
        }
    }
    ActivityCaller.prototype.list = false; //defaults to false to ensure ActivityList loaded
    
    function WithActivityList(cb){
        if(!activityCaller) {activityCaller = new ActivityCaller();}
        if(!alreadyCalledBack) {
            callbacks.push(cb);
        } else {
            cb.call(activityCaller, activityCaller.list);
        }
    }
    window.WithActivityList = WithActivityList;
})(jQuery);
