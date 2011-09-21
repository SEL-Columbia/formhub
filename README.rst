ODK Deploy
==========

* odk_logger - This app serves XForms to ODK Collect and receives
  submissions from ODK Collect. This is a stand alone application.
* odk_viewer - This app provides a
  csv and xls export of the data stored in odk_logger. This app uses a
  data dictionary as produced by pyxform. It also provides a map and
  single survey view.
* main - This app is the glue that brings odk_logger and odk_exporter
  together. This is where xls2xform conversion happens.

TODO:
* Get the conversion, download XForm, upload survey, download csv
  process working and tested.
* ui app: we need to come up with a smart way to customize the look of
  the site without affecting the rest of the code. maybe ui is how we
  should do this.
* Get rid of common_tags.py
