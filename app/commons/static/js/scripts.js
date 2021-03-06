// Because MS sucks...
if (navigator.userAgent.match(/IEMobile\/10\.0/)) {
  var msViewportStyle = document.createElement('style')
  msViewportStyle.appendChild(
    document.createTextNode(
      '@-ms-viewport{width:auto!important}'
    )
  )
  document.querySelector('head').appendChild(msViewportStyle)
}

function refresh_oembed(target) {
    target.find('a.oembed').oembed(null, {maxHeight:"400"});
    target.find('span.embedly').each(function (i, e) {
        e = $(e);
        var README = "Please, do NOT use this API key. You can get one too for free on http://embed.ly !";
        var url = "https://api.embed.ly/1/extract?key=396f02e230724c218db720b2dd2daed0&url="+e.attr('data-url');
        $.ajax(url).done(function (r) {
            if (r['images'] && r['images'][0] && r['images'][0]['url']) {
                e.append('<a href="'+ e.attr('data-url')+ '"><img src="'+r['images'][0]['url']+'"/></a>');
            } else {
                e.replaceWith('');
            }
        });
    });

}

function activate_tooltips(target) {
    if (!Modernizr.touch){
        $(target).find("[data-toggle='tooltip']").tooltip();
        $(target).find(".avatar[title]").tooltip();
    }
}

function replace_invalid_avatar(inside) {
    // Replace non-existent or empty avatars
    $(inside).find("img.avatar[src='']").each(function() {
      $(this).attr("src", "/static/images/avatars/default.png");
    });
    $(inside).find("img.avatar").error(function () {
     $(this).unbind("error").attr("src", "/static/images/avatars/erreur404.png"); });
}

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

function contrib_message(msg_type, msg_content) {
    $(".contrib-messages").append(nunjucks.render("commons/contrib_message.html", { type: msg_type, message: msg_content }));
}

$(document).ready(function() {
    // Add CSRF token for ajax calls
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (! (/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });
    // Replace empty or invalid avatar.
    replace_invalid_avatar($("body"));

    // Activate tooltips
    activate_tooltips($("body"));

    // Open navbar menu when hover, only if navbar is not collapsed
    $('#navbarA-collapse .dropdown-toggle').closest('li').hover(function(){
        if (! $('#navbarA-collapse').hasClass('in'))                
            $(this).addClass('open');
    }, function() {
        if (! $('#navbarA-collapse').hasClass('in')) 
            $(this).removeClass('open');
    });

    // Confirm dialog    
    $('.confirm-action').click(function (e) {
        e.preventDefault();
        $('#confirm-action').modal('show');
        $('#confirm-action #confirm-action-yes').attr('href', $(this).attr('href'));
    });

    // OEmbed-ed elements
    refresh_oembed($("body"));

    // Auto-hide navbar on scroll
    $(".navbar-fixed-top").autoHidingNavbar({showOnBottom: false});
});

