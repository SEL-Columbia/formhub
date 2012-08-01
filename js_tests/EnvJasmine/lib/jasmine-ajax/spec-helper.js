beforeEach(function() {
    if (!jasmine.Ajax.isInstalled()) {
        jasmine.Ajax.installMock();
    }
});

afterEach(function() {
    clearAjaxRequests();
});
