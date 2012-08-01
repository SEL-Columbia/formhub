// Load the file to test here.
//
// Example:
EnvJasmine.load(EnvJasmine.jsDir + "demo.js");

// Load mocks for this spec
EnvJasmine.load(EnvJasmine.mocksDir + "demo.mock.js");

describe("Demo", function () {
    it("asserts that one plus one equals two", function () {
        expect(1 + 1 == 2).toEqual(true);
    });

    it("asserts that 1 + 1 does not equal 3", function () {
        expect(1 + 1 == 3).toEqual(false);
    });

    it("asserts that a user has a birthdate", function () {
        expect(Demo.checkBirthdate(demoUser)).toEqual(true);
    });

    it("asserts that an ill-formed user has no birthdate", function () {
        expect(Demo.checkBirthdate(badUser)).toEqual(false);
    });
});
