/*jshint multistr:true */

this.recline = this.recline || {};
this.recline.View = this.recline.View || {};

(function($, my) {
    my.LanguageSelector = Backbone.View.extend({
        className: 'recline-filter-editor well',
        template: '\
        <div class="languages"> \
          <h3>Languages</h3> \
          <form class="form-stacked"> \
            <fieldset> \
              <label>Change Language</label> \
              <select class="lang-selector fields"> \
                {{#languages}} \
                <option value="{{id}}">{{label}}</option> \
                {{/languages}} \
              </select> \
            </fieldset> \
          </form> \
        </div>',
        events: {
            'change select.lang-selector': 'onChangeLanguage'
        },
        initialize: function() {
            this.el = $(this.el);
            _.bindAll(this, 'render');
            this.model.fields.bind('reset', this.render);
        },
        render: function() {
            var self = this;
            var tmplData = {};
            var languages = [];
            _.each(this.model.get('languages'), function(lang, index){
                languages.push({id: index.toString(), label: lang});
            });
            tmplData.languages = languages;
            tmplData.language = this.model.get('language');
            var out = Mustache.render(this.template, tmplData);
            this.el.html(out);
        },
        onChangeLanguage: function(e) {
            e.preventDefault();
            var $target = $(e.target);
            var language = $($target[0].options[$target[0].selectedIndex]).html();
            // update the labels to match the new language
            this.model.fields.each(function(field, index){
                if(field.has('fhLabel'))
                {
                    field.set('label', recline.Backend.FormhubMongoAPI.
                        _fhMultilangLabel(field.get('fhLabel'), language), {silent: true});
                }
            });
            this.model.set({language: language});
        }
    });
})(jQuery, recline.View);
