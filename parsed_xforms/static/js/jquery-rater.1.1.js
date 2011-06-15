//jQuery Rater Plugin 1.1 Copyright 2008 Jarrett Vance http://jvance.com
$.fn.rater = function(options) {
    var opts = $.extend({}, $.fn.rater.defaults, options);
    return this.each(function() {
        var $this = $(this);
        var $on = $this.find('.ui-rater-starsOn');
        var $off = $this.find('.ui-rater-starsOff');
        if (opts.size == undefined) opts.size = $off.height();
        if (opts.rating == undefined) opts.rating = $on.width() / opts.size;
        if (opts.id == undefined) opts.id = $this.attr('id');

        $off.mousemove(function(e) {
            var left = e.clientX - $off.offset().left;
            var width = $off.width() - ($off.width() - left);
            width = Math.min(Math.ceil(width / (opts.size / opts.step)) * opts.size / opts.step, opts.size * opts.ratings.length)
            $on.width(width);
            var r = Math.round($on.width() / $off.width() * (opts.ratings.length * opts.step)) / opts.step;
            $this.attr('title', opts.ratings[r - 1] == undefined ? r : opts.ratings[r - 1]);
        }).hover(function(e) { $on.addClass('ui-rater-starsHover'); }, function(e) {
            $on.removeClass('ui-rater-starsHover'); $on.width(opts.rating * opts.size);
        }).click(function(e) {
            var r = Math.round($on.width() / $off.width() * (opts.ratings.length * opts.step)) / opts.step;
            $.fn.rater.rate($this, opts, r);
        }).css('cursor', 'pointer'); $on.css('cursor', 'pointer');
    });
};

$.fn.rater.defaults = {
    postHref: location.href,
    ratings: ['Bad', 'Boring', 'Average', 'Good', 'Great'],
    step: 1
};

$.fn.rater.rate = function($this, opts, rating) {
  var $on = $this.find('.ui-rater-starsOn');
  var $off = $this.find('.ui-rater-starsOff');
  $off.fadeTo(600, 0.4, function() {
    $.ajax({
      url: opts.postHref,
      type: "POST",
      data: 'id=' + opts.id + '&rating=' + rating,
      complete: function(req) {
        if (req.status == 200) { //success
          opts.rating = parseFloat(req.responseText);
          $off.unbind('click').unbind('mousemove').unbind('mouseenter').unbind('mouseleave');
          $off.css('cursor', 'default'); $on.css('cursor', 'default');
          $off.fadeTo(600, 0.1, function() {
            $on.removeClass('ui-rater-starsHover').width(opts.rating * opts.size);
            var $count = $this.find('.ui-rater-rateCount');
            if ($count) {
              $count.text(parseInt($count.text()) + 1);
              $this.find('.ui-rater-rating').text(opts.rating.toFixed(1));
            }
            $off.fadeTo(500, 1);
            $this.attr('title', 'Your rating: ' + rating.toFixed(1));
          });
        } else { //failure
          alert(req.responseText);
          $off.fadeTo(2200, 1);
        }
      }
    });
  });
};
