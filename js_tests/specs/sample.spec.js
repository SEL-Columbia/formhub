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
    var sampleFormJSONManager = new FormJSONManager(FormJSONData.url);
    
    it ("checks that form json loads properly for init with no callback", function () {
        runs(function () {
            expect(sampleFormJSONManager).toBeDefined();
            expect(sampleFormJSONManager.callback).toBeUndefined();
        });
    });
    
    sampleFormJSONManager._init(FormJSONData.actualJSON);
    it ("checks that form json init parses geopoints and supportedLanguages ", function () {
        runs(function() {
            expect(sampleFormJSONManager.geopointQuestions).toEqual(FormJSONData.geoPointQuestions);
            expect(sampleFormJSONManager.getGeoPointQuestion()).toEqual(FormJSONData.geoPointQuestions[0]);
            expect(sampleFormJSONManager.supportedLanguages).toEqual(FormJSONData.supportedLanguages);
        });
    });
});
