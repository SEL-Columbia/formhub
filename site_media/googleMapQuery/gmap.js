//Resize the map window...
$(function(){
    $(window).resize(function(){
        var mapBox = $('.map-tab'),
            offset, sh,
        	padding = 10;
        	
    	offset = mapBox.offset().top;
    	wh = $(window).height();
    	sh = wh - (offset + padding);
     	if(sh>100) {mapBox.css({'height':sh})}
    });
    $(function(){$(window).trigger('resize')})
})
