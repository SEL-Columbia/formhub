EnvJasmine.load(EnvJasmine.mocksDir + "fh_utils.mock.js");
EnvJasmine.load(EnvJasmine.jsDir + "main/static/js/fh_utils.js");

describe("Formhub JS utils tests", function() {
    it("tests that timezone without minute component get a 00 minute appended", function() {
        expect(timezoneWithoutMinute).toBeDefined();
        expect(fhUtils.DateTimeToISOString(timezoneWithoutMinute['submitted_date']))
            .toEqual(timezoneWithoutMinute['expected_iso_date']);
    });

    it("tests that timezone with minute component get a 00 minute appended", function() {
        expect(timezoneWitMinute).toBeDefined();
        expect(fhUtils.DateTimeToISOString(timezoneWitMinute['submitted_date']))
            .toEqual(timezoneWitMinute['expected_iso_date']);
    });

    it("tests that timezone with Z component", function() {
        expect(timezoneWithZ).toBeDefined();
        expect(fhUtils.DateTimeToISOString(timezoneWithZ['submitted_date']))
            .toEqual(timezoneWithZ['expected_iso_date']);
    });
});