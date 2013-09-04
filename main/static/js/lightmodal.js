
function setMapHeight(){
    var newHeight = $(window).height()- $('.navbar-inner').height();
    $('#map_canvas').height(newHeight);
}

function formatLatLon(coordinates) {
    if (coordinates !== undefined && coordinates !== null) {
        var llstr = coordinates.toString();
        var lld = llstr.substr(7, llstr.length - 8).replace(" ", "").split(",");
        var lat = lld[0];
        var lng = lld[1];
        return lat + " " + lng;
    }
    return "";
}

function getiFrame(url, callback) {
    var aFrame = $('<iframe />');
    aFrame.attr('src', url);
    aFrame.attr('scrolling', 'yes');
    aFrame.attr('marginwidth', 0);
    aFrame.attr('marginheight', 0);
    aFrame.attr('frameborder', 0);
    aFrame.attr('vspace', 0);
    aFrame.attr('hspace', 0);
    // aFrame.load(callback);
    return aFrame;
}

function setupBlankModal(elem_cls) {
    var container = $('#content_modal');
    container.attr('class', elem_cls);
    container.empty();
    var closeButton = $('<div class="close"/>');
    container.append(closeButton);
    return container;
}

function initializeModal(modal, easyClose) {
    if (easyClose !== true && easyClose !== false)
        easyClose = false;
    $(modal).easyModal({
        top: 20,
        autoOpen: false,
        overlayOpacity: 0.9,
        overlayColor: "#333",
        overlayClose: easyClose,
        closeOnEscape: easyClose});
}

function setupModalWithEnketo(enketo_url) {
    var container = setupBlankModal('add_submission_with');
    var iframe = getiFrame(enketo_url, function (e) {
        console.log("REDIRECTION");
    });
    container.append(iframe);
    initializeModal(container, false);
    container.trigger('openModal');
}

function addSubmissionAt(coordinates) {
    $.getJSON(enketoAddWithUrl, {coordinates: formatLatLon(coordinates)})
        .done(function (data){
            setupModalWithEnketo(data.edit_url);
        })
        .fail(function (err){
            console.log("Error getting enketo add url");
        });
}

function setupEnketoModal(enketo_url) {
    var container = setupBlankModal('edit_submission');
    var iframe = getiFrame(enketo_url, function (e) {
        console.log("REDIRECTION");
    });
    container.append(iframe);
    initializeModal(container, false);
    container.trigger('openModal');
}

function deleteData(idToDelete){
    $.post(deleteAPIUrl, {'id': idToDelete})
        .success(function(data){
            console.log("successfully deleted.")
        })
        .error(function(){
           alert("{% trans 'BAD REQUEST' %}");
        });
    $('.delete_modal').trigger("closeModal");
}

function requestDataDeletion(feature_id) {
    idToDelete = feature_id;
    var container = $('.delete_modal');

    var h3 = $('<h3/>');
    h3.html(gettext("Delete Confirmation"));
    container.append(h3);

    var confirm = $('<p/>');
    confirm.html(gettext("Are you sure you want to delete this record. If you are unsure about deleting this record press 'Cancel'."));
    container.append(confirm);

    var cancel_btn = $('<a href="#"/>');
    cancel_btn.addClass('btn');
    cancel_btn.click(function(){
        container.trigger("closeModal");
    });
    cancel_btn.html(gettext("Cancel"));
    container.append(cancel_btn);

    var confirm_btn = $('<a href="#"/>');
    confirm_btn.addClass('btn btn-danger');
    confirm_btn.click(function(){
        deleteData(feature_id);
    });
    confirm_btn.html(gettext("Delete"));
    container.append(confirm_btn);

    initializeModal(container, true);
    container.trigger("openModal");
}

function setupFeaturePopup(feature_id) {

    var container = setupBlankModal('edit_submission_popup');
    initializeModal(container, true);

    $.getJSON(mongoAPIUrl, {'query': '{"_id":' + feature_id + '}'})
    .done(function(data){
        var content;
        if(data.length > 0)
            content = JSONSurveyToHTML(data[0]);
        else
            content = $("<p>An unexpected error occurred</p>");
        // replace content in modal
        container = setupBlankModal('edit_submission_popup');
        container.append(content);

        // click on the Edit button
        $('button.edit-submission').click(function () {
            var data_id = $(this).data('id');
            var url = enketoEditUrl + data_id;
            container.trigger('closeModal');
            setupEnketoModal(url);
        });

        $('button.del-submission').click(function () {
            var data_id = $(this).data('id');
            container.trigger('closeModal');
            requestDataDeletion(data_id);
        });

        container.trigger('openModal');
    })
    .fail(function(err){
        console.log("Error getting data from mongo");
    });

}

function refreshMap() {
    return window.location.reload();
}
