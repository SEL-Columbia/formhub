/*!   jQuery Plug-in: "buildIn"
-*    (author:Alex Dorey <http://github.com/dorey>)
-*   =========================
-*   > Based on the JSON syntax of indieinvader's htmlbuilder and JsonML.
-*   > Allows jQuery enabled pages to describe html in an array syntax
-*   > Defaults to using jQuery's "append" function, but can also use "prepend", "before", and "after"
-*   > Also allows "replace", which is equivalent to $(selector).innerHTML="<element tree />"
-*  
-*   Basic usage:
-*     $(selector).buildIn(<tagName>, <tagAttributes>, <elementContents>)
-*     example:
-*       $('body').buildIn('a', {href:'#simple'}, 'A link is easy to add!')
-*  
*/
;
(function($){
	function json2html(){
		if(arguments.length==1) {
			if(typeof(arguments[0])==='string') {return arguments[0] }
			if(arguments[0] instanceof Array) {return json2html.apply(this, arguments[0])}
			return "";
		}
		var tag = arguments[0],
			output="<" + tag;
		
		if (typeof(arguments[1])==='object' &&
		 	arguments[1] !== null) {
			$.each(arguments[1], function(k,v){
				output+=' '+k+'="'+v+'"';
			});
		}
		
		if(arguments.length<3) { //probably should use a better condition here
			return output+" />";
		}
		output+=">";

		for(var i=2;i<arguments.length; i++) {
			output+=json2html(arguments[i]);
		}
		output+="</"+tag+">";
		return output;
	}
	function json2dom(){
		return $(json2html.apply(this,arguments))
	}
	var jQueryInserters = /append|prepend|before|after|replace/i;
	function buildIn(){
		var args = arguments, action = 'append';
		if(typeof(arguments[0])==='string' && arguments[0].match(jQueryInserters)) {
			args = $(arguments).splice(1);
			action = arguments[0].match(jQueryInserters)[0].toLowerCase();
			if(action=='replace'){action='html';}
		}
		eval("this."+action+"(json2html.apply(this,args))");
	}
	$.json2html = json2html;
	$.json2dom = json2dom;
	$.fn.buildIn = buildIn;
})(jQuery);