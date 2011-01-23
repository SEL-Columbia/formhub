function(doc) {
  var keys = 'device_id'.split(' ');
  // get sub dict of survey_data with keys
  var result = {};
  for(var i=0; i<keys.length; i++){
    result[keys[i]] = doc.parsed_xml.survey_data[keys[i]];
  }
  emit(doc._id, result);
}