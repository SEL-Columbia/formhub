$(document).ready(function(){

    // table sort example
    // ==================

    $("#sortTableExample").tablesorter( { sortList: [[ 1, 0 ]] } )


    // add on logic
    // ============

    $('.add-on :checkbox').click(function () {
        if ($(this).attr('checked')) {
            $(this).parents('.add-on').addClass('active')
        } else {
            $(this).parents('.add-on').removeClass('active')
        }
    })

    // Copy code blocks in docs
    $(".copy-code").focus(function () {
        var el = this;
        // push select to event loop for chrome :{o
        setTimeout(function () { $(el).select(); }, 0);
    });


    // POSITION STATIC TWIPSIES
    // ========================

    $(window).bind( 'load resize', function () {
        $(".tooltips a").each(function () {
            $(this)
            .tooltip({
                live: false
                , placement: $(this).attr('title')
                , trigger: 'manual'
                , offset: 2
            })
            .tooltip('show')
        })
    })

    // CSRF Protection for AJAX
    // https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    $(document).ajaxSend(function(event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        function sameOrigin(url) {
            // url could be relative or scheme relative or absolute
            var host = document.location.host; // host + port
            var protocol = document.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        function safeMethod(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });
    // END CSRF Protection for AJAX
    // https://docs.djangoproject.com/en/dev/ref/contrib/csrf/

    // app main.show
    $('.bind-edit').click(function() {
        var btn = $(this);
        var type_id = '#' + $(this).data('id');
        btn.hide();
        $(type_id + '_save').show();
        $(type_id).removeAttr('disabled');
        return false;
    });

    $('.bind-save').click(function() {
        var saveBtn = $(this);
        var type = saveBtn.data('id');
        var type_id = '#' + type;
        var params = {};
        params[type] = $(type_id).val();
        $.post(saveBtn.data('url'), params, function (data) {
            saveBtn.hide();
            $(type_id + '_edit').show();
            $(type_id).attr('disabled', '');
        });
        return false;
    });

    $('.bind-save').prevAll('input[type="text"]').keypress(function(e) {   // an alternative to this specific binding would've been to
        var code = (e.keyCode ? e.keyCode : e.which);                      // link the action to form submission instead of the button
        if(code == 13) {                                                   // but it wouldn't work for the source form
            $(this).nextAll('.bind-save').click();                         // (which has multiple submit buttons)
            return false;
        }
    });

    $('.bind-add').click(function() {
        var addBtn = $(this);
        var type = addBtn.data('id');
        var type_id = '#' + type;
        var params = {};
        params[type] = $(type_id).val();
        // TODO handle multi-part post
        $.post(addBtn.data('url'), params, function (data) {
            $(type_id).val('');
        });
        return false;
    });

    setHrefFromSelect('#form-license')
    setHrefFromSelect('#data-license')

    //$('#new-form').tooltip({'placement': 'left'})

    $(function () {
        $("a[rel=tooltip]").tooltip({
            live: true,
            placement: 'top'
        })
    })
    $('.btn').tooltip();

    $("a[rel=popover]")
        .popover()
        .click(function(e) {
            e.preventDefault()
        })

    $("a[rel=clickover-btns]")
        .clickoverbtns({
            html: true,
            title: false,
            template: '<div class="popover"><div class="arrow"></div><div class="popover-inner"><div class="popover-content"><p></p></div></div></div>',
            content: function(){
                return '<a href=="#">Click Me</a>'
            }
        })
        .click(function(e) {
            e.preventDefault()
        })

    $(".modal form").submit(function(){
        $(this).parent(".modal").modal('hide');
    });
});

function setHrefFromSelect(id) {
    $(id).change(function() {
        var el = $(id + '_info');
        var val = $(this).val();
        if (val.substr(0,4) === 'http') {
            el.show();
            el.attr('href', val);
        } else
            el.hide();
    });
}

function privacyEdit(url, param) {
    $.post(url, {toggle_shared: param});
}

