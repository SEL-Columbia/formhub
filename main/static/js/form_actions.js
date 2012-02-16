var clone_xlsform = function (url, username, formid) {
    // send to server form owner and form id for cloning/copying
    $.post(url,
        {'username': username,
         'id_string': formid}, function(data){
        if(data.type == "success" || data.type == "error"){
            $('#mfeedback').html('<div class="alert-message"><a class="close" href="#">x</a><p>' + data.text+'</p></div>');
            $('#mfeedback').show();
            $('.alert-message').alert()
        }
    }, 'json');
};
