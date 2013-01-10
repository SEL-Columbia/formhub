this.fh = this.fh || {};
this.fh.View = this.fh.View || {};
(function($, my){
    my.MultiView = recline.View.MultiView.extend({
        template: ' \
  <div class="recline-data-explorer"> \
    <div class="alert-messages"></div> \
    <div class="header clearfix"> \
      <div class="navigation"> \
        <div class="btn-group" data-toggle="buttons-radio"> \
        {{#views}} \
        <a href="#{{id}}" data-view="{{id}}" class="btn">{{label}}</a> \
        {{/views}} \
        </div> \
      </div> \
      <div class="recline-results-info"> \
        <span class="doc-count">{{recordCount}}</span> records\
      </div> \
      <div class="menu-right"> \
        <div class="btn-group" data-toggle="buttons-checkbox"> \
          {{#sidebarViews}} \
          <a href="#" data-action="{{id}}" class="btn active">{{label}}</a> \
          {{/sidebarViews}} \
        </div> \
      </div> \
    </div> \
    <h4>Double click on any record to open it on a page where you can view, edit or delete it.</h4> \
    <div class="data-view-sidebar"></div> \
    <div class="data-view-container"></div> \
  </div> \
  ',

        render: function() {
            var tmplData = this.model.toTemplateJSON();
            tmplData.views = this.pageViews;
            tmplData.sidebarViews = this.sidebarViews;
            var template = Mustache.render(this.template, tmplData);
            $(this.el).html(template);

            // now create and append other views
            var $dataViewContainer = this.el.find('.data-view-container');
            var $dataSidebar = this.el.find('.data-view-sidebar');

            // the main views
            _.each(this.pageViews, function(view, pageName) {
                view.view.render();
                $dataViewContainer.append(view.view.el);
                if (view.view.elSidebar) {
                    $dataSidebar.append(view.view.elSidebar);
                }
            });

            _.each(this.sidebarViews, function(view) {
                this['$'+view.id] = view.view.el;
                $dataSidebar.append(view.view.el);
            }, this);

            var pager = new recline.View.Pager({
                model: this.model.queryState
            });
            this.el.find('.recline-results-info').after(pager.el);

            var queryEditor = new recline.View.QueryEditor({
                model: this.model.queryState
            });
            var $queryEditor = this.el.find('.query-editor-here');
            if($queryEditor.length > 0)
                $queryEditor.append(queryEditor.el);

        }
    });
})(jQuery, fh.View);