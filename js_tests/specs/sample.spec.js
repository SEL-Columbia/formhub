// Load mocks for this spec
EnvJasmine.load(EnvJasmine.mocksDir + "sample.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/formManagers.js");

describe("Sample", function () {
    it("asserts that one plus one equals two", function () {
        expect(1 + 1 == 2).toEqual(true);
    });

    it("asserts that sample moock data is defined", function() {
        expect(SampleMockData).toBeDefined();
    });
});

describe("FormJSON tests", function() {
    FormJSONData.forEach(function(formJSONDatum) {
        $.getJSON(formJSONDatum.url, function(data) {
            console.log(data);
        });
        it ("checks that form json loads properly for " + formJSONDatum.url, function () {
            that = this; 
            that.callbackCalled = false;
            var mockCallBack = function () { that.callbackCalled = true; }
            var sampleFormJSONManager = new FormJSONManager(formJSONDatum.url, mockCallBack);
            runs(function () {
                expect(sampleFormJSONManager).toBeDefined();
                expect(sampleFormJSONManager.callback).toBeDefined();
                sampleFormJSONManager.loadFormJSON();
            });
            waitsFor(function () {
                return this.callBackCalled;
            }, "Can sometimes take a while to load form.json", 20000);
            runs(function() {
                expect(sampleFormJSONManager.getGeoPointQuestion()).toEqual(formJSONDatum.geoPointQuestions[0]);
                expect(sampleFormJSONManager.supportedLanguages).toEqual(formJSONDatum.supportedLanguages);
            });
        });
    });
});
