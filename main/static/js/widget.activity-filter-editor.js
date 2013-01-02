/*jshint multistr:true */

this.recline = this.recline || {};
this.recline.View = this.recline.View || {};

(function($, my) {

    my.ActivityFilterEditor = my.FilterEditor.extend({
        template: ' \
    <div class="filters"> \
      <h3>Filters</h3> \
      <a href="#" class="js-add-filter">Add filter</a> \
      <form class="form-stacked js-add" style="display: none;"> \
        <fieldset> \
          <label>Field</label> \
          <select class="fields"> \
            {{#fields}} \
            <option value="{{id}}">{{label}}</option> \
            {{/fields}} \
          </select> \
          <label>Filter type</label> \
          <select class="filterType"> \
            <option value="term">Value</option> \
            <option value="range">Range</option> \
            <option value="select_one">Options</option> \
            <option value="geo_distance">Geo distance</option> \
          </select> \
          <button type="submit" class="btn">Add</button> \
        </fieldset> \
      </form> \
      <form class="form-stacked js-edit"> \
        {{#filters}} \
          {{{filterRender}}} \
        {{/filters}} \
        {{#filters.length}} \
        <button type="submit" class="btn">Update</button> \
        {{/filters.length}} \
      </form> \
    </div> \
  ',
        filterTemplates: {
            term: ' \
      <div class="filter-{{type}} filter"> \
        <fieldset> \
          <legend> \
            {{field}} <small>{{type}}</small> \
            <a class="js-remove-filter" href="#" title="Remove this filter" data-filter-id="{{id}}">&times;</a> \
          </legend> \
          <input class="{{class}}" type="text" value="{{term}}" name="term" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
        </fieldset> \
      </div> \
    ',
            range: ' \
      <div class="filter-{{type}} filter"> \
        <fieldset> \
          <legend> \
            {{field}} <small>{{type}}</small> \
            <a class="js-remove-filter" href="#" title="Remove this filter" data-filter-id="{{id}}">&times;</a> \
          </legend> \
          <label class="control-label" for="">From</label> \
          <input class="{{class}}" type="text" value="{{start}}" name="start" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
          <label class="control-label" for="">To</label> \
          <input class="{{class}}" type="text" value="{{stop}}" name="stop" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
        </fieldset> \
      </div> \
    ',
            geo_distance: ' \
      <div class="filter-{{type}} filter"> \
        <fieldset> \
          <legend> \
            {{field}} <small>{{type}}</small> \
            <a class="js-remove-filter" href="#" title="Remove this filter" data-filter-id="{{id}}">&times;</a> \
          </legend> \
          <label class="control-label" for="">Longitude</label> \
          <input type="text" value="{{point.lon}}" name="lon" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
          <label class="control-label" for="">Latitude</label> \
          <input type="text" value="{{point.lat}}" name="lat" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
          <label class="control-label" for="">Distance (km)</label> \
          <input type="text" value="{{distance}}" name="distance" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}" /> \
        </fieldset> \
      </div> \
    ',
            select_one: '\
    <div class="filter-{{type}} filter"> \
        <fieldset> \
          <legend> \
            {{field}} <small>{{type}}</small> \
            <a class="js-remove-filter" href="#" title="Remove this filter" data-filter-id="{{id}}">&times;</a> \
          </legend> \
          <select name="term" data-filter-field="{{field}}" data-filter-id="{{id}}" data-filter-type="{{type}}">\
            {{#options}}\
            <option value="{{name}}" {{#selected}}selected{{/selected}}>{{name}}</option>\
            {{/options}}\
          </select>\
        </fieldset> \
      </div> \
    '
        },
        render: function() {
            var self = this;
            var tmplData = $.extend(true, {}, this.model.queryState.toJSON());
            // we will use idx in list as there id ...
            tmplData.filters = _.map(tmplData.filters, function(filter, idx) {
                filter.id = idx;
                return filter;
            });
            tmplData.fields = this.model.fields.toJSON();
            tmplData.filterRender = function() {
                return Mustache.render(self.filterTemplates[this.type], this);
            };
            var out = Mustache.render(this.template, tmplData);
            this.el.html(out);
            // bind datepicker
            $("form.js-edit input.datepicker").datepicker({
                format: 'yyyy-mm-ddThh:ii:ss'
            });
        },
        onAddFilter: function(e) {
            var self = this;
            e.preventDefault();
            var $target = $(e.target);
            $target.hide();
            var filterType = $target.find('select.filterType').val();
            var field      = $target.find('select.fields').val();
            var filter = {type: filterType, field: field};
            // check for options
            if(this.model.fields.get(field).has('options'))
            {
                filter.options = _.map(this.model.fields.get(field).get('options'), function(option){
                    return {name: option, selected: false};
                });
            }
            // check for datetime fields
            if(this.model.fields.get(field).get('type') == "date-time")
            {
                filter['class'] = 'datepicker';
            }
            this.model.queryState.addFilter(filter);
            // trigger render explicitly as queryState change will not be triggered (as blank value for filter)
            this.render();
        },
        onTermFiltersUpdate: function(e) {
            var self = this;
            e.preventDefault();
            var filters = self.model.queryState.get('filters');
            var $form = $(e.target);
            _.each($form.find('input, select'), function(input) {
                var $input = $(input);
                var filterType  = $input.attr('data-filter-type');
                var fieldId     = $input.attr('data-filter-field');
                var filterIndex = parseInt($input.attr('data-filter-id'));
                var name        = $input.attr('name');
                var value       = $input.val();

                switch (filterType) {
                    case 'term':
                        filters[filterIndex].term = value;
                        break;
                    case 'select_one':
                        filters[filterIndex].term = value;
                        _.each(filters[filterIndex].options, function(option, idx){
                           option.name==value?option.selected=true:option.selected=false;
                        });
                        break;
                    case 'range':
                        filters[filterIndex][name] = value;
                        break;
                    case 'geo_distance':
                        if(name === 'distance') {
                            filters[filterIndex].distance = parseFloat(value);
                        }
                        else {
                            filters[filterIndex].point[name] = parseFloat(value);
                        }
                        break;
                }
            });
            self.model.queryState.set({filters: filters});
            self.model.queryState.trigger('change');
        }
    });


})(jQuery, recline.View);