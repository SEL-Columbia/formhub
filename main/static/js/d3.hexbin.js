/**
 * d3.layout.hexbin
 * 
 * by Zachary Forest Johnson
 * indiemaps.com/blog
 * 
 * 
 * hexbinning for javascript
 * requires Alex Tingle's hex.js and Mike Bostock's D3.js
 * 
 */

(function(){ 
	
if ( !d3.layout ) d3.layout = {};

d3.layout.hexbin = function()
{
	// set any constants here
	var xValuer = function(d){ return d.x; },
		yValuer = function(d){ return d.y; },
	 	xRanger = d3_layout_hexbinRange,
		yRanger = d3_layout_hexbinRange,
		hexI = null; // Distance between centres of adjacent hexes.
	
	/**
	 * @constructor
	 * @param data An array of 2d points
	 * 
	 * @returns An array of hex objects, with important properties, including data and pointString
	 * 
	 */
	function hexbin( data ) 
	{
		var xValues = data.map(xValuer, this),
			yValues = data.map(yValuer, this),
			xRange = xRanger.call(this, xValues ),
			yRange = yRanger.call(this, yValues );
			
		if ( !hexI )
		{
			hexI = ( ( xRange[1] - xRange[0] ) + ( yRange[1] - yRange[0] ) ) / 2 / 15;
		}
		
		var cols = Math.ceil( ( xRange[1] - xRange[0] ) / hexI + .5 ),
			rows = Math.ceil( ( yRange[1] - yRange[0] ) / (HEX.J * hexI) + .5 ),
			grid = new HEX.Grid( cols, rows ),
			hexset = [],
			i = j = -1,
			hex, d, pt;
			
		// now let's add all the hexes in the grid to the set
		while ( ++i < cols )
		{
			j = -1;
			while ( ++j < rows )
			{
				hex = grid.hex( i, j );
				hex.data = [];
				hex.points = d3_layout_hexbinGeneratePoints( hex, hexI, xRange[0], yRange[1] );
				hex.pointString = d3_layout_hexbinGeneratePointString( hex, hexI, xRange[0], yRange[1] );
				HEX.set_insert( hexset, hex );
			}
		}
		
		// bin data, ignoring points outside the x or y range
		i = -1;
		while ( ++i < data.length )
		{
			d = data[i];
			pt = new HEX.Point(
				// need to convert to the data space used by the hex grid
				( ( xValuer( d ) - xRange[0] ) + ( .5 * hexI ) ) / hexI,
				( ( yRange[1] - yValuer( d ) ) + ( .5 * hexI ) ) / hexI
			);
						
			hex = grid.hex( pt );
			hex.data.push( d );
		}		
		
		return hexset;
	}
	
	/*
	 * Specifies how to extract the _x_ or _horizontal_ value from the associated data. The default
	 * value function extracts the 'x' property of the data object.
	 */
	hexbin.xValue = function( xAccessor )
	{
		if (!arguments.length) return xValuer;
    	xValuer = xAccessor;
    	return hexbin;
	}
	
	/**
	 * Specifies how to extract the _y_ or _vertical_ value from the associated data. The default
  	 * value function extracts the 'y' property of the data object.
	 */
	hexbin.yValue = function( yAccessor )
	{
		if (!arguments.length) return yValuer;
    	yValuer = yAccessor;
    	return hexbin;
	}
	
	/**
	 * Specifies the horizontal range of the hexbins. Values outside the
	 * specified range
	 * will be ignored. The argument `x` may be specified either as a
	 * two-element array representing the minimum and maximum value of the
	 * range, or as a
	 * function that returns the range given the array of values and the
	 * current index `i`. The default range is the extent (minimum and
	 * maximum) of the
	 * xValues.
	 */
	hexbin.xRange = function( x )
	{
		if (!arguments.length) return xRanger;
		xRanger = d3.functor(x);
		return hexbin;
	}
	
	
	/**
	 * Specifies the vertical range of the hexbins. Values outside the specified range
	 * will be ignored. The argument `y` may be specified either as a two-element
	 * array representing the minimum and maximum value of the range, or as a
	 * function that returns the range given the array of values and the current
	 * index `i`. The default range is the extent (minimum and maximum) of the
	 * yValues.
	 */
	
	hexbin.yRange = function( y )
	{
		if (!arguments.length) return yRanger;
		yRanger = d3.functor(y);
		return hexbin;
	}
	
	/**
	 * Specifies the distance between centers of adjacent hexes. The default hexI is 
	 * null so you better set it.
	 */
	hexbin.hexI = function( i )
	{
		if (!arguments.length) return hexI;
		hexI = i;
		return hexbin;
	}

	return hexbin;
};

/**
 * identical to d3_layout_histogramRange function
 */
function d3_layout_hexbinRange(values) 
{
  return [d3.min(values), d3.max(values)];
}


function d3_layout_hexbinGeneratePoints( d, hexI, xMin, yMax )
{
	var dir = HEX.A, 
		pt = d.edge( dir ).start_point(), 
		x = xMin + ( pt.x * hexI - .5 * hexI ), 
		y = yMax - ( pt.y * hexI - .5 * hexI ),
		i = -1,
		pts = [ { x : x,  y : y } ];
		
	while ( ++i < HEX.DIRECTIONS.length )
	{
		dir = HEX.DIRECTIONS[ i ];
		pt = d.edge( dir ).end_point();
		x = xMin + ( pt.x * hexI - .5 * hexI );
		y = yMax - ( pt.y * hexI - .5 * hexI );
		
		pts.push( { x : x,  y : y } );
	}
	
	return pts;
}


function d3_layout_hexbinGeneratePointString( d, hexI, xMin, yMax )
{
	var dir = HEX.A, 
		pt = d.edge( dir ).start_point(), 
		x = xMin + ( pt.x * hexI - .5 * hexI ), 
		y = yMax - ( pt.y * hexI - .5 * hexI ),
		i = -1,
		pointString = x + ',' + y;
							
	// line to's
	while ( ++i < HEX.DIRECTIONS.length )
	{
		dir = HEX.DIRECTIONS[ i ];
		pt = d.edge( dir ).end_point();
		x = xMin + ( pt.x * hexI - .5 * hexI );
		y = yMax - ( pt.y * hexI - .5 * hexI );
		
		pointString += " " + x + ',' + y;
	}
	
	return pointString;
}
	
})();
