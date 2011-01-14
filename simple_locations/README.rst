simple-locations
================

A simple Locations (Area, AreaType, Point) model for Django/RapidSMS applications.


Point
-----

A simple coordinates holder: latittude and longitude.


AreaType
--------

Defines the kind of an area. Use case would be District, Village, etc.
AreaType includes a required slug field.


Area
----

Area defines a zone/area. Fields:

* name
* code (uuid-generated if not provided)
* kind (AreaType)
* location (Point)
* parent (Area)

Dependencies
============

* django-mptt
* `code_generator <http://github.com/yeleman/code_generator>`_
