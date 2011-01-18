function(doc) {
  var results = {};
  (function(doc){
    this.survey_type = doc.parsed_xml.survey_type;
    this.image_url = doc.parsed_xml.survey_data.picture;
    this.district_id = null;
    var geopoint = doc.parsed_xml.survey_data.geopoint.split(" ");
    this.gps = {lat: geopoint[0], lng: geopoint[1]};
    this.device_id = doc.parsed_xml.survey_data.device_id;
  }).call(results, doc)
  emit(doc._id, results);
}