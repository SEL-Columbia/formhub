// Load mocks for this spec
EnvJasmine.load(EnvJasmine.mocksDir + "formManagers.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/formManagers.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/underscore-min.js");

describe("FormJSON tests", function() {
    var sampleFJM1, sampleFJM2, sampleFJM2_1;
    beforeEach(function () {
        sampleFJM1 = new FormJSONManager(fjmData1.url);
        sampleFJM1._init(fjmData1.actualJSON);
        sampleFJM2 = new FormJSONManager(fjmData2.url);
        sampleFJM2._init(fjmData2.actualJSON);
        sampleFJM2_1 = new FormJSONManager(fjmData2.url);
        sampleFJM2_1._init(fjmData2_1.actualJSON);
    });
    
    it ("checks that form json loads properly for init with no callback", function () {
        runs(function () {
            expect(sampleFJM1).toBeDefined();
            expect(sampleFJM1.callback).toBeUndefined();
        });
    });
    it ("checks that form json init parses geopoints and supportedLanguages ", function () {
        runs(function() {
            expect(sampleFJM1.getGeoPointQuestion()).toEqual(fjmData1.geoPointQuestions[0]);
            expect(sampleFJM1.geopointQuestions).toEqual(fjmData1.geoPointQuestions);
            expect(sampleFJM1.supportedLanguages).toEqual(fjmData1.supportedLanguages);
        });
    });
    it ("checks that form json init parses selectOneQuestionNames", function () {
        runs(function() {
            expect(_.pluck(sampleFJM1.getSelectOneQuestions(), 'name')).toEqual(fjmData1.selectOneQuestionNames);
            expect(_.uniq(_.pluck(sampleFJM1.getSelectOneQuestions(), 'type'))).toEqual(["select one"]);
        });
    });
    it ("checks questions are returned by name, and choices are returned by question", function () {
        runs(function() {
            expect(sampleFJM1.getQuestionByName('water_point_geocode')).toEqual(fjmData1.geoPointQuestions[0]);
            expect(sampleFJM1.getChoices(sampleFJM1.getQuestionByName('animal_point'))).toEqual(fjmData1.choicesForAnimalPoint);
        });
    });
    it ("checks that form json parses labels for English", function () {
        runs(function() {
            var geoQ = sampleFJM1.getQuestionByName('water_point_geocode');
            expect(sampleFJM1.getMultilingualLabel(geoQ)).toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ), "English").toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ), "French").toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ), "^&~#*(").toEqual(fjmData1.geoPointQuestions[0].label.English);

        });
    });
    it ("checks that form json parses labels", function () {
        runs(function() {
            var geoQ = sampleFJM1.getQuestionByName('water_point_geocode');
            expect(sampleFJM1.getMultilingualLabel(geoQ)).toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ, "English")).toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ, "French")).toEqual(fjmData1.geoPointQuestions[0].label.English);
            expect(sampleFJM1.getMultilingualLabel(geoQ, "^&~#*(")).toEqual(fjmData1.geoPointQuestions[0].label.English);
        });
        runs(function() {
            var facilityQ = sampleFJM2.getQuestionByName('facility_type');
            expect(sampleFJM2.getMultilingualLabel(facilityQ)).toEqual(fjmData2.labelsForFacilityType.French);
            expect(sampleFJM2.getMultilingualLabel(facilityQ, "English")).toEqual(fjmData2.labelsForFacilityType.English);
            expect(sampleFJM2.getMultilingualLabel(facilityQ, "French")).toEqual(fjmData2.labelsForFacilityType.French);
            expect(sampleFJM2.getMultilingualLabel(facilityQ, "^&~#*(")).toEqual(fjmData2.labelsForFacilityType.French);
            expect(sampleFJM2.getMultilingualLabel(sampleFJM2.getQuestionByName('start'))).toEqual('start');
        });
    });
    it("checks that multi-lang labels are properly parsed when there is a mismatch in language labels", function(){
        /**
         * Prompted by a form where the first question where the label is not
         * empty has a space character in one language (Vietnamese) and nothing in the rest
         * The form's json ends up having a label object with a single value which is Vietnamese
         * while the rest of the questions that have valid labels have objects for each language
         * The old implementation would break at the first valid label, in thi case we would
         * assume all the questions only have vietnamese as a language
         */
        expect(sampleFJM2_1.supportedLanguages.length).toBe(2);
    });
});
