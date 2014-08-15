/*                            Package   : libhex
 * hex.js                     Created   : 2007/12/02
 *                            Author    : Alex Tingle
 *
 *    Copyright (C) 2007-2008, Alex Tingle.
 *
 *    This file is part of the libhex application.
 *
 *    libhex is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    libhex is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

var HEX = {};


//
// Exceptions

HEX.exception = function(kind,message)
{
  this.kind=kind;
  this.message=message;
}

HEX.exception.prototype = {
  toString : function()
    {
      return this.kind + ": " + this.message;
    }
}

HEX.invalid_argument = function(message)
{
  return new HEX.exception('invalid_argument',message);
}

HEX.out_of_range = function(message)
{
  return new HEX.exception('out_of_range',message);
}


//
// Distance

HEX.M_SQRT3 =1.73205080756887729352744634150587236; // sqrt(3)
HEX.I =1.0;             ///< Distance between centres of adjacent hexes.
HEX.J =HEX.M_SQRT3/2.0; ///< Distance between adjacent hex rows.
HEX.K =1.0/HEX.M_SQRT3; ///< Length of hex's edge.

//
// Direction

HEX.A=0;
HEX.B=1;
HEX.C=2;
HEX.D=3;
HEX.E=4;
HEX.F=5;
HEX.DIRECTIONS =['A', 'B', 'C', 'D', 'E', 'F'];

HEX.to_direction = function(c)
{
  if(c.length!==1 || c<'A' || c>'F')
      throw HEX.invalid_argument("to_direction: "+c);
  return HEX[c];
}
HEX.to_char = function(d)
{
  if(d<0 || d>HEX.DIRECTIONS.length)
      throw HEX.invalid_argument("to_char: "+d);
  return HEX.DIRECTIONS[d];
}


// Direction arithmetic.

HEX.add = function(d,i)
{
  if(typeof d === 'string')
      d=HEX.to_direction(d);
  d= (d+i) % HEX.DIRECTIONS.length;
  while(d<0)
    d += HEX.DIRECTIONS.length;
  return d;
}
HEX.sub = function(d,i) { return HEX.add(d,-i); }
HEX.inc = function(d)   { return HEX.add(d,1);  }
HEX.dec = function(d)   { return HEX.add(d,-1); }


/** steps is a string of characters A-F, representing a set of Directions.
 *  This function rotates each step by i.
 *
 *  @param steps  String, sequence of direction letters A-Z
 *  @param i      integer, number of directions to rotate (anti-clockwise).
 *  @return       String, sequence of direction letters A-Z
 */
HEX.rotate = function(steps,i)
{
  // Rotate all letters A-F, but leave other characters alone.
  var result ='';
  for(var i=0, len=steps.length; i<len; i++)
  {
    var c =steps.charAt(i);
    if('A'<=c && c<='F')
    {
      d =HEX.to_direction(c);
      c =HEX.to_char(d+i);
    }
    result += c;
  }
  return result;
}

////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Point

/** X-Y coordinate class. String representation is "x,y", e.g. "1.2,3.4". */
HEX.Point = function(a,b)
{
  if(typeof a === 'string')
  {
    var piece =a.split(',');
    if(piece.length!==2)
      throw HEX.invalid_argument(a);
    this.i=parseFloat(piece[0]);
    this.j=parseFloat(piece[1]);
  }
  else
  {
    this.x = a? a: 0;
    this.y = b? b: 0;
  }
}

HEX.Point.prototype = {
  /** Return a new Point, translated by vector (dx,dy). */
  offset : function(dx,dy) { return new HEX.Point(this.x+dx, this.y+dy); },
  /** Return a new Point, translated by vector (p.x,p.y). */
  add : function(p) { return new HEX.Point(this.x+p.x, this.y+p.y); },
  sub : function(p) { return new HEX.Point(this.x-p.x, this.y-p.y); },
  mul : function(v) { return new HEX.Point(this.x*v, this.y*v); },
  div : function(v) { return new HEX.Point(this.x/v, this.y/v); },
  /** The string representation of a Point is "x,y" */
  toString : function() { return ''+this.x+','+this.y; }
};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Grid

/** A square field of hexagons that form the universe in which the other
 *  objects exist. */
HEX.Grid = function(cols,rows)
{
  if(0>cols || cols>=0x4000)
      throw HEX.out_of_range("cols");
  if(0>rows || rows>=0x4000)
      throw HEX.out_of_range("rows");
  this._hexes = {};
  this.cols = cols;
  this.rows = rows;
}

HEX.Grid.prototype = {

  to_area : function()
    {
      var hexes = [];
      for(var i=0; i<this.cols; ++i)
          for(var j=0; j<this.rows; ++j)
              hexes.push( this.hex(i,j) );
      HEX.uniq(hexes);
      return new HEX.Area(hexes);
    },

  // factory methods

  hex : function(a,b)
    {
      return new HEX.Hex(this,a,b);
    },

  /** Parse strings generated by set_str()
   *  @return  sorted Array of unique HEX.Hex objects */
  hexes : function(str)
    {
      var result = [];
      var piece =str.split(' ');
      for(var i=0, len=piece.length; i<len; ++i)
        result.push( this.hex(piece[i]) );
      HEX.uniq(result);
      return result;
    },

  /** Parse strings generated by Area::str()
   *  @return  object of type HEX.Area */
  area : function(str)
    {
      // Parse string of area fillpaths
      // E.g. 1_2>CDE:ABC
      var result = [];
      var pos =str.search(/[>:]/);
      if(pos<0)
          throw HEX.invalid_argument(str+' [1]');
      var origin =this.hex( str.substr(0,pos) );
      var start  =origin;
      while(pos>=0)
      {
        var next =this._str_find(str,/[>:]/,pos+1);
        var steps =str.substr( pos+1, (next<0)?(str.length):(next-pos-1) );
        if(str.charAt(pos)==='>')
        {
          start=origin.go(steps);
        }
        else // ':'
        {
          var path =new HEX.Path(start,steps);
          result = HEX.set_union(result,path.hexes);
          start=origin;
        }
        pos=next;
      }
      return new HEX.Area(result);
    },

  /** Parse strings generated by Path::str()
   *  @return  object of type HEX.Path */
  path : function(str)
    {
      var colon =str.indexOf(':');
      if(colon<=0 || (colon+1)>=str.length)
          throw HEX.invalid_argument(s);
      var origin =this.hex( str.substr(0,colon) );
      return new HEX.Path(origin,str.substr(colon+1));
    },

  // String utility
  
  /** Like String.indexOf, except it takes a regular expression. */
  _str_find : function(haystack,needle,start_pos)
    {
      var s =haystack.substr(start_pos);
      var pos =s.search(needle);
      if(pos<0)
        return pos;
      else
        return start_pos+pos;
    }

};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Edge

/** The interface between a hex and one of its six neighbours. Length K.
 * Each hex has its OWN set of edges, so each hex-hex interface has TWO edges-
 * one for each hex. */
HEX.Edge = function(hex,direction)
{
  this.hex=hex;
  this.direction=direction;
}

HEX.Edge.prototype = {

  /** @return the complementary edge. */
  complement : function()
    {
      var adjacent_hex =this.hex.go(this.direction);
      if(adjacent_hex)
          return adjacent_hex.edge(HEX.add(this.direction,3));
      else
          return null;
    },

  /** @return  TRUE if Edge v is next to this one. */
  is_next : function(v)
    {
      // TRUE iff: &v == next_in(T) || next_in(F) || next_out(T) || next_out(F)
      if( this.hex.valueOf() === v.hex.valueOf() )
      {
        return(  HEX.add(this.direction,1) === v.direction ||
                 HEX.sub(this.direction,1) === v.direction    );
      }
      else
      {
        var vv =v.valueOf();
        return(  vv === this.next_out(true ).valueOf() ||
                 vv === this.next_out(false).valueOf()    );
      }
    },

  /** @param clockwise  false [DEFAULT] - positive direction.
   *                    true - negative (clockwise) direction.
   *  @return  the next Edge object in *this* hex.
   */
  next_in : function(clockwise)
    {
      var one =(clockwise? -1: 1);
      return this.hex.edge( HEX.add(this.direction,one) );
    },

  /** @param clockwise  false [DEFAULT] - positive direction.
   *                    true - negative (clockwise) direction.
   *  @return  the next Edge object in *adjacent* hex.
   */
  next_out : function(clockwise)
    {
      var one =(clockwise? -1: 1);
      var c = this.hex.edge( HEX.add(this.direction,one) ).complement();
      if(c)
          return c.hex.edge( HEX.sub(this.direction,one) );
      else
          return null;
    },

  /** Helper function. Offsets Point p towards the start_point of edge in
   *  direction d.
   *  @return  new Point.
   */
  _corner_offset : function(p,d,bias)
    {
      var dx =0.0;
      var dy =0.0;
      switch(d)
      {
        case HEX.A: dx =  HEX.I/2.0; dy = -HEX.K/2.0; break;
        case HEX.B: dx =  HEX.I/2.0; dy =  HEX.K/2.0; break;
        case HEX.C: dx =        0.0; dy =  HEX.K    ; break;
        case HEX.D: dx = -HEX.I/2.0; dy =  HEX.K/2.0; break;
        case HEX.E: dx = -HEX.I/2.0; dy = -HEX.K/2.0; break;
        case HEX.F: dx =        0.0; dy = -HEX.K    ; break;
      }
      if(bias)
          return p.offset(dx*(1.0+bias),dy*(1.0+bias));
      else
          return p.offset(dx,dy);
    },

  /** @param bias       float [DEFAULT=1.0]
   *  @param clockwise  false [DEFAULT] - positive direction.
   *                    true - negative (clockwise) direction.
   *  @return  new Point
   */
  start_point : function(bias,clockwise)
    {
      var dir =HEX.add( this.direction, (clockwise?1:0) );
      return this._corner_offset( this.hex.centre(), dir, bias );
    },

  /** @param bias       float [DEFAULT=1.0]
   *  @param clockwise  false [DEFAULT] - positive direction.
   *                    true - negative (clockwise) direction.
   *  @return  new Point
   */
  end_point : function(bias,clockwise)
    {
      return this.start_point( bias, (clockwise? false: true) );
    },

  /** Calculate the point where two biased edged meet. This might be complicated
   *  if the two edged belong to different hexes.
   *  @param next  adjacent Edge object.
   *  @param bias  float [DEFAULT=1.0]
   *  @return  new Point
   */
  join_point : function(next,bias)
    {
      if(!bias || this.hex.valueOf()===next.hex.valueOf())
      {
        if(HEX.inc(this.direction) === next.direction)
            return this.end_point(bias);
        else
            return this.start_point(bias); // clockwise
      }
      else if(next.valueOf() === this.next_out().valueOf())
      {
        var p =this._corner_offset( this.hex.centre(), HEX.add(this.direction,2) );
        return this._corner_offset( p, this.direction, bias );
      }
      else // clockwise
      {
        var p =this._corner_offset( this.hex.centre(), HEX.dec(this.direction) );
        return this._corner_offset( p, HEX.inc(this.direction), bias );
      }
    },

  valueOf : function()
    {
      return this.hex.valueOf()*10 + this.direction;
    }
};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Hex

/** Hex location class.
 *
 *  Possible constructors:
 *    new HEX.Hex(i,j)            - i,j are hex's I & J indices.
 *    new HEX.Hex(new Point(x,y)) - x,y are cartesian coordinates
 *    new HEX.Hex(str)            - str is a string like '2_5'
 */
HEX.Hex = function(grid,a,b)
{
  if(typeof a === 'string')
  {
    var piece =a.split('_');
    if(piece.length!==2)
      throw HEX.invalid_argument("'HEX.Hex('"+a+"')");
    this.i=parseInt(piece[0],10);
    this.j=parseInt(piece[1],10);
  }
  else if(a instanceof HEX.Point)
  {
    this._set_from_point(a);
  }
  else
  {
    this.i=a;
    this.j=b;
  }
  // If the grid already contains this hex, then just return a ref.
  var key=this.valueOf();
  if(grid._hexes.hasOwnProperty(key))
      return grid._hexes[key];
  // else... check bounds.
  if(0>this.i || this.i>=grid.cols)
      throw HEX.out_of_range("i");
  if(0>this.j || this.j>=grid.rows)
      throw HEX.out_of_range("j");
  // Register this new Hex.
  grid._hexes[key] = this;
  this.grid = grid;
}

HEX.Hex.prototype = {

  /** Helper: set value from Point. */
  _set_from_point : function(p)
    {
      // (Note I==1.0, so the factor of I has been omitted.)
      var K_2 =HEX.K/2.0;
      // BI is unit vector in direction B
      var BIx = 0.5;
      var BIy = 1.5 * HEX.K;
      // CI is unit vector in direction C
      var CIx = -BIx;
      var CIy =  BIy;

      // Calculate the 'simple' solution.
      var x = p.x;
      var y = p.y - HEX.K;
      this.j = Math.round( y/HEX.J );
      if(this.j % 2)
          x -= 1.0; // odd rows
      else
          x -= 0.5; // even rows
      this.i = Math.round( x );                                     //   x / I
      // Now calculate the x,y offsets (in units of (I,J) )
      var dx = x - this.i;                                          //   i * I
      var dy = y - this.j * HEX.J;
      // Only need more work if |dy| > K/2
      if( dy < -K_2 || K_2 < dy )
      {
        var BId = (BIx * dx) + (BIy * dy);
        var CId = (CIx * dx) + (CIy * dy);

        if(      BId >  0.5 )
                              HEX.go( this, HEX.B );
        else if( BId < -0.5 )
                              HEX.go( this, HEX.E );
        else if( CId >  0.5 )
                              HEX.go( this, HEX.C );
        else if( CId < -0.5 )
                              HEX.go( this, HEX.F );
      }
    },

  /** Obtain this hex's Edge object in the given direction. */
  edge : function(direction)
    {
      return new HEX.Edge(this,direction);
    },

  /** Get the centre of this hex as a HEX.Point object. */
  centre : function()
    {
      var result = new HEX.Point();
      if(this.j % 2)
          result.x = HEX.I * (1 + this.i); // odd rows
      else 
          result.x = HEX.I/2.0 + HEX.I * this.i; // even rows
      result.y = HEX.K + HEX.J * this.j;
      return result;
    },

  /** Get a NEW HEX.Hex object, translated from this one by steps/distance. */
  go : function(steps, distance)
    {
      var pos ={ i:this.i, j:this.j };
      HEX.go(pos,steps,distance);
      try
      {
        return this.grid.hex( pos.i, pos.j );
      }
      catch(e) 
      {
	  	if ( e instanceof HEX.exception && e.kind=='out_of_range' )
        	return null;
      }
    },

  toString : function()
    {
      return ''+this.i+'_'+this.j;
    },

  valueOf : function()
    {
      return 0x4000*this.i + this.j + 1;
    }

};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Area

/** A connected set of hexes. */
HEX.Area = function(hexset)
{
  if(!(hexset instanceof Array))
    throw HEX.invalid_argument(hexset);
  this.hexes = hexset;
}

HEX.Area.prototype = {

  size     : function()  { return this.hexes.length; },
  contains : function(h) { return HEX.set_contains(this.hexes,h); },

  /** @return a HEX.Boundary for this area. */
  boundary : function()
    {
      // Start with a random hex.
      var h =this.hexes[0];
      var grid =h.grid;
      var i0 =h.i;
      var j0 =h.j;
      // Find an edge.
      var i=0;
      while(i<=i0 && !this.contains(grid.hex(i,j0)))
          ++i;
      var result =[]; // edges
      result.push( grid.hex(i,j0).edge(HEX.D) );
      // Follow the edge round.
      while(true)
      {
        var e =result[ result.length-1 ].next_out();
        if( !e || !this.contains(e.hex) )
            e = result[ result.length-1 ].next_in();
        if(e.valueOf() === result[0].valueOf())
            break;
        result.push(e);
      }
      return new HEX.Boundary(result);
    },

  enclosed_areas : function()
    {
      var a =this.boundary().area();
      return HEX.areas( HEX.set_difference( a.hexes, this.hexes ) );
    },

  /** For drawing the structure. If include_boundary is TRUE, then the
   *  last item in the list is the external boundary of the area.
   *
   *  @return  Array of Boundary objects.
   */
  skeleton : function(include_boundary)
    {
      var result =[];
      for(var h=0, len=this.hexes.length; h<len; ++h)
      {
        var edges =[];
        edges.push( this.hexes[h].edge(HEX.A) );
        edges.push( this.hexes[h].edge(HEX.B) );
        edges.push( this.hexes[h].edge(HEX.C) );
        result.push( new HEX.Boundary(edges) );
      }
      if(include_boundary)
          result.push(this.boundary());
      return result;
    },

  /** A list of one or more paths that include every hex in the area once. */
  fillpaths : function(origin)
    {
      var result = []; // list of Paths
      // Try to calculate a path that fills area.
      var queue =this.hexes.slice(0); // copy
      var seen = [];
      var path = [];
      var hex = origin? origin: queue[0];
      var dir = HEX.F;
      while(queue.length)
      {
        path.push( hex );
        HEX.set_erase(queue,hex);
        HEX.set_insert(seen,hex);
        var d=HEX.add(dir,1);
        while(true)
        {
          if(d===dir)
          {
            result.push( new HEX.Path(path) );
            path = [];
            hex = queue[0];
            break;
          }
          var hd =hex.go(d);
          if(HEX.set_contains(queue,hd) && !HEX.set_contains(seen,hd))
          {
            hex = hd;
            dir = HEX.add(d,3);
            break;
          }
          d=HEX.inc(d);
        }
      }
      return result;
    },

  toString : function(origin)
    {
      origin = origin? origin: this.hexes[0];
      var result = '';
      var paths  =this.fillpaths(origin);
      result += origin.toString();
      for(var p =0, len=paths.length; p<len; ++p)
      {
        if(paths[p].hexes[0].valueOf() !== origin.valueOf())
            result += ">" + HEX.steps(origin,paths[p].hexes[0]);
        result += ":" + paths[p].steps();
      }
      return result;
    },

  go : function(steps,distance)
    {
      var result = [];
      for(var h=0, len=this.hexes.length; h<len; ++i)
        result.push( this.hexes[h].go(steps,distance) );
      return new HEX.Area(result);
    }
};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Path

/** A sequence of adjacent hexes. */
HEX.Path = function(a,b)
{
  if(a instanceof Array)
  {
    this.hexes=a;
    return;
  }
  if(a instanceof HEX.Hex && b instanceof HEX.Hex)
  {
    b=HEX.steps(a,b);
  }
  if(a instanceof HEX.Hex && typeof b === 'string')
  {
    var steps=b;
    this.hexes=[a];
    var cur =0;
    while(cur<steps.length && steps.charAt(cur)!=='?')
    {
      // Find direction
      var dir =HEX.to_direction( steps.charAt(cur) );
      ++cur;
      var repeat =(cur<steps.length && steps.charAt(cur)==='*');
      do{
          var next =this.hexes[this.hexes.length-1].go( dir );
          if(next)
              this.hexes.push( next );
          else if(steps.charAt(steps.length-1)==='?' || repeat)
              return; // bail out instead of throwing
          else
              throw HEX.out_of_range('path:'+steps);
      } while(repeat);
    }
  }
  else
    throw HEX.invalid_argument('HEX.Path()');
}

HEX.Path.prototype = {

  to_area : function() { return new HEX.Area(this.hexes); },
  length  : function() { return this.hexes.length; }, ///< in units of I

  steps : function()
    {
      var result ='';
      var curr =0;
      for(var h=0, len=this.hexes.length; h<len; ++h)
      {
        if(curr)
            result += HEX.steps( curr, this.hexes[h] );
        curr = this.hexes[h];
      }
      return result;
    },
    
  toString : function()
    {
      var result =this.hexes[0].toString();
      result+=':'+this.steps();
      return result;
    }

};


////////////////////////////////////////////////////////////////////////////////
//
//  HEX.Boundary

/** A sequence of adjacent edges. */
HEX.Boundary = function(edges)
{
  this.edges=edges;
}

HEX.Boundary.prototype = {

  /** in units of K */
  length : function() { return this.edges.length; },

  /** @return  TRUE if this Boundary has no endpoints. */
  is_closed : function()
    {
      return( this.edges.length>2 &&
              this.edges[0].is_next( this.edges[ this.edges.length-1 ] ) );
    },

  /** @return  TRUE if this Boundary contains a finite area. */
  is_container : function()
    {
      if(this.is_closed())
      {
        try {
          var p1 =this.complement().to_path();
          var p0 =this.to_path();
          return( p0.length() < p1.length() );
        }
        catch(e) {
          // If is_closed AND there is no complement, then the boundary must
          // be at the very edge of the grid... it MUST be a container.
          if(e instanceof HEX.exception && e.kind==='out_of_range')
            return true;
        }
      }
      return false;
    },

  /** @return  object of type HEX.Boundary that traces this in reverse. */
  complement : function()
    {
      var result =[];
      for(var e=0, len=this.edges.length; e<len; ++e)
      {
        var c =this.edges[e].complement();
        if(c)
            result.push( c );
        else
            throw HEX.out_of_range("Boundary complement out of range.");
      }
      return new HEX.Boundary(result);
    },

  /** @return  a HEX.Path object that follows this Boundary. */
  to_path : function()
    {
      var result =[];
      var last =null;
      for(var e=0, len=this.edges.length; e<len; ++e)
        if( !last || this.edges[e].hex.valueOf() !== last )
        {
          result.push( this.edges[e].hex );
          last=this.edges[e].hex.valueOf();
        }
      return new HEX.Path(result);
    },

  /** @return  TRUE if this boundary is clockwise (normally FALSE). */
  clockwise : function()
    {
      // Boundaries usually go round in a positive (anti-clockwise) direction.
      if(this.edges.length > 1)
      {
        var e0 =this.edges[0];
        var e1 =this.edges[1];
        if(e0.valueOf()===e1.next_in().valueOf())
            return true;
        var e1_next_out =e1.next_out(); // May be null.
        return( e1_next_out && e0.valueOf()===e1_next_out.valueOf() );
      }
      return false;
    },

  toString : function()
    {
      var result =this.edges[0].hex.toString() + (this.clockwise()?"-":"+");
      for(var e=0, len=this.edges.length; e<len; ++e)
          result += HEX.to_char( this.edges[e].direction );
      return result;
    },

  /** Calculate the set of points required to draw this boundary.
   *
   *  @param bias  float [DEFAULT=1.0]
   *  @return      Array of HEX.Point objects
   */
  stroke : function(bias)
    {
      var result =[];
      var cw =this.clockwise();
      if(bias)
      {
        var last =null;
        for(var e=0, len=this.edges.length; e<len; ++e)
        {
          if(last)
              result.push( last.join_point(this.edges[e],bias) );
          last = this.edges[e];
        }
        if(this.is_closed())
        {
          var p =last.join_point(this.edges[0],bias);
          result.unshift( p );
          result.push( p );
        }
        else
        {
          result.unshift( this.edges[0].start_point(bias,cw) );
          result.push( last.end_point(bias,cw) );
        }
      }
      else
      {
        if(this.edges.length)
        {
          var e =0;
          result.push( this.edges[e].start_point(0.0,cw) );
          while(e<this.edges.length)
          {
            result.push( this.edges[e].end_point(0.0,cw) );
            ++e;
          }
        }
      }
      return result;
    },

  /** Returns the HEX.Area enclosed by the boundary.
   *  It is an error to call this function when is_closed()==false */
  area : function()
    {
      if(!this.is_closed())
      {
        alert('It is an error to call HEX.Boundary.area() when the boundary'+
              ' is not open.');
      }
      var beyond =[];
      var queue =[];
      for(var e=0, len=this.edges.length; e<len; ++e)
      {
        queue.push(  this.edges[e].hex );
        beyond.push( this.edges[e].hex.go( this.edges[e].direction ) );
      }
      HEX.uniq(beyond);
      HEX.uniq(queue);
      return HEX.fill(beyond,queue);
    }

};


////////////////////////////////////////////////////////////////////////////////
//
//  Algorithms


/** Translates hex along steps. (If steps is just one char, then it
 *  goes for distance hexes.)
 *
 *  @param pos       in/out object with properties i,j. *Not* a HEX.Hex object.
 *  @param steps     String, sequence of direction letters A-F
 *                   OR integer value HEX.A..HEX.F
 *  @param distance  optional integer in hexes (if steps is single-valued)
 */
HEX.go = function(pos, steps, distance)
{
  // Disallow fully constructed HEX.Hex objects.
  if(pos instanceof HEX.Hex && pos.hasOwnProperty('grid'))
      throw HEX.invalid_argument("HEX.go(hex,...)");
  if(typeof steps === 'number')
      steps=HEX.to_char(steps);
  if(steps.length>1 || !distance)
      distance = 1;

  for(var x=0; x<(distance?distance:1); x++)
  {
    for(var s=0, len=steps.length; s<len; ++s)
    {
      var c =steps.charAt(s);
      if('A'>c || c>'F')
          return;
      var direction=HEX.to_direction(c);
      if(pos.j%2)
          switch(direction) // odd
          {
            case HEX.A: ++pos.i;          break;
            case HEX.B: ++pos.i; ++pos.j; break;
            case HEX.C:          ++pos.j; break;
            case HEX.D: --pos.i;          break;
            case HEX.E:          --pos.j; break;
            case HEX.F: ++pos.i; --pos.j; break;
            default: throw HEX.invalid_argument('go: '+direction);
          }
      else
          switch(direction) // even
          {
            case HEX.A: ++pos.i;          break;
            case HEX.B:          ++pos.j; break;
            case HEX.C: --pos.i; ++pos.j; break;
            case HEX.D: --pos.i;          break;
            case HEX.E: --pos.i; --pos.j; break;
            case HEX.F:          --pos.j; break;
            default: throw HEX.invalid_argument('go: '+direction);
          }
    }
  }
}


/** Calculates a minimum-length path between two hexes.
 *  The result is one of many possible solutions.
 *
 *  @param from  object of type HEX.Hex
 *  @param to    object of type HEX.Hex
 *  @return      String, sequence of direction letters A-F
 */
HEX.steps = function(from,to)
{
  var result ='';
  var pos ={ i:from.i, j:from.j };
  var direction;
  while(true)
  {
    if( pos.j < to.j )                                          // go up
    {
        if(      pos.i < to.i )              direction = HEX.B;
        else if( pos.i > to.i || pos.j%2 )   direction = HEX.C;
        else                                 direction = HEX.B;
    }
    else if( pos.j > to.j )                                     // go down
    {
        if(      pos.i < to.i )              direction = HEX.F;
        else if( pos.i > to.i || pos.j%2 )   direction = HEX.E;
        else                                 direction = HEX.F;
    }
    else // pos.j == to.j                                       // go across
    {
        if(      pos.i < to.i )              direction = HEX.A;
        else if( pos.i > to.i )              direction = HEX.D;
        else                                 break;             //  Done!
    }
    result += HEX.to_char(direction);
    HEX.go(pos,direction);
  }
  return result;
}


/** The length of the shortest path between two hexes.
 *
 *  @param from  object of type HEX.Hex
 *  @param to    object of type HEX.Hex
 *  @return      integer distance (in hexes)
 */
HEX.distance = function(from,to)
{
  return HEX.steps(from,to).length;
}


/** Calculates the set of hexes that are range r from hex h.
 *  The result may NOT be a valid Area, since it may be cut into several
 *  pieces by the edge of the grid.
 *
 *  @param h         object of type HEX.Hex
 *  @param distance  integer range (in hexes)
 *  @return          Sorted Array of unique HEX.Hex objects
 */
HEX.range = function(h,distance)
{
  var result = [];
  if(distance<1)
  {
    result.push(h);
  }
  else
  {
    var pos={ i:h.i, j:h.j };

    try {
      HEX.go(pos,HEX.A,distance); // in/out: pos
      result.push( h.grid.hex(pos.i,pos.j) );
    } catch(e) {}
  
    for(var d=0; d<HEX.DIRECTIONS.length; ++d)
    {
      var direction =HEX.add(HEX.C,d);
      for(var count=0; count<distance; ++count)
          try {
            HEX.go(pos,direction); // in/out: pos
            result.push( h.grid.hex(pos.i,pos.j) );
          } catch(e) {}
    }
  }
  HEX.sort(result);
  return result;
}


/** Compare-by-value for sorting.
 *  null & undefined values are pushed to the end. */
HEX._cmp = function(a,b)
{
  // Push empty elements to the end.
  if(b===null || b===undefined) return -1; // [a,b]
  if(a===null || a===undefined) return 1;  // [b,a]
  // ...otherwise sort by value.
  return( a.valueOf() - b.valueOf() );
}


/** In-place sort an array by value, rather than by string.
 *  Moan: Who the hell thought it was a good idea for the default Javascript
 *  sort to be by string-representation?? */
HEX.sort = function(hex_array)
{
  hex_array.sort(HEX._cmp);
}


/** Ensures that hex_array is a sorted set of unique Hexes.
 *
 *  @param hex_array  in/out Array of HEX.Hex objects
 *  @return           !!NONE!! - hex_array is modified directly.
 */
HEX.uniq = function(hex_array)
{
  hex_array.sort(HEX._cmp);
  var new_length =hex_array.length;
  var curr =-1;
  for(var i=0, len=hex_array.length; i<len; ++i)
  {
    if(hex_array[i]===null || hex_array[i]===undefined ||
        curr.valueOf() === hex_array[i].valueOf())
    {
      delete hex_array[i];
      --new_length;
    }
    else
    {
      curr = hex_array[i];
    }
  }
  if(new_length!==len)
  {
    hex_array.sort(HEX._cmp); // pushes all empty elements to the end.
    hex_array.length = new_length;
  }
}


HEX.set_find = function(hexset,hex)
{
  // binary chop.
  var lower=0, upper=hexset.length-1;
  while(lower <= upper)
  {
    var pos=Math.floor((lower+upper)/2);
    if(hexset[pos] > hex)
      upper = pos - 1;
    else if(hexset[pos] < hex)
      lower = pos + 1;
    else
      return pos;
  }
  return -1;
}


HEX.set_contains = function(hexset,hex)
{
  return HEX.set_find(hexset,hex) >= 0;
}


/** Inserts Hex h into hex_array (and incidentally, turn it into a
 *  sorted unique set).
 *
 *  @param hex_array  in/out Array of HEX.Hex objects -> set
 *  @param h          HEX.Hex object
 *  @return           !!NONE!! - hex_array is modified directly.
 */
HEX.set_insert = function(hex_array,h)
{
  hex_array.push(h);
  HEX.uniq(hex_array);
}


/** Remove Hex h from hexset.
 *
 *  @param hexset  in/out Sorted Array of unique HEX.Hex objects
 *  @param h       HEX.Hex object
 *  @return        TRUE iff hexset contained h
 */
HEX.set_erase = function(hexset,h)
{
  var pos = HEX.set_find(hexset,h);
  if(pos>=0)
  {
    delete hexset[pos];
    hexset.sort(HEX._cmp);
    hexset.pop();
    return true;
  }
  return false;
}


/** The set difference between a and b.
 *
 *  @params  Sorted array of unique HEX.Hex objects
 *  @return  Sorted array of unique HEX.Hex objects
 */
HEX.set_difference = function(a,b)
{
  var result = [];
  for(var i=0, len=a.length; i<len; ++i)
    if(!HEX.set_contains(b,a[i]))
      result.push( a[i] );
  return result;
}


/** The set intersection between a and b.
 *
 *  @params  Sorted array of unique HEX.Hex objects
 *  @return  Sorted array of unique HEX.Hex objects
 */
HEX.set_intersection = function(a,b)
{
  var result = [];
  for(var i=0, len=a.length; i<len; ++i)
    if(HEX.set_contains(b,a[i]))
      result.push( a[i] );
  return result;
}


/** The set set_union between a and b.
 *
 *  @params  Array of HEX.Hex objects
 *  @return  Array of HEX.Hex objects
 */
HEX.set_union = function(a,b)
{
  var result =a.concat(b);
  HEX.uniq( result );
  return result;
}


/** Generates a string representation of hex-set a.
 *
 *  @param a  Array of HEX.Hex objects
 *  @return   string representation
 */
HEX.set_str = function(a)
{
  var result ='';
  for(var i=0, len=a.length; i<len; ++i)
    result += a[i].toString() + ' ';
  return result;
}


/** Max. area that contains hexes in a, but does not intersect beyond.
 *
 *  @param beyond  Array of HEX.Hex objects, that delimit the area to be filled.
 *  @param a       Array of HEX.Hex objects, that delimit the area to be filled.
 *                 OR a single HEX.Hex object.
 *  @return        HEX.Area object
 */
HEX.fill = function(beyond, a)
{
  if(a instanceof HEX.Hex)
    a = [a];

  var queue  = a.slice(0); // copy a
  var result = a.slice(0); // copy a
  while(queue.length)
  {
    var h = queue.shift();
    for(var d=0; d<HEX.DIRECTIONS.length; ++d)
    {
      var hd =h.go( HEX.add(HEX.A,d) );
      if(!HEX.set_contains(beyond,hd) && !HEX.set_contains(result,hd))
      {
        HEX.set_insert(queue,hd);
        HEX.set_insert(result,hd);
      }
    }
  }
  return new HEX.Area(result);
}


/** Helper: Find the connected set (Area) that contains the first hex in s. */
HEX._extract_connected_set = function(s)
{
  var result = [];
  var queue  = []; // Hexes in result that have not yet been checked.
  var h = s[0]; // Just pick a random hex in s.
  while(true)
  {
    HEX.set_insert(result,h);
    HEX.set_erase(s,h);
    if(s.length===0)
        break; // optimisation - not strictly necessary.
    var range1 =HEX.set_intersection( s, HEX.range(h,1) );
    queue = HEX.set_union( queue, range1 );
    if(queue.length===0)
        break;
    h = queue.shift();
  }
  return result;
}


/** Find all of the Areas (connected sets) in s.
 *
 *  @param s  Sorted set of unique HEX.Hex objects.
 *  @return   Array of HEX.Area objects.
 */
HEX.areas = function(s)
{
  var unallocated = s.slice(0); // copy of s
  var result = [];
  while(unallocated.length>0)
  {
    var area =new HEX.Area( HEX._extract_connected_set(unallocated) );
    result.push( area );
  }
  return result;
}


/** TRUE iff s is connected.
 *
 *  @param s  Sorted set of unique HEX.Hex objects.
 *  @return   bool
 */
HEX.is_connected = function(s)
{
  var unallocated = s.slice(0);
  HEX._extract_connected_set( unallocated );
  return( unallocated.length===0 );
}
