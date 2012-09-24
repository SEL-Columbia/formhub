EnvJasmine.load(EnvJasmine.mocksDir + "instance_view.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/underscore-min.js");
EnvJasmine.load(EnvJasmine.mocksDir + "../utils.js");
EnvJasmine.load(EnvJasmine.jsDir + "odk_viewer/static/js/instance.js");

describe("Instance View tests", function() {
    it("checks that parseQuestions builds hierachy's as expected", function() {
        expect(SurveyData.children).toBeDefined();
        expect(questions).toBeDefined();
        parseQuestions(SurveyData.children);
        // must only have one question
        expect(Object.size(questions)).toEqual(1);
        expect(questions['note_one_a_group_a_question']).toBeDefined();
    });
});