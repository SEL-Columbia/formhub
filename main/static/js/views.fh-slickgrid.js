this.recline = this.recline || {};
this.recline.View = this.recline.View || {};

(function($, my) {
    my.FHSlickGrid = my.SlickGrid.extend({
        initialize: function(modelEtc) {
            var self = this;
            this.el = $(this.el);
            this.el.addClass('recline-slickgrid');
            _.bindAll(this, 'render');
            this.model.records.bind('add', this.render);
            this.model.records.bind('reset', this.render);
            this.model.records.bind('remove', this.render);
            this.model.records.bind('change', this.onRecordChanged, this);
            // language change event
            this.model.bind('change:language', this.onChangeLanguage, this);

            var state = _.extend({
                    hiddenColumns: [],
                    columnsOrder: [],
                    columnsSort: {},
                    columnsWidth: [],
                    columnsEditor: [],
                    options: {},
                    fitColumns: false
                }, modelEtc.state

            );
            this.state = new recline.Model.ObjectState(state);
        },

        onChangeLanguage: function(model, new_lang, changes){
            if(this.grid)
            {
                // get visible columns
                var columns = [];
                _.each(this.grid.getColumns(), function(column, index){
                    columns.push(column.id);
                });
                this.setColumns(columns);
                this.grid.render();
            }
        }
    });
})(jQuery, recline.View);
