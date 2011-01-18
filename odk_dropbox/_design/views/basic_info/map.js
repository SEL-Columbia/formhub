function(doc) {
    emit(doc._id, (function(data){
        var geopoint = data.survey_data.geopoint.split(" ");
        return {
            survey_type: data.survey_type,
            image_url: data.survey_data.picture,
            district_id: null,
            gps: {lat: geopoint[0], lng: geopoint[1]},
            device_id: data.survey_data.device_id
        }
    })(doc.parsed_xml));
}