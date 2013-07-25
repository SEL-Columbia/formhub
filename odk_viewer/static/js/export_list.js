var fhExportList =  (function(){
    var _progress_url
    var _bNothingToRefresh = false
    var _refreshAfter = 5000 // time to refresh after in ms

    return {
        init: function(progress_url, refreshAfter) {
            _progress_url = progress_url
            _refreshAfter = typeof refreshAfter !== 'undefined' ? refreshAfter : _refreshAfter
        },

        getAllComplete: function() {
            return _bNothingToRefresh
        },

        refreshExports: function(export_id) {
            var export_id = typeof export_id !== 'undefined' ? export_id : null
            var selector = 'a[class=refresh-export-progress]'
            var progress_elements, params
            var export_ids = []

            // set to true to 1. wait for a pending export to set to false and 2. prevent the refresh from running again till we're done
            _bNothingToRefresh = true

            /// if export_id is set refresh only the matching element else refresh all
            if(export_id)
                selector = 'a[data-export=' + export_id + ']'

            progress_elements = $(selector)

            /// lets see if we have any elements to process
            if(progress_elements.length > 0)
            {
                /// build array of export ids to pass to url
                _.each(progress_elements, function(item){
                    var anchor = $(item)
                    var parent = anchor.parent()
                    var statusElm = $(parent.children('span.status')[0])

                    // change classes so if a user manually refreshes, that export will not be auto-refreshed
                    anchor.removeClass('refresh-export-progress')
                    anchor.addClass('updating')
                    anchor.hide()
                    // set the status for each as refreshing
                    statusElm.html("Refreshing ...")

                    export_ids.push($(item).data('export'))
                })
                params = {'export_ids': export_ids}

                $.ajax({
                        url: _progress_url,
                        dataType: 'json',
                        data: params,
                        traditional: true // used to get jquery to send each id as a separate query as used by django
                    })
                    .success(function(data){
                        // foreach export_id update the status
                        _.each(data, function(status){
                            var anchor = $('a[class=updating]a[data-export=' + status.export_id +']')
                            var parent = anchor.parent()
                            var statusElm = $(parent.children('span.status')[0])

                            if(status.complete)
                            {
                                anchor.remove()
                                if(status.url)
                                {
                                    parent.empty()
                                    parent.append($('<a></a>').attr('href', status.url).html(status.filename))
                                }
                                else
                                {
                                    // empty url means complete but export failed
                                    parent.empty()
                                    // translate
                                    parent.append("Failed ...")
                                    if(status.error)
                                    {
                                      parent.append(status.message);
                                    }
                                }
                            }
                            else
                            {
                                // an export is not complete, reset to false
                                _bNothingToRefresh = false

                                statusElm.html("Pending ...")
                                anchor.addClass('refresh-export-progress')
                                anchor.removeClass('updating')
                                anchor.show()
                            }
                        })
                    })
                    .error(function(){
                        _.each(progress_elements, function(item){
                            var anchor = $(item)
                            var parent = anchor.parent()
                            var statusElm = $(parent.children('span.status')[0])

                            statusElm.html("Unexpected error ...")
                            anchor.addClass('refresh-export-progress')
                            anchor.removeClass('updating')
                            anchor.show()
                        })
                    })
            }
        },

        autoRefresh: function() {
            if(!_bNothingToRefresh)
            {
                fhExportList.refreshExports()
                setTimeout(fhExportList.autoRefresh, _refreshAfter)
            }
        }
    }
})();

$(document).ready(function(){
    fhExportList.init(progress_url, 8000);
    setTimeout(fhExportList.autoRefresh, 5000);

    $('a[data-role=refresh-export-progress]').click(function(evt){
        var anchor = $(this);

        evt.preventDefault();
        fhExportList.refreshExports(anchor.data('export'));
    });
});
