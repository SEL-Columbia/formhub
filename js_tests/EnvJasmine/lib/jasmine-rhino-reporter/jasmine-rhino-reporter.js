importPackage(java.lang);

var RhinoReporter = function() {
	/*
	 * Reporter which reports the number of //expects// checks which
	 * passed/failed at the end of the test run 
	 */
    return {
        reportRunnerStarting: function(runner) {
            if (EnvJasmine.incrementalOutput) {
                print(EnvJasmine.specFile);
            }
        },

        reportRunnerResults: function(runner) {
            var results = runner.results();

            if (EnvJasmine.incrementalOutput) {
                var passed = results.passedCount - EnvJasmine.passedCount,
                    failed = results.failedCount - EnvJasmine.failedCount,
                    total = results.totalCount - EnvJasmine.totalCount;
                print();
                print([
                    EnvJasmine[passed ? 'green' : 'plain']("Passed: " + passed),
                    EnvJasmine[failed ? 'red' : 'plain']("Failed: " + failed),
                    EnvJasmine.plain("Total: " + total)
                ].join(' '));
            }

            EnvJasmine.passedCount = results.passedCount;
            EnvJasmine.failedCount = results.failedCount;
            EnvJasmine.totalCount = results.totalCount;
        },

        reportSuiteResults: function(suite) {
        },

        reportSpecStarting: function(spec) {
        },

        reportSpecResults: function(spec) {
            if (spec.results().passed()) {
                System.out.print(EnvJasmine.green("."));
            } else {
                var i, msg, result,
                    specResults = spec.results().getItems();

                System.out.print(EnvJasmine.red("F"));

                msg = [
                    "FAILED",
                    "File : " + EnvJasmine.specFile,
                    "Suite: " + this.getSuiteName(spec.suite),
                    "Spec : " + spec.description
                ];

                for (i = 0; i < specResults.length; i++) {
                    result = specResults[i];
                    if (result.type == 'log') {
                        msg.push(result.toString());
                    } else if (result.type == 'expect' && result.passed && !result.passed()) {
                        msg.push(result.message);

                        if (result.trace.stack) {
                            msg.push(specResults[i].trace.stack);
                        }
                    }
                }

                EnvJasmine.results.push(msg.join("\n"));
            }
        },

        log: function(str) {
        },

        getSuiteName: function(suite) {
            var suitePath = [];

            while (suite) {
                suitePath.unshift(suite.description);
                suite = suite.parentSuite;
            }

            return suitePath.join(' - ');
        }
    };
};

var RhinoSpecReporter = function() {
	/*
	 * Reporter which reports the number of //specs// which passed/failed at the end
	 * of the test run 
	 */
    return {
        reportRunnerStarting: function(runner) {
            if (EnvJasmine.incrementalOutput) {
                print(EnvJasmine.specFile);
            }
        },

        reportRunnerResults: function(runner) {
            var results = runner.results();

            if (EnvJasmine.incrementalOutput) {
                print();
                print([
                    EnvJasmine.green("Passed: " + (results.passedCount - EnvJasmine.passedCount)),
                    EnvJasmine.red("Failed: " + (results.failedCount - EnvJasmine.failedCount)),
                    EnvJasmine.plain("Total: " + (results.totalCount - EnvJasmine.totalCount))
                ].join(' '));
            }
        },

        reportSuiteResults: function(suite) {
        },

        reportSpecStarting: function(spec) {
        },

        reportSpecResults: function(spec) {
            if (spec.results().passed()) {
                System.out.print(EnvJasmine.green("."));
                EnvJasmine.passedCount += 1;
            } else {
                var i, msg, result,
                    specResults = spec.results().getItems();

                System.out.print(EnvJasmine.red("F"));

                msg = [
                    "FAILED",
                    "File : " + EnvJasmine.specFile,
                    "Suite: " + this.getSuiteName(spec.suite),
                    "Spec : " + spec.description
                ];

                for (i = 0; i < specResults.length; i++) {
                    result = specResults[i];
                    if (result.type == 'log') {
                        msg.push(result.toString());
                    } else if (result.type == 'expect' && result.passed && !result.passed()) {
                        msg.push(result.message);

                        if (result.trace.stack) {
                            msg.push(specResults[i].trace.stack);
                        }
                    }
                }
                EnvJasmine.failedCount += 1;

                EnvJasmine.results.push(msg.join("\n"));
            }
            EnvJasmine.totalCount += 1;
        },

        log: function(str) {
        },

        getSuiteName: function(suite) {
            var suitePath = [];

            while (suite) {
                suitePath.unshift(suite.description);
                suite = suite.parentSuite;
            }

            return suitePath.join(' - ');
        }
    };
};


