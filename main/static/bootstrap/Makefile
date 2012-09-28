BOOTSTRAP_LESS = ./less/bootstrap-custom.less
BOOTSTRAP = ./css/bootstrap.css
BOOTSTRAP_MIN = ./css/bootstrap.min.css
BOOTSTRAP_RESPONSIVE_LESS = ./less/responsive-custom.less
BOOTSTRAP_RESPONSIVE = ./css/bootstrap-responsive.css
BOOTSTRAP_RESPONSIVE_MIN = ./css/bootstrap-responsive.min.css
SCREEN_LESS = ./less/screen.less
SCREEN = ../css/screen.css
SCREEN_MIN = ../css/screen.min.css
BOOTSTRAP_JS = ./js/bootstrap.js
BOOTSTRAP_JS_MIN = ./js/bootstrap.min.js
DATE=$(shell date +%I:%M%p)
CHECK=\033[32m✔\033[39m
HR=\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#

#
# BUILD SIMPLE BOOTSTRAP DIRECTORY
# recess & uglifyjs are required
#

bootstrap:
	mkdir -p ./img
	mkdir -p ./css
	mkdir -p ./js
	cp src/img/* ./img/
	lessc ${BOOTSTRAP_LESS} ${BOOTSTRAP}
	recess --compress ${BOOTSTRAP} > ${BOOTSTRAP_MIN}
	lessc ${BOOTSTRAP_RESPONSIVE_LESS} ${BOOTSTRAP_RESPONSIVE}
	recess --compress ${BOOTSTRAP_RESPONSIVE} > ${BOOTSTRAP_RESPONSIVE_MIN}
	lessc ${SCREEN_LESS} ${SCREEN}
	recess --compress ${SCREEN} > ${SCREEN_MIN}
	cat src/js/bootstrap-transition.js src/js/bootstrap-alert.js src/js/bootstrap-button.js src/js/bootstrap-carousel.js src/js/bootstrap-collapse.js src/js/bootstrap-dropdown.js src/js/bootstrap-modal.js src/js/bootstrap-tooltip.js src/js/bootstrap-popover.js src/js/bootstrap-scrollspy.js src/js/bootstrap-tab.js src/js/bootstrap-typeahead.js js/bootstrapx-clickover.js js/bootstrapx-clickover-btns.js > ${BOOTSTRAP_JS}
	uglifyjs -nc ${BOOTSTRAP_JS} > ./js/bootstrap.min.tmp.js
	echo "/*!\n* Bootstrap.js by @fat & @mdo\n* Copyright 2012 Twitter, Inc.\n* http://www.apache.org/licenses/LICENSE-2.0.txt\n*/" > ./js/copyright.js
	cat ./js/copyright.js ./js/bootstrap.min.tmp.js > ${BOOTSTRAP_JS_MIN}
	rm ./js/copyright.js ./js/bootstrap.min.tmp.js
	
#
# RUN JSHINT & QUNIT TESTS IN PHANTOMJS
#

test:
	jshint src/js/*.js --config src/js/.jshintrc
	jshint src/js/tests/unit/*.js --config src/js/.jshintrc
	node src/js/tests/server.js &
	phantomjs src/js/tests/phantom.js "http://localhost:3000/js/tests"
	kill -9 `cat src/js/tests/pid.txt`
	rm src/js/tests/pid.txt

#
# WATCH LESS FILES
#

watch:
	echo "Watching less files..."; \
	watchr -e "watch('src/less/.*\.less') { system 'make' }"


.PHONY: docs watch gh-pages
