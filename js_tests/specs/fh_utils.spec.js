EnvJasmine.load(EnvJasmine.mocksDir + "fh_utils.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/fh_utils.js");

describe("Formhub JS utils tests", function() {
    it("tests that an ison date in the correct format is returned", function() {
        expect(SubmissionDates).toBeDefined();
        _.each(SubmissionDates, function(submissionDate){
            expect(fhUtils.DateTimeToISOString(submissionDate['submitted_date']))
                .toEqual(submissionDate['expected_iso_date']);
        })
    });
});