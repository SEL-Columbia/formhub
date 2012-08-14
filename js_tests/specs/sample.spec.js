// Load mocks for this spec
EnvJasmine.load(EnvJasmine.mocksDir + "sample.mock.js");

describe("Sample", function () {
    it("asserts that one plus one equals two", function () {
        expect(1 + 1 == 2).toEqual(true);
    });

    it("asserts that sample moock data is defined", function() {
        expect(SampleMockData).toBeDefined();
    });
});