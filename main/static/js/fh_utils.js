var fhUtils =  (function(){
    return{
    }
})();

fhUtils.ObjectSize = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

/**
 * Convert a date-time string in the form "2012-04-30T13:58:15.746+03" to an
 * ISO string in the form 2012-04-30T13:58:15.746+03:00
 */
fhUtils.DateTimeToISOString = function(dateString)
{
    var matches = /(^.+?\.\d+\W\d{2}):*(\d*)/.exec(dateString);
    if(matches)
        // we now have 2012-04-30T13:58:15.746+03 and possibly 00 or blank
        return matches[1] + ':' + (matches[2]?matches[2]:'00');
    throw(dateString + " does not match format <YYYY-MM-DD>T<HH:MM.SSS><+/->HH[:SS]");
}