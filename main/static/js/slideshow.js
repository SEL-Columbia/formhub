//Slideshow
var images = [],
		index = 1,
		staticImageDir = "/static/images/",
		imageCount = 10,
		loadIntervalId,
		restartTimeoutId,
		rotateTime = 6000,
		waitToRefreshTime = 12000;

for (var i=1; i<imageCount + 1; i++) {
	images.push(staticImageDir + 'screens/' + i + '.jpg');
}

/*$.each(images, function (i, val) {
  $('<img/>').attr('src', val);
});*/

function rotateImage() {
	$('#topslider').fadeOut(300, function() {
	  $(this).attr('src', images[index]);
	  $(this).fadeIn(300, function() {
	    if (index == images.length-1) { index = 0; }
	    else { index++; }
	  });
	});
}

function startRotate() {
	loadIntervalId = setInterval(rotateImage, rotateTime);
}

function stopRotate(intId) {
	clearInterval(intId);
}

function userClicked() {
	if (loadIntervalId) { stopRotate(loadIntervalId); }
	if (restartTimeoutId) { clearTimeout(restartTimeoutId); }
	restartTimeoutId = setTimeout(startRotate, waitToRefreshTime - rotateTime);
	
	$('#topslider').fadeOut(function() {
	  $(this).attr('src', images[index]);
	  $(this).fadeIn('0', function() {
	    if (index == images.length-1) { index = 0; }
	    else { index++; }
	  });
	});
}

//Features
var callouts = [],
		featureIndex = 1,
		featureCount = 3,
		loadFeatureIntervalId,
		restartFeatureTimeoutId,
		rotateFeatureTime = 10000;


for (var i=1; i<featureCount + 1; i++) {
	callouts.push(staticImageDir + 'features/' + i + '.jpg');
}

$.each(callouts, function (i, val) {
  $('<img/>').attr('src', val);
});

function changeFeature(fId) {
	$('#featuretable td').attr('class','feature_off');
	$('#feature'+fId).attr('class','feature_on');
	$('#featurescallout').fadeOut(300, function() {
	  $(this).attr('src', callouts[fId-1]);
	  $(this).fadeIn(300, function() {
	    featureIndex = fId;
	  });
	});
}

function rotateFeature() {
	if (featureIndex == callouts.length) { featureIndex = 1; }
	else { featureIndex++; }
	changeFeature(featureIndex);
}

function startRotateFeatures() {
	loadFeatureIntervalId = setInterval(rotateFeature, rotateFeatureTime);
}

function userClickedFeature(fId) {
	if (loadFeatureIntervalId) { stopRotate(loadFeatureIntervalId); }
	if (restartFeatureTimeoutId) { clearTimeout(restartFeatureTimeoutId); }
	restartFeatureTimeoutId = setTimeout(startRotateFeatures, waitToRefreshTime - rotateFeatureTime);
	changeFeature(fId);
}


$(document).ready(function()
{
 	//startRotate();
  startRotateFeatures();
});