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

        render: function() {
            var self = this;

            var options = _.extend({
                enableCellNavigation: true,
                enableColumnReorder: true,
                explicitInitialization: true,
                syncColumnCellResize: true,
                forceFitColumns: this.state.get('fitColumns')
            }, self.state.get('gridOptions'));

            // We need all columns, even the hidden ones, to show on the column picker
            var columns = [];
            // custom formatter as default one escapes html
            // plus this way we distinguish between rendering/formatting and computed value (so e.g. sort still works ...)
            // row = row index, cell = cell index, value = value, columnDef = column definition, dataContext = full row values
            var formatter = function(row, cell, value, columnDef, dataContext) {
                var field = self.model.fields.get(columnDef.id);
                if (field.renderer) {
                    return field.renderer(value, field, dataContext);
                } else {
                    return value;
                }
            }
            _.each(this.model.fields.toJSON(),function(field){
                var column = {
                    id:field['id'],
                    name:field.hasOwnProperty('multi_lang_labels')?
                        recline.Backend.FormhubMongoAPI._fhMultilangLabel(field.multi_lang_labels, self.model.get('language')):field['label'],
                    field:field['id'],
                    sortable: true,
                    minWidth: 80,
                    formatter: formatter
                };

                var widthInfo = _.find(self.state.get('columnsWidth'),function(c){return c.column == field.id});
                if (widthInfo){
                    column['width'] = widthInfo.width;
                }

                var editInfo = _.find(self.state.get('columnsEditor'),function(c){return c.column == field.id});
                if (editInfo){
                    column['editor'] = editInfo.editor;
                }
                columns.push(column);
            });

            // Restrict the visible columns
            var visibleColumns = columns.filter(function(column) {
                return _.indexOf(self.state.get('hiddenColumns'), column.id) == -1;
            });

            // Order them if there is ordering info on the state
            if (this.state.get('columnsOrder') && this.state.get('columnsOrder').length > 0) {
                visibleColumns = visibleColumns.sort(function(a,b){
                    return _.indexOf(self.state.get('columnsOrder'),a.id) > _.indexOf(self.state.get('columnsOrder'),b.id) ? 1 : -1;
                });
                columns = columns.sort(function(a,b){
                    return _.indexOf(self.state.get('columnsOrder'),a.id) > _.indexOf(self.state.get('columnsOrder'),b.id) ? 1 : -1;
                });
            }

            // Move hidden columns to the end, so they appear at the bottom of the
            // column picker
            var tempHiddenColumns = [];
            for (var i = columns.length -1; i >= 0; i--){
                if (_.indexOf(_.pluck(visibleColumns,'id'),columns[i].id) == -1){
                    tempHiddenColumns.push(columns.splice(i,1)[0]);
                }
            }
            columns = columns.concat(tempHiddenColumns);

            // Transform a model object into a row
            function toRow(m) {
                var row = {};
                self.model.fields.each(function(field){
                    row[field.id] = m.getFieldValueUnrendered(field);
                });
                return row;
            }

            function RowSet() {
                var models = [];
                var rows = [];

                this.push = function(model, row) {
                    models.push(model);
                    rows.push(row);
                }

                this.getLength = function() { return rows.length; }
                this.getItem = function(index) { return rows[index];}
                this.getItemMetadata= function(index) { return {};}
                this.getModel= function(index) { return models[index]; }
                this.getModelRow = function(m) { return models.indexOf(m);}
                this.updateItem = function(m,i) {
                    rows[i] = toRow(m);
                    models[i] = m
                };
            };

            var data = new RowSet();

            this.model.records.each(function(doc){
                data.push(doc, toRow(doc));
            });

            this.grid = new Slick.Grid(this.el, data, visibleColumns, options);

            // Column sorting
            var sortInfo = this.model.queryState.get('sort');
            if (sortInfo){
                var column = sortInfo[0].field;
                var sortAsc = !(sortInfo[0].order == 'desc');
                this.grid.setSortColumn(column, sortAsc);
            }

            this.grid.onSort.subscribe(function(e, args){
                var order = (args.sortAsc) ? 'asc':'desc';
                var sort = [{
                    field: args.sortCol.field,
                    order: order
                }];
                self.model.query({sort: sort});
            });

            this.grid.onColumnsReordered.subscribe(function(e, args){
                self.state.set({columnsOrder: _.pluck(self.grid.getColumns(),'id')});
            });

            this.grid.onColumnsResized.subscribe(function(e, args){
                var columns = args.grid.getColumns();
                var defaultColumnWidth = args.grid.getOptions().defaultColumnWidth;
                var columnsWidth = [];
                _.each(columns,function(column){
                    if (column.width != defaultColumnWidth){
                        columnsWidth.push({column:column.id,width:column.width});
                    }
                });
                self.state.set({columnsWidth:columnsWidth});
            });

            this.grid.onCellChange.subscribe(function (e, args) {
                // We need to change the model associated value
                //
                var grid = args.grid;
                var model = data.getModel(args.row);
                var field = grid.getColumns()[args.cell]['id'];
                var v = {};
                v[field] = args.item[field];
                model.set(v);
            });

            this.grid.onDblClick.subscribe(function (e, args){
                var cell = this.getCellFromEvent(e)
                var record = this.getData().getModel(cell.row);
                self.trigger("doubleclick", record);
            });

            var columnpicker = new Slick.Controls.ColumnPicker(columns, this.grid,
                _.extend(options,{state:this.state}));

            if (self.visible){
                self.grid.init();
                self.rendered = true;
            } else {
                // Defer rendering until the view is visible
                self.rendered = false;
            }

            return this;
        },

        // set columns to show on the grid - meant to be used after grid is init-ed, if not, grid will be init-ed first
        setColumns: function(columnsToShow) {
            if(!columnsToShow.length)
                return;
            var self = this;
            var visibleColumns = [];
            var hiddenColumnsIds = [];
            var formatter = function(row, cell, value, columnDef, dataContext) {
                var field = self.model.fields.get(columnDef.id);
                if (field.renderer) {
                    return field.renderer(value, field, dataContext);
                } else {
                    return value;
                }
            }
            _.each(this.model.fields.toJSON(),function(field){
                // check if this column is in put to show list
                var foundColumn = _.find(columnsToShow, function(columnName){
                    return field['id'] == columnName;
                });
                if(foundColumn){
                    var column = {
                        id:field['id'],
                        name:field.hasOwnProperty('multi_lang_labels')?
                            recline.Backend.FormhubMongoAPI._fhMultilangLabel(field.multi_lang_labels, self.model.get('language')):field['label'],
                        field:field['id'],
                        sortable: true,
                        minWidth: 80,
                        formatter: formatter
                    };

                    var widthInfo = _.find(self.state.get('columnsWidth'),function(c){return c.column == field.id});
                    if (widthInfo){
                        column['width'] = widthInfo.width;
                    }

                    var editInfo = _.find(self.state.get('columnsEditor'),function(c){return c.column == field.id});
                    if (editInfo){
                        column['editor'] = editInfo.editor;
                    }
                    visibleColumns.push(column);
                }
                else
                {
                    hiddenColumnsIds.push(field['id']);
                }
            });
            if (!this.rendered){
                if (!this.grid){
                    this.render();
                }
                this.grid.init();
                this.rendered = true;
            }
            this.grid.setColumns(visibleColumns);
            this.state.set({hiddenColumns:hiddenColumnsIds});
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
