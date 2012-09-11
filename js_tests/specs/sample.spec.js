// Load mocks for this spec
EnvJasmine.load(EnvJasmine.mocksDir + "sample.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/formManagers.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/underscore-min.js");

describe("FormJSON tests", function() {
    var sampleFJM;
    beforeEach(function () {
        sampleFJM = new FormJSONManager(fjmData.url);
        sampleFJM._init(fjmData.actualJSON);
    });
    
    it ("checks that form json loads properly for init with no callback", function () {
        runs(function () {
            expect(sampleFJM).toBeDefined();
            expect(sampleFJM.callback).toBeUndefined();
        });
    });
    it ("checks that form json init parses geopoints and supportedLanguages ", function () {
        runs(function() {
            expect(sampleFJM.getGeoPointQuestion()).toEqual(fjmData.geoPointQuestions[0]);
            expect(sampleFJM.geopointQuestions).toEqual(fjmData.geoPointQuestions);
            expect(sampleFJM.supportedLanguages).toEqual(fjmData.supportedLanguages);
        });
    });
    it ("checks that form json init parses selectOneQuestionNames", function () {
        runs(function() {
            expect(_.pluck(sampleFJM.getSelectOneQuestions(), 'name')).toEqual(fjmData.selectOneQuestionNames);
            expect(_.uniq(_.pluck(sampleFJM.getSelectOneQuestions(), 'type'))).toEqual(["select one"]);
        });
    });
    it ("checks questions are returned by name, and choices are returned by question", function () {
        runs(function() {
            expect(sampleFJM.getQuestionByName('water_point_geocode')).toEqual(fjmData.geoPointQuestions[0]);
            expect(sampleFJM.getChoices(sampleFJM.getQuestionByName('animal_point'))).toEqual(fjmData.choicesForAnimalPoint);
        });
    });
    it ("checks that form json parses labels for multiple languages", function () {
        runs(function() {
            var geoQ = sampleFJM.getQuestionByName('water_point_geocode');
            expect(sampleFJM.getMultilingualLabel(geoQ)).toEqual(fjmData.geoPointQuestions[0].label.English);
            expect(sampleFJM.getMultilingualLabel(geoQ), "English").toEqual(fjmData.geoPointQuestions[0].label.English);
            expect(sampleFJM.getMultilingualLabel(geoQ), "French").toEqual(fjmData.geoPointQuestions[0].label.English);
            expect(sampleFJM.getMultilingualLabel(geoQ), "^&~#*(").toEqual(fjmData.geoPointQuestions[0].label.English);

        });
    });
});
