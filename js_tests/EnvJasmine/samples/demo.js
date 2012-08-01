// Sample demo

if (!this.Demo) {
    Demo = {};
}

Demo.checkBirthdate = function (user) {
    return !user.birthdate ? false : true;
}
