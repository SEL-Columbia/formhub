// Load the file to test here.
//
// Example:
EnvJasmine.load(EnvJasmine.jsDir + "ajaxDemo.js");

// This is the test code.
describe("AjaxDemo", function () {
    it("calls the addDataToDOM function on success", function () {
        TwitterWidget.makeRequest(); // Make the AJAX call

        spyOn(TwitterWidget, "addDataToDOM"); // Add a spy to the callback

        mostRecentAjaxRequest().response({status: 200, responseText: "foo"}); // Mock the response

        expect(TwitterWidget.addDataToDOM).toHaveBeenCalledWith("foo");
    });
});
