function LoadCustomMarker(){
function CustomMarker(opt_options) {
  var options = opt_options || {};

  /**
   * @type {boolean}
   * @private
   */
  this.ready_ = false;

  /**
   * @type {boolean}
   * @private
   */
  this.dragging_ = false;

  if (opt_options['visible'] == undefined) {
    opt_options['visible'] = true;
  }

  if (opt_options['shadow'] == undefined) {
    opt_options['shadow'] = '7px -3px 5px rgba(88,88,88,0.7)';
  }

  if (opt_options['anchor'] == undefined) {
    opt_options['anchor'] = CustomMarkerPosition['BOTTOM'];
  }

  this.setValues(options);
}
CustomMarker.prototype = new google.maps.OverlayView();
window['CustomMarker'] = CustomMarker;


/**
 * Returns the current visibility state of the marker.
 *
 * @return {boolean} The visiblity of the marker.
 */
CustomMarker.prototype.getVisible = function() {
  return /** @type {boolean} */ (this.get('visible'));
};
CustomMarker.prototype['getVisible'] = CustomMarker.prototype.getVisible;


/**
 * Sets the visiblility state of the marker.
 *
 * @param {boolean} visible The visiblilty of the marker.
 */
CustomMarker.prototype.setVisible = function(visible) {
  this.set('visible', visible);
};
CustomMarker.prototype['setVisible'] = CustomMarker.prototype.setVisible;


/**
 *  The visible changed event.
 */
CustomMarker.prototype.visible_changed = function() {
  if (this.ready_) {
    this.markerWrapper_.style['display'] = this.getVisible() ? '' : 'none';
    this.draw();
  }
};
CustomMarker.prototype['visible_changed'] = CustomMarker.prototype.visible_changed;


/**
 * Sets the marker to be flat.
 *
 * @param {boolean} flat If the marker is to be flat or not.
 */
CustomMarker.prototype.setFlat = function(flat) {
  this.set('flat', !!flat);
};
CustomMarker.prototype['setFlat'] = CustomMarker.prototype.setFlat;


/**
 * If the makrer is flat or not.
 *
 * @return {boolean} True the marker is flat.
 */
CustomMarker.prototype.getFlat = function() {
  return /** @type {boolean} */ (this.get('flat'));
};
CustomMarker.prototype['getFlat'] = CustomMarker.prototype.getFlat;


/**
 * Get the width of the marker.
 *
 * @return {Number} The width of the marker.
 */
CustomMarker.prototype.getWidth = function() {
  return /** @type {Number} */ (this.get('width'));
};
CustomMarker.prototype['getWidth'] = CustomMarker.prototype.getWidth;


/**
 * Get the height of the marker.
 *
 * @return {Number} The height of the marker.
 */
CustomMarker.prototype.getHeight = function() {
  return /** @type {Number} */ (this.get('height'));
};
CustomMarker.prototype['getHeight'] = CustomMarker.prototype.getHeight;


/**
 * Sets the marker's box shadow.
 *
 * @param {string} shadow The box shadow to set.
 */
CustomMarker.prototype.setShadow = function(shadow) {
  this.set('shadow', shadow);
  this.flat_changed();
};
CustomMarker.prototype['setShadow'] = CustomMarker.prototype.setShadow;


/**
 * Gets the marker's box shadow.
 *
 * @return {string} The box shadow.
 */
CustomMarker.prototype.getShadow = function() {
  return /** @type {string} */ (this.get('shadow'));
};
CustomMarker.prototype['getShadow'] = CustomMarker.prototype.getShadow;


/**
 * Flat changed event.
 */
CustomMarker.prototype.flat_changed = function() {
  if (!this.ready_) {
    return;
  }

  this.markerWrapper_.style['boxShadow'] =
      this.markerWrapper_.style['webkitBoxShadow'] =
      this.markerWrapper_.style['MozBoxShadow'] =
      this.getFlat() ? '' : this.getShadow();
};
CustomMarker.prototype['flat_changed'] = CustomMarker.prototype.flat_changed;


/**
 * Sets the zIndex of the marker.
 *
 * @param {Number} index The index to set.
 */
CustomMarker.prototype.setZIndex = function(index) {
  this.set('zIndex', index);
};
CustomMarker.prototype['setZIndex'] = CustomMarker.prototype.setZIndex;


/**
 * Gets the zIndex of the marker.
 *
 * @return {Number} The zIndex of the marker.
 */
CustomMarker.prototype.getZIndex = function() {
  return /** @type {Number} */ (this.get('zIndex'));
};
CustomMarker.prototype['getZIndex'] = CustomMarker.prototype.getZIndex;


/**
 * zIndex changed event.
 */
CustomMarker.prototype.zIndex_changed = function() {
  if (this.getZIndex() && this.ready_) {
    this.markerWrapper_.style.zIndex = this.getZIndex();
  }
};
CustomMarker.prototype['zIndex_changed'] = CustomMarker.prototype.zIndex_changed;

/**
 * Whether the marker is draggable or not.
 *
 * @return {boolean} True if the marker is draggable.
 */
CustomMarker.prototype.getDraggable = function() {
  return /** @type {boolean} */ (this.get('draggable'));
};
CustomMarker.prototype['getDraggable'] = CustomMarker.prototype.getDraggable;


/**
 * Sets the marker to be draggable or not.
 *
 * @param {boolean} draggable If the marker is draggable or not.
 */
CustomMarker.prototype.setDraggable = function(draggable) {
  this.set('draggable', !!draggable);
};
CustomMarker.prototype['setDraggable'] = CustomMarker.prototype.setDraggable;


/**
 * Draggable property changed callback.
 */
CustomMarker.prototype.draggable_changed = function() {
  if (this.ready_) {
    if (this.getDraggable()) {
      this.addDragging_(this.markerWrapper_);
    } else {
      this.removeDragListeners_();
    }
  }
};
CustomMarker.prototype['draggable_changed'] =
    CustomMarker.prototype.draggable_changed;


/**
 * Gets the postiton of the marker.
 *
 * @return {google.maps.LatLng} The position of the marker.
 */
CustomMarker.prototype.getPosition = function() {
  return /** @type {google.maps.LatLng} */ (this.get('position'));
};
CustomMarker.prototype['getPosition'] = CustomMarker.prototype.getPosition;


/**
 * Sets the position of the marker.
 *
 * @param {google.maps.LatLng} position The position to set.
 */
CustomMarker.prototype.setPosition = function(position) {
  this.set('position', position);
};
CustomMarker.prototype['setPosition'] = CustomMarker.prototype.setPosition;


/**
 * Position changed event.
 */
CustomMarker.prototype.position_changed = function() {
  this.draw();
};
CustomMarker.prototype['position_changed'] =
    CustomMarker.prototype.position_changed;


/**
 * Gets the anchor.
 *
 * @return {google.maps.Size} The position of the anchor.
 */
CustomMarker.prototype.getAnchor = function() {
  return /** @type {google.maps.Size} */ (this.get('anchor'));
};
CustomMarker.prototype['getAnchor'] = CustomMarker.prototype.getAnchor;


/**
 * Sets the anchor.
 *
 * @param {CustomMarkerPosition|google.maps.Size} anchor The anchor to set.
 */
CustomMarker.prototype.setAnchor = function(anchor) {
  this.set('anchor', anchor);
};
CustomMarker.prototype['setAnchor'] = CustomMarker.prototype.setAnchor;


/**
 * Anchor changed event.
 */
CustomMarker.prototype.anchor_changed = function() {
  this.draw();
};
CustomMarker.prototype['anchor_changed'] = CustomMarker.prototype.anchor_changed;


/**
 * Converts a HTML string to a document fragment.
 *
 * @param {string} htmlString The HTML string to convert.
 * @return {Node} A HTML document fragment.
 * @private
 */
CustomMarker.prototype.htmlToDocumentFragment_ = function(htmlString) {
  var tempDiv = document.createElement('DIV');
  tempDiv.innerHTML = htmlString;
  if (tempDiv.childNodes.length == 1) {
    return /** @type {!Node} */ (tempDiv.removeChild(tempDiv.firstChild));
  } else {
    var fragment = document.createDocumentFragment();
    while (tempDiv.firstChild) {
      fragment.appendChild(tempDiv.firstChild);
    }
    return fragment;
  }
};


/**
 * Removes all children from the node.
 *
 * @param {Node} node The node to remove all children from.
 * @private
 */
CustomMarker.prototype.removeChildren_ = function(node) {
  if (!node) {
    return;
  }

  var child;
  while (child = node.firstChild) {
    node.removeChild(child);
  }
};


/**
 * Sets the content of the marker.
 *
 * @param {string|Node} content The content to set.
 */
CustomMarker.prototype.setContent = function(content) {
  this.set('content', content);
};
CustomMarker.prototype['setContent'] = CustomMarker.prototype.setContent;


/**
 * Get the content of the marker.
 *
 * @return {string|Node} The marker content.
 */
CustomMarker.prototype.getContent = function() {
  return /** @type {Node|string} */ (this.get('content'));
};
CustomMarker.prototype['getContent'] = CustomMarker.prototype.getContent;


/**
 * Sets the marker content and adds loading events to images
 */
CustomMarker.prototype.content_changed = function() {
  if (!this.markerContent_) {
    // Marker content area doesnt exist.
    return;
  }

  this.removeChildren_(this.markerContent_);
  var content = this.getContent();
  if (content) {
    if (typeof content == 'string') {
      content = content.replace(/^\s*([\S\s]*)\b\s*$/, '$1');
      content = this.htmlToDocumentFragment_(content);
    }
    this.markerContent_.appendChild(content);

    var that = this;
    var images = this.markerContent_.getElementsByTagName('IMG');
    for (var i = 0, image; image = images[i]; i++) {
      // By default, a browser lets a image be dragged outside of the browser,
      // so by calling preventDefault we stop this behaviour and allow the image
      // to be dragged around the map and now out of the browser and onto the
      // desktop.
      google.maps.event.addDomListener(image, 'mousedown', function(e) {
        if (that.getDraggable()) {
          if (e.preventDefault) {
            e.preventDefault();
          }
          e.returnValue = false;
        }
      });

      // Because we don't know the size of an image till it loads, add a
      // listener to the image load so the marker can resize and reposition
      // itself to be the correct height.
      google.maps.event.addDomListener(image, 'load', function() {
        that.draw();
      });
    }

    google.maps.event.trigger(this, 'domready');
  }

  if (this.ready_) {
    this.draw();
  }
};
CustomMarker.prototype['content_changed'] = CustomMarker.prototype.content_changed;

/**
 * Sets the cursor.
 *
 * @param {string} whichCursor What cursor to show.
 * @private
 */
CustomMarker.prototype.setCursor_ = function(whichCursor) {
  if (!this.ready_) {
    return;
  }

  var cursor = '';
  if (navigator.userAgent.indexOf('Gecko/') !== -1) {
    // Moz has some nice cursors :)
    if (whichCursor == 'dragging') {
      cursor = '-moz-grabbing';
    }

    if (whichCursor == 'dragready') {
      cursor = '-moz-grab';
    }

    if (whichCursor == 'draggable') {
      cursor = 'pointer';
    }
  } else {
    if (whichCursor == 'dragging' || whichCursor == 'dragready') {
      cursor = 'move';
    }

    if (whichCursor == 'draggable') {
      cursor = 'pointer';
    }
  }

  if (this.markerWrapper_.style.cursor != cursor) {
    this.markerWrapper_.style.cursor = cursor;
  }
};

/**
 * Start dragging.
 *
 * @param {Event} e The event.
 */
CustomMarker.prototype.startDrag = function(e) {
  if (!this.getDraggable()) {
    return;
  }

  if (!this.dragging_) {
    this.dragging_ = true;
    var map = this.getMap();
    this.mapDraggable_ = map.get('draggable');
    map.set('draggable', false);

    // Store the current mouse position
    this.mouseX_ = e.clientX;
    this.mouseY_ = e.clientY;

    this.setCursor_('dragready');

    // Stop the text from being selectable while being dragged
    this.markerWrapper_.style['MozUserSelect'] = 'none';
    this.markerWrapper_.style['KhtmlUserSelect'] = 'none';
    this.markerWrapper_.style['WebkitUserSelect'] = 'none';

    this.markerWrapper_['unselectable'] = 'on';
    this.markerWrapper_['onselectstart'] = function() {
      return false;
    };

    this.addDraggingListeners_();

    google.maps.event.trigger(this, 'dragstart');
  }
};


/**
 * Stop dragging.
 */
CustomMarker.prototype.stopDrag = function() {
  if (!this.getDraggable()) {
    return;
  }

  if (this.dragging_) {
    this.dragging_ = false;
    this.getMap().set('draggable', this.mapDraggable_);
    this.mouseX_ = this.mouseY_ = this.mapDraggable_ = null;

    // Allow the text to be selectable again
    this.markerWrapper_.style['MozUserSelect'] = '';
    this.markerWrapper_.style['KhtmlUserSelect'] = '';
    this.markerWrapper_.style['WebkitUserSelect'] = '';
    this.markerWrapper_['unselectable'] = 'off';
    this.markerWrapper_['onselectstart'] = function() {};

    this.removeDraggingListeners_();

    this.setCursor_('draggable');
    google.maps.event.trigger(this, 'dragend');

    this.draw();
  }
};


/**
 * Handles the drag event.
 *
 * @param {Event} e The event.
 */
CustomMarker.prototype.drag = function(e) {
  if (!this.getDraggable() || !this.dragging_) {
    // This object isn't draggable or we have stopped dragging
    this.stopDrag();
    return;
  }

  var dx = this.mouseX_ - e.clientX;
  var dy = this.mouseY_ - e.clientY;

  this.mouseX_ = e.clientX;
  this.mouseY_ = e.clientY;

  var left = parseInt(this.markerWrapper_.style['left'], 10) - dx;
  var top = parseInt(this.markerWrapper_.style['top'], 10) - dy;

  this.markerWrapper_.style['left'] = left + 'px';
  this.markerWrapper_.style['top'] = top + 'px';

  var offset = this.getOffset_();

  // Set the position property and adjust for the anchor offset
  var point = new google.maps.Point(left - offset.width, top - offset.height);
  var projection = this.getProjection();
  this.setPosition(projection.fromDivPixelToLatLng(point));

  this.setCursor_('dragging');
  google.maps.event.trigger(this, 'drag');
};


/**
 * Removes the drag listeners associated with the marker.
 *
 * @private
 */
CustomMarker.prototype.removeDragListeners_ = function() {
  if (this.draggableListener_) {
    google.maps.event.removeListener(this.draggableListener_);
    delete this.draggableListener_;
  }
  this.setCursor_('');
};


/**
 * Add dragability events to the marker.
 *
 * @param {Node} node The node to apply dragging to.
 * @private
 */
CustomMarker.prototype.addDragging_ = function(node) {
  if (!node) {
    return;
  }

  var that = this;
  this.draggableListener_ =
    google.maps.event.addDomListener(node, 'mousedown', function(e) {
      that.startDrag(e);
    });

  this.setCursor_('draggable');
};


/**
 * Add dragging listeners.
 *
 * @private
 */
CustomMarker.prototype.addDraggingListeners_ = function() {
  var that = this;
  if (this.markerWrapper_.setCapture) {
    this.markerWrapper_.setCapture(true);
    this.draggingListeners_ = [
      google.maps.event.addDomListener(this.markerWrapper_, 'mousemove', function(e) {
        that.drag(e);
      }, true),
      google.maps.event.addDomListener(this.markerWrapper_, 'mouseup', function() {
        that.stopDrag();
        that.markerWrapper_.releaseCapture();
      }, true)
    ];
  } else {
    this.draggingListeners_ = [
      google.maps.event.addDomListener(window, 'mousemove', function(e) {
        that.drag(e);
      }, true),
      google.maps.event.addDomListener(window, 'mouseup', function() {
        that.stopDrag();
      }, true)
    ];
  }
};


/**
 * Remove dragging listeners.
 *
 * @private
 */
CustomMarker.prototype.removeDraggingListeners_ = function() {
  if (this.draggingListeners_) {
    for (var i = 0, listener; listener = this.draggingListeners_[i]; i++) {
      google.maps.event.removeListener(listener);
    }
    this.draggingListeners_.length = 0;
  }
};


/**
 * Get the anchor offset.
 *
 * @return {google.maps.Size} The size offset.
 * @private
 */
CustomMarker.prototype.getOffset_ = function() {
  var anchor = this.getAnchor();
  if (typeof anchor == 'object') {
    return /** @type {google.maps.Size} */ (anchor);
  }

  var offset = new google.maps.Size(0, 0);
  if (!this.markerContent_) {
    return offset;
  }

  var width = this.markerContent_.offsetWidth;
  var height = this.markerContent_.offsetHeight;

  switch (anchor) {
   case CustomMarkerPosition['TOP_LEFT']:
     break;
   case CustomMarkerPosition['TOP']:
     offset.width = -width / 2;
     break;
   case CustomMarkerPosition['TOP_RIGHT']:
     offset.width = -width;
     break;
   case CustomMarkerPosition['LEFT']:
     offset.height = -height / 2;
     break;
   case CustomMarkerPosition['MIDDLE']:
     offset.width = -width / 2;
     offset.height = -height / 2;
     break;
   case CustomMarkerPosition['RIGHT']:
     offset.width = -width;
     offset.height = -height / 2;
     break;
   case CustomMarkerPosition['BOTTOM_LEFT']:
     offset.height = -height;
     break;
   case CustomMarkerPosition['BOTTOM']:
     offset.width = -width / 2;
     offset.height = -height;
     break;
   case CustomMarkerPosition['BOTTOM_RIGHT']:
     offset.width = -width;
     offset.height = -height;
     break;
  }

  return offset;
};


/**
 * Adding the marker to a map.
 * Implementing the interface.
 */
CustomMarker.prototype.onAdd = function() {
  if (!this.markerWrapper_) {
    this.markerWrapper_ = document.createElement('DIV');
    this.markerWrapper_.style['position'] = 'absolute';
  }

  if (this.getZIndex()) {
    this.markerWrapper_.style['zIndex'] = this.getZIndex();
  }

  this.markerWrapper_.style['display'] = this.getVisible() ? '' : 'none';

  if (!this.markerContent_) {
    this.markerContent_ = document.createElement('DIV');
    this.markerWrapper_.appendChild(this.markerContent_);

    var that = this;
    google.maps.event.addDomListener(this.markerContent_, 'click', function(e) {
      google.maps.event.trigger(that, 'click');
    });
    google.maps.event.addDomListener(this.markerContent_, 'mouseover', function(e) {
      google.maps.event.trigger(that, 'mouseover');
    });
    google.maps.event.addDomListener(this.markerContent_, 'mouseout', function(e) {
      google.maps.event.trigger(that, 'mouseout');
    });
  }

  this.ready_ = true;
  this.content_changed();
  this.flat_changed();
  this.draggable_changed();

  var panes = this.getPanes();
  if (panes) {
    panes.overlayImage.appendChild(this.markerWrapper_);
  }

  google.maps.event.trigger(this, 'ready');
};
CustomMarker.prototype['onAdd'] = CustomMarker.prototype.onAdd;


/**
 * Impelementing the interface.
 */
CustomMarker.prototype.draw = function() {
  if (!this.ready_ || this.dragging_) {
    return;
  }

  var projection = this.getProjection();

  if (!projection) {
    // The map projection is not ready yet so do nothing
    return;
  }

  var latLng = /** @type {google.maps.LatLng} */ (this.get('position'));
  var pos = projection.fromLatLngToDivPixel(latLng);

  var offset = this.getOffset_();
  this.markerWrapper_.style['top'] = (pos.y + offset.height) + 'px';
  this.markerWrapper_.style['left'] = (pos.x + offset.width) + 'px';

  var height = this.markerContent_.offsetHeight;
  var width = this.markerContent_.offsetWidth;

  if (width != this.get('width')) {
    this.set('width', width);
  }

  if (height != this.get('height')) {
    this.set('height', height);
  }
};
CustomMarker.prototype['draw'] = CustomMarker.prototype.draw;


/**
 * Removing a marker from the map.
 * Implementing the interface.
 */
CustomMarker.prototype.onRemove = function() {
  if (this.markerWrapper_ && this.markerWrapper_.parentNode) {
    this.markerWrapper_.parentNode.removeChild(this.markerWrapper_);
  }
  this.removeDragListeners_();
};
CustomMarker.prototype['onRemove'] = CustomMarker.prototype.onRemove;


/**
 * CustomMarker Anchor positions
 * @enum {number}
 */
var CustomMarkerPosition = {
  'TOP_LEFT': 1,
  'TOP': 2,
  'TOP_RIGHT': 3,
  'LEFT': 4,
  'MIDDLE': 5,
  'RIGHT': 6,
  'BOTTOM_LEFT': 7,
  'BOTTOM': 8,
  'BOTTOM_RIGHT': 9
};
window['CustomMarkerPosition'] = CustomMarkerPosition;
}