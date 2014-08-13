var dataset = new recline.Model.Dataset({
    formUrl: formJSONUrl,
    dataUrl: mongoAPIUrl,
    backend: "FormhubMongoAPI"
});

var fhSlickView = new recline.View.FHSlickGrid({
    model: dataset,
    state: {
        fitColumns: false
    }
});

var views = [
    {
        id: 'grid',
        label: 'Data Grid',
        view: fhSlickView
    }
];

var fieldsView = new recline.View.Fields({
    model: dataset
});
var filterEditor = new recline.View.FilterEditor({
    model: dataset
});
dataset.bind('change:language', function(){
    fieldsView.render();
    filterEditor.render();
});
sideBarViews = [
    {
        id: 'langsView',
        label: 'Languages',
        view: new recline.View.LanguageSelector({
            model: dataset
        })
    },
    {
        id: 'filterEditor',
        label: 'Filters',
        view: filterEditor
    },
    {
        id: 'fieldsView',
        label: 'Fields',
        view: fieldsView
    }
];

multiView = new fh.View.MultiView({
    model: dataset,
    views: views,
    sidebarViews: sideBarViews
});

// attach callback field's reset so we can setup what columns to show
dataset.fields.on("reset", function(){
    // use the first numDefaultColumns columns
    var columnsToShow = _.first(_.map(dataset.fields.models, function(field){
        return field.id;
    }), numDefaultColumns);
    fhSlickView.setColumns(columnsToShow);
});

// subscribe to the grids double click event to navigate to the instance view
fhSlickView.on("doubleclick", function(record){
    var record_id = record.get("_id");
    if(record_id)
        window.open(instance_view_url + "#/" + record_id, "_blank");
});

$(document).ready(function(){
    // attach to DOM
    $('#data-grid').append(multiView.el);
});