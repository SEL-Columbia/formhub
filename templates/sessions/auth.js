'use strict';

// Assume global app variable
// running behind nginx, this file is dynamically served by django
// based on the users current settings
app.run(function($rootScope){
    $rootScope.userId = '{{username}}';
    $rootScope.formId = '{{form}}';
});