pyxform
=======

.. automodule:: pyxform

xls2xform
---------

.. automodule:: pyxform.xls2xform

API
---

pyxform takes an object oriented approach to defining
surveys. Questions, question options, groups of questions, and surveys
are all instances of SurveyElement. This allows us to model a survey
as a tree of SurveyElements. The class inheritance is structured as
follows:

* SurveyElement
    + Option
    + Question
        - InputQuestion
        - UploadQuestion
        - MultipleChoiceQuestion
    + Section
        - RepeatingSection
        - GroupedSection
        - Survey

SurveyElement
~~~~~~~~~~~~~

.. autoclass:: pyxform.survey_element.SurveyElement
    :members:

Question
~~~~~~~~

.. autoclass:: pyxform.question.Question
    :members:
