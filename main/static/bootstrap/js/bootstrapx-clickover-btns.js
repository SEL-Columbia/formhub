/* ==========================================================
 * bootstrapx-clickover-btns.js
 * https://github.com/lecar-red/bootstrapx-clickover
 * version: 1.0
 * ==========================================================
 *
 * Based on https://github.com/lecar-red/bootstrapx-clickover
 * Create a popup that contains a bootstrap button group
 *
 * ========================================================== */
!function($) {
  "use strict"

  /* class definition */
  var ClickoverBtns = function ( element, options ) {
    // local init
    this.cinit('clickoverbtns', element, options );
  }

    ClickoverBtns.prototype = $.extend({}, $.fn.clickover.Constructor.prototype, {

    constructor: ClickoverBtns

    , cinit: function( type, element, options ) {
        this.attr = {};

        // choose random attrs instead of timestamp ones
        this.attr.me = ((Math.random() * 10) + "").replace(/\D/g, '');
        this.attr.click_event_ns = "click." + this.attr.me;

        if (!options) options = {};

        options.trigger = 'manual';

        // call parent
        this.init( type, element, options );

        // setup our own handlers
        this.$element.on( 'mouseenter', this.options.selector, $.proxy(this.clickery, this) );

        // soon add click hanlder to body to close this element
        // will need custom handler inside here
    }

    ,show: function () {
        var $tip
            , inside
            , pos
            , actualWidth
            , actualHeight
            , placement
            , tp

        if (this.hasContent() && this.enabled) {
            $tip = this.tip()
            this.setContent()

            if (this.options.animation) {
                $tip.addClass('fade')
            }

            placement = typeof this.options.placement == 'function' ?
                this.options.placement.call(this, $tip[0], this.$element[0]) :
                this.options.placement

            inside = /in/.test(placement)

            $tip.css({ display: 'block' })

            pos = this.getPosition(inside)

            actualWidth = $tip[0].offsetWidth
            actualHeight = $tip[0].offsetHeight

            switch (inside ? placement.split(' ')[1] : placement) {
                case 'bottom':
                    tp = {top: pos.top + pos.height, left: pos.left + pos.width / 2 - actualWidth / 2}
                    break
                case 'top':
                    tp = {top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2}
                    break
                case 'left':
                    tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth}
                    break
                case 'right':
                    tp = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width}
                    break
            }

            $tip
                .css(tp)
                .addClass(placement)
                .addClass('in')
        }
    }

    ,setContent: function () {
        var $tip = this.tip()
        $tip.removeClass('fade in top bottom left right')
    }

    ,hide: function () {
        var that = this
            , $tip = this.tip()

        $tip.removeClass('in')

        function removeWithAnimation() {
            var timeout = setTimeout(function () {
                $tip.off($.support.transition.end).remove()
            }, 500)

            $tip.one($.support.transition.end, function () {
                clearTimeout(timeout)
                $tip.hide()
            })
        }

        $.support.transition && this.$tip.hasClass('fade') ?
            removeWithAnimation() :
            $tip.hide()
    }

    , getPosition: function (inside) {
        return $.extend({}, (inside ? {top: 0, left: 0} : this.$element.position()), {
            width: this.$element[0].offsetWidth
            , height: this.$element[0].offsetHeight
        })
    }

    ,tip: function () {
        return this.$tip = this.$tip || $(this.$element.data('targetSelector'))
    }
  })

  /* plugin definition */
  /* stolen from bootstrap tooltip.js */
  $.fn.clickoverbtns = function( option ) {
    return this.each(function() {
      var $this = $(this)
        , data = $this.data('clickover')
        , options = typeof option == 'object' && option

      if (!data) $this.data('clickover', (data = new ClickoverBtns(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.clickoverbtns.Constructor = ClickoverBtns

  // these defaults are passed directly to parent classes
  $.fn.clickoverbtns.defaults = $.extend({}, $.fn.clickover.defaults, {
    my_default: 'default'
  })

}( window.jQuery );

