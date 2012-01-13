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


  // Disable certain links in docs
  // =============================
  // Please do not carry these styles over to your projects, it's merely here to prevent button clicks form taking you away from your spot on page

  $('ul.tabs a, ul.pills a, .pagination a, .well .btn, .actions .btn, .alert-message .btn, a.close').click(function (e) {
    e.preventDefault()
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
    $(".twipsies a").each(function () {
       $(this)
        .twipsy({
          live: false
        , placement: $(this).attr('title')
        , trigger: 'manual'
        , offset: 2
        })
        .twipsy('show')
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

// main.show
    bindEditPost('title');
    bindEditPost('description');
});

function bindEditPost(type) {
  $('#' + type + '_edit').click(function() {
    var btn = $(this);
    var type_id = '#' + $(this).data('id');
    btn.hide();
    $(type_id + '_save').show();
    $(type_id).removeAttr('disabled');
    return false;
  });

  $('#' + type + '_save').click(function() {
    var saveBtn = $(this);
    var type_id = '#' + saveBtn.data('id');
    var params = {};
    params[type] = $(type_id).val();
    $.post(saveBtn.data('url'), params, function (data) {
      saveBtn.hide();
      $(type_id + '_edit').show();
      $(type_id).attr('disabled', '');
    })
    return false;
  });
}

function privacyEdit(url, param) {
  $.post(url, {toggle_shared: param});
}


