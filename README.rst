ODK Deploy
==========

How should this project be structured?

* odk_logger - Previously called xform_manager, this app serves XForms
  to ODK Collect and receives submissions from ODK Collect. This is a
  stand alone application.
* odk_exporter - Previously called parsed_xforms, this app provides a
  csv and xls export of the data stored in odk_logger. This app uses a
  data dictionary as produced by pyxform.
* odk_mapper - This app will pull some code out of
  parsed_xforms. Maybe it's smart to combine odk_exporter and
  odk_mapper?
* main - This app can be the glue that brings odk_logger and
  odk_exporter together. This pull the QuickConverter out of
  xls2xform.

Apps to be removed:
* survey_photos: we will need some mapping features, maybe this code
  is in parsed_xforms.
* test_static
* ui: we need to come up with a smart way to customize the look of the
  site without affecting the rest of the code. maybe ui is how we
  should do this.
* user_management: i don't think we need this heavy lifting. we'll be
  satisfied if users must log in to access the site and then they can
  only access their surveys.

I want to talk with Alex about these ideas before I push ahead. I
think the next step is to get something working as quickly as possible
with what we have. To do this I will be working primarily in main to
get things working and tested.
