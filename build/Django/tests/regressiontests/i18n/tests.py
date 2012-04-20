# -*- encoding: utf-8 -*-
import datetime
import decimal
import os
import sys
import pickle
from threading import local

from django.conf import settings
from django.template import Template, Context
from django.utils.formats import (get_format, date_format, time_format,
    localize, localize_input, iter_format_modules, get_format_modules)
from django.utils.importlib import import_module
from django.utils.numberformat import format as nformat
from django.utils.safestring import mark_safe, SafeString, SafeUnicode
from django.utils.translation import (ugettext, ugettext_lazy, activate,
        deactivate, gettext_lazy, pgettext, npgettext, to_locale,
        get_language_info, get_language)
from django.utils.unittest import TestCase


from forms import I18nForm, SelectDateForm, SelectDateWidget, CompanyForm
from models import Company, TestModel

from commands.tests import *

from test_warnings import DeprecationWarningTests

class TranslationTests(TestCase):

    def test_lazy_objects(self):
        """
        Format string interpolation should work with *_lazy objects.
        """
        s = ugettext_lazy('Add %(name)s')
        d = {'name': 'Ringo'}
        self.assertEqual(u'Add Ringo', s % d)
        activate('de')
        try:
            self.assertEqual(u'Ringo hinzuf\xfcgen', s % d)
            activate('pl')
            self.assertEqual(u'Dodaj Ringo', s % d)
        finally:
            deactivate()

        # It should be possible to compare *_lazy objects.
        s1 = ugettext_lazy('Add %(name)s')
        self.assertEqual(True, s == s1)
        s2 = gettext_lazy('Add %(name)s')
        s3 = gettext_lazy('Add %(name)s')
        self.assertEqual(True, s2 == s3)
        self.assertEqual(True, s == s2)
        s4 = ugettext_lazy('Some other string')
        self.assertEqual(False, s == s4)

    def test_lazy_pickle(self):
        s1 = ugettext_lazy("test")
        self.assertEqual(unicode(s1), "test")
        s2 = pickle.loads(pickle.dumps(s1))
        self.assertEqual(unicode(s2), "test")

    def test_pgettext(self):
        # Reset translation catalog to include other/locale/de
        self.old_locale_paths = settings.LOCALE_PATHS
        settings.LOCALE_PATHS += (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'other', 'locale'),)
        from django.utils.translation import trans_real
        trans_real._active = local()
        trans_real._translations = {}
        activate('de')

        self.assertEqual(pgettext("unexisting", "May"), u"May")
        self.assertEqual(pgettext("month name", "May"), u"Mai")
        self.assertEqual(pgettext("verb", "May"), u"Kann")
        self.assertEqual(npgettext("search", "%d result", "%d results", 4) % 4, u"4 Resultate")

        settings.LOCALE_PATHS = self.old_locale_paths

    def test_string_concat(self):
        """
        unicode(string_concat(...)) should not raise a TypeError - #4796
        """
        import django.utils.translation
        self.assertEqual(u'django', unicode(django.utils.translation.string_concat("dja", "ngo")))

    def test_safe_status(self):
        """
        Translating a string requiring no auto-escaping shouldn't change the "safe" status.
        """
        s = mark_safe('Password')
        self.assertEqual(SafeString, type(s))
        activate('de')
        try:
            self.assertEqual(SafeUnicode, type(ugettext(s)))
        finally:
            deactivate()
        self.assertEqual('aPassword', SafeString('a') + s)
        self.assertEqual('Passworda', s + SafeString('a'))
        self.assertEqual('Passworda', s + mark_safe('a'))
        self.assertEqual('aPassword', mark_safe('a') + s)
        self.assertEqual('as', mark_safe('a') + mark_safe('s'))

    def test_maclines(self):
        """
        Translations on files with mac or dos end of lines will be converted
        to unix eof in .po catalogs, and they have to match when retrieved
        """
        from django.utils.translation.trans_real import translation
        ca_translation = translation('ca')
        ca_translation._catalog[u'Mac\nEOF\n'] = u'Catalan Mac\nEOF\n'
        ca_translation._catalog[u'Win\nEOF\n'] = u'Catalan Win\nEOF\n'
        activate('ca')
        try:
            self.assertEqual(u'Catalan Mac\nEOF\n', ugettext(u'Mac\rEOF\r'))
            self.assertEqual(u'Catalan Win\nEOF\n', ugettext(u'Win\r\nEOF\r\n'))
        finally:
            deactivate()

    def test_to_locale(self):
        """
        Tests the to_locale function and the special case of Serbian Latin
        (refs #12230 and r11299)
        """
        self.assertEqual(to_locale('en-us'), 'en_US')
        self.assertEqual(to_locale('sr-lat'), 'sr_Lat')

    def test_to_language(self):
        """
        Test the to_language function
        """
        from django.utils.translation.trans_real import to_language
        self.assertEqual(to_language('en_US'), 'en-us')
        self.assertEqual(to_language('sr_Lat'), 'sr-lat')


class FormattingTests(TestCase):

    def setUp(self):
        self.use_i18n = settings.USE_I18N
        self.use_l10n = settings.USE_L10N
        self.use_thousand_separator = settings.USE_THOUSAND_SEPARATOR
        self.thousand_separator = settings.THOUSAND_SEPARATOR
        self.number_grouping = settings.NUMBER_GROUPING
        self.n = decimal.Decimal('66666.666')
        self.f = 99999.999
        self.d = datetime.date(2009, 12, 31)
        self.dt = datetime.datetime(2009, 12, 31, 20, 50)
        self.t = datetime.time(10, 15, 48)
        self.l = 10000L
        self.ctxt = Context({
            'n': self.n,
            't': self.t,
            'd': self.d,
            'dt': self.dt,
            'f': self.f,
            'l': self.l,
        })

    def tearDown(self):
        # Restore defaults
        settings.USE_I18N = self.use_i18n
        settings.USE_L10N = self.use_l10n
        settings.USE_THOUSAND_SEPARATOR = self.use_thousand_separator
        settings.THOUSAND_SEPARATOR = self.thousand_separator
        settings.NUMBER_GROUPING = self.number_grouping

    def test_locale_independent(self):
        """
        Localization of numbers
        """
        settings.USE_L10N = True
        settings.USE_THOUSAND_SEPARATOR = False
        self.assertEqual(u'66666.66', nformat(self.n, decimal_sep='.', decimal_pos=2, grouping=3, thousand_sep=','))
        self.assertEqual(u'66666A6', nformat(self.n, decimal_sep='A', decimal_pos=1, grouping=1, thousand_sep='B'))

        settings.USE_THOUSAND_SEPARATOR = True
        self.assertEqual(u'66,666.66', nformat(self.n, decimal_sep='.', decimal_pos=2, grouping=3, thousand_sep=','))
        self.assertEqual(u'6B6B6B6B6A6', nformat(self.n, decimal_sep='A', decimal_pos=1, grouping=1, thousand_sep='B'))
        self.assertEqual(u'-66666.6', nformat(-66666.666, decimal_sep='.', decimal_pos=1))
        self.assertEqual(u'-66666.0', nformat(int('-66666'), decimal_sep='.', decimal_pos=1))
        self.assertEqual(u'10000.0', nformat(self.l, decimal_sep='.', decimal_pos=1))

        # date filter
        self.assertEqual(u'31.12.2009 в 20:50', Template('{{ dt|date:"d.m.Y в H:i" }}').render(self.ctxt))
        self.assertEqual(u'⌚ 10:15', Template('{{ t|time:"⌚ H:i" }}').render(self.ctxt))

    def test_l10n_disabled(self):
        """
        Catalan locale with format i18n disabled translations will be used,
        but not formats
        """
        settings.USE_L10N = False
        activate('ca')
        try:
            self.assertEqual(u'N j, Y', get_format('DATE_FORMAT'))
            self.assertEqual(0, get_format('FIRST_DAY_OF_WEEK'))
            self.assertEqual(u'.', get_format('DECIMAL_SEPARATOR'))
            self.assertEqual(u'10:15 a.m.', time_format(self.t))
            self.assertEqual(u'des. 31, 2009', date_format(self.d))
            self.assertEqual(u'desembre 2009', date_format(self.d, 'YEAR_MONTH_FORMAT'))
            self.assertEqual(u'12/31/2009 8:50 p.m.', date_format(self.dt, 'SHORT_DATETIME_FORMAT'))
            self.assertEqual(u'No localizable', localize('No localizable'))
            self.assertEqual(u'66666.666', localize(self.n))
            self.assertEqual(u'99999.999', localize(self.f))
            self.assertEqual(u'10000', localize(self.l))
            self.assertEqual(u'des. 31, 2009', localize(self.d))
            self.assertEqual(u'des. 31, 2009, 8:50 p.m.', localize(self.dt))
            self.assertEqual(u'66666.666', Template('{{ n }}').render(self.ctxt))
            self.assertEqual(u'99999.999', Template('{{ f }}').render(self.ctxt))
            self.assertEqual(u'des. 31, 2009', Template('{{ d }}').render(self.ctxt))
            self.assertEqual(u'des. 31, 2009, 8:50 p.m.', Template('{{ dt }}').render(self.ctxt))
            self.assertEqual(u'66666.67', Template('{{ n|floatformat:2 }}').render(self.ctxt))
            self.assertEqual(u'100000.0', Template('{{ f|floatformat }}').render(self.ctxt))
            self.assertEqual(u'10:15 a.m.', Template('{{ t|time:"TIME_FORMAT" }}').render(self.ctxt))
            self.assertEqual(u'12/31/2009', Template('{{ d|date:"SHORT_DATE_FORMAT" }}').render(self.ctxt))
            self.assertEqual(u'12/31/2009 8:50 p.m.', Template('{{ dt|date:"SHORT_DATETIME_FORMAT" }}').render(self.ctxt))

            form = I18nForm({
                'decimal_field': u'66666,666',
                'float_field': u'99999,999',
                'date_field': u'31/12/2009',
                'datetime_field': u'31/12/2009 20:50',
                'time_field': u'20:50',
                'integer_field': u'1.234',
            })
            self.assertEqual(False, form.is_valid())
            self.assertEqual([u'Introdu\xefu un n\xfamero.'], form.errors['float_field'])
            self.assertEqual([u'Introdu\xefu un n\xfamero.'], form.errors['decimal_field'])
            self.assertEqual([u'Introdu\xefu una data v\xe0lida.'], form.errors['date_field'])
            self.assertEqual([u'Introdu\xefu una data/hora v\xe0lides.'], form.errors['datetime_field'])
            self.assertEqual([u'Introdu\xefu un n\xfamero sencer.'], form.errors['integer_field'])

            form2 = SelectDateForm({
                'date_field_month': u'12',
                'date_field_day': u'31',
                'date_field_year': u'2009'
            })
            self.assertEqual(True, form2.is_valid())
            self.assertEqual(datetime.date(2009, 12, 31), form2.cleaned_data['date_field'])
            self.assertEqual(
                u'<select name="mydate_month" id="id_mydate_month">\n<option value="1">gener</option>\n<option value="2">febrer</option>\n<option value="3">mar\xe7</option>\n<option value="4">abril</option>\n<option value="5">maig</option>\n<option value="6">juny</option>\n<option value="7">juliol</option>\n<option value="8">agost</option>\n<option value="9">setembre</option>\n<option value="10">octubre</option>\n<option value="11">novembre</option>\n<option value="12" selected="selected">desembre</option>\n</select>\n<select name="mydate_day" id="id_mydate_day">\n<option value="1">1</option>\n<option value="2">2</option>\n<option value="3">3</option>\n<option value="4">4</option>\n<option value="5">5</option>\n<option value="6">6</option>\n<option value="7">7</option>\n<option value="8">8</option>\n<option value="9">9</option>\n<option value="10">10</option>\n<option value="11">11</option>\n<option value="12">12</option>\n<option value="13">13</option>\n<option value="14">14</option>\n<option value="15">15</option>\n<option value="16">16</option>\n<option value="17">17</option>\n<option value="18">18</option>\n<option value="19">19</option>\n<option value="20">20</option>\n<option value="21">21</option>\n<option value="22">22</option>\n<option value="23">23</option>\n<option value="24">24</option>\n<option value="25">25</option>\n<option value="26">26</option>\n<option value="27">27</option>\n<option value="28">28</option>\n<option value="29">29</option>\n<option value="30">30</option>\n<option value="31" selected="selected">31</option>\n</select>\n<select name="mydate_year" id="id_mydate_year">\n<option value="2009" selected="selected">2009</option>\n<option value="2010">2010</option>\n<option value="2011">2011</option>\n<option value="2012">2012</option>\n<option value="2013">2013</option>\n<option value="2014">2014</option>\n<option value="2015">2015</option>\n<option value="2016">2016</option>\n<option value="2017">2017</option>\n<option value="2018">2018</option>\n</select>',
                SelectDateWidget(years=range(2009, 2019)).render('mydate', datetime.date(2009, 12, 31))
            )

            # We shouldn't change the behavior of the floatformat filter re:
            # thousand separator and grouping when USE_L10N is False even
            # if the USE_THOUSAND_SEPARATOR, NUMBER_GROUPING and
            # THOUSAND_SEPARATOR settings are specified
            settings.USE_THOUSAND_SEPARATOR = True
            settings.NUMBER_GROUPING = 1
            settings.THOUSAND_SEPARATOR = '!'
            self.assertEqual(u'66666.67', Template('{{ n|floatformat:2 }}').render(self.ctxt))
            self.assertEqual(u'100000.0', Template('{{ f|floatformat }}').render(self.ctxt))
        finally:
            deactivate()

    def test_l10n_enabled(self):
        settings.USE_L10N = True
        # Catalan locale
        activate('ca')
        try:
            self.assertEqual('j \de F \de Y', get_format('DATE_FORMAT'))
            self.assertEqual(1, get_format('FIRST_DAY_OF_WEEK'))
            self.assertEqual(',', get_format('DECIMAL_SEPARATOR'))
            self.assertEqual(u'10:15:48', time_format(self.t))
            self.assertEqual(u'31 de desembre de 2009', date_format(self.d))
            self.assertEqual(u'desembre del 2009', date_format(self.d, 'YEAR_MONTH_FORMAT'))
            self.assertEqual(u'31/12/2009 20:50', date_format(self.dt, 'SHORT_DATETIME_FORMAT'))
            self.assertEqual('No localizable', localize('No localizable'))

            settings.USE_THOUSAND_SEPARATOR = True
            self.assertEqual(u'66.666,666', localize(self.n))
            self.assertEqual(u'99.999,999', localize(self.f))
            self.assertEqual(u'10.000', localize(self.l))
            self.assertEqual(u'True', localize(True))

            settings.USE_THOUSAND_SEPARATOR = False
            self.assertEqual(u'66666,666', localize(self.n))
            self.assertEqual(u'99999,999', localize(self.f))
            self.assertEqual(u'10000', localize(self.l))
            self.assertEqual(u'31 de desembre de 2009', localize(self.d))
            self.assertEqual(u'31 de desembre de 2009 a les 20:50', localize(self.dt))

            settings.USE_THOUSAND_SEPARATOR = True
            self.assertEqual(u'66.666,666', Template('{{ n }}').render(self.ctxt))
            self.assertEqual(u'99.999,999', Template('{{ f }}').render(self.ctxt))
            self.assertEqual(u'10.000', Template('{{ l }}').render(self.ctxt))

            form3 = I18nForm({
                'decimal_field': u'66.666,666',
                'float_field': u'99.999,999',
                'date_field': u'31/12/2009',
                'datetime_field': u'31/12/2009 20:50',
                'time_field': u'20:50',
                'integer_field': u'1.234',
            })
            self.assertEqual(True, form3.is_valid())
            self.assertEqual(decimal.Decimal('66666.666'), form3.cleaned_data['decimal_field'])
            self.assertEqual(99999.999, form3.cleaned_data['float_field'])
            self.assertEqual(datetime.date(2009, 12, 31), form3.cleaned_data['date_field'])
            self.assertEqual(datetime.datetime(2009, 12, 31, 20, 50), form3.cleaned_data['datetime_field'])
            self.assertEqual(datetime.time(20, 50), form3.cleaned_data['time_field'])
            self.assertEqual(1234, form3.cleaned_data['integer_field'])

            settings.USE_THOUSAND_SEPARATOR = False
            self.assertEqual(u'66666,666', Template('{{ n }}').render(self.ctxt))
            self.assertEqual(u'99999,999', Template('{{ f }}').render(self.ctxt))
            self.assertEqual(u'31 de desembre de 2009', Template('{{ d }}').render(self.ctxt))
            self.assertEqual(u'31 de desembre de 2009 a les 20:50', Template('{{ dt }}').render(self.ctxt))
            self.assertEqual(u'66666,67', Template('{{ n|floatformat:2 }}').render(self.ctxt))
            self.assertEqual(u'100000,0', Template('{{ f|floatformat }}').render(self.ctxt))
            self.assertEqual(u'10:15:48', Template('{{ t|time:"TIME_FORMAT" }}').render(self.ctxt))
            self.assertEqual(u'31/12/2009', Template('{{ d|date:"SHORT_DATE_FORMAT" }}').render(self.ctxt))
            self.assertEqual(u'31/12/2009 20:50', Template('{{ dt|date:"SHORT_DATETIME_FORMAT" }}').render(self.ctxt))

            form4 = I18nForm({
                'decimal_field': u'66666,666',
                'float_field': u'99999,999',
                'date_field': u'31/12/2009',
                'datetime_field': u'31/12/2009 20:50',
                'time_field': u'20:50',
                'integer_field': u'1234',
            })
            self.assertEqual(True, form4.is_valid())
            self.assertEqual(decimal.Decimal('66666.666'), form4.cleaned_data['decimal_field'])
            self.assertEqual(99999.999, form4.cleaned_data['float_field'])
            self.assertEqual(datetime.date(2009, 12, 31), form4.cleaned_data['date_field'])
            self.assertEqual(datetime.datetime(2009, 12, 31, 20, 50), form4.cleaned_data['datetime_field'])
            self.assertEqual(datetime.time(20, 50), form4.cleaned_data['time_field'])
            self.assertEqual(1234, form4.cleaned_data['integer_field'])

            form5 = SelectDateForm({
                'date_field_month': u'12',
                'date_field_day': u'31',
                'date_field_year': u'2009'
            })
            self.assertEqual(True, form5.is_valid())
            self.assertEqual(datetime.date(2009, 12, 31), form5.cleaned_data['date_field'])
            self.assertEqual(
                u'<select name="mydate_day" id="id_mydate_day">\n<option value="1">1</option>\n<option value="2">2</option>\n<option value="3">3</option>\n<option value="4">4</option>\n<option value="5">5</option>\n<option value="6">6</option>\n<option value="7">7</option>\n<option value="8">8</option>\n<option value="9">9</option>\n<option value="10">10</option>\n<option value="11">11</option>\n<option value="12">12</option>\n<option value="13">13</option>\n<option value="14">14</option>\n<option value="15">15</option>\n<option value="16">16</option>\n<option value="17">17</option>\n<option value="18">18</option>\n<option value="19">19</option>\n<option value="20">20</option>\n<option value="21">21</option>\n<option value="22">22</option>\n<option value="23">23</option>\n<option value="24">24</option>\n<option value="25">25</option>\n<option value="26">26</option>\n<option value="27">27</option>\n<option value="28">28</option>\n<option value="29">29</option>\n<option value="30">30</option>\n<option value="31" selected="selected">31</option>\n</select>\n<select name="mydate_month" id="id_mydate_month">\n<option value="1">gener</option>\n<option value="2">febrer</option>\n<option value="3">mar\xe7</option>\n<option value="4">abril</option>\n<option value="5">maig</option>\n<option value="6">juny</option>\n<option value="7">juliol</option>\n<option value="8">agost</option>\n<option value="9">setembre</option>\n<option value="10">octubre</option>\n<option value="11">novembre</option>\n<option value="12" selected="selected">desembre</option>\n</select>\n<select name="mydate_year" id="id_mydate_year">\n<option value="2009" selected="selected">2009</option>\n<option value="2010">2010</option>\n<option value="2011">2011</option>\n<option value="2012">2012</option>\n<option value="2013">2013</option>\n<option value="2014">2014</option>\n<option value="2015">2015</option>\n<option value="2016">2016</option>\n<option value="2017">2017</option>\n<option value="2018">2018</option>\n</select>',
                SelectDateWidget(years=range(2009, 2019)).render('mydate', datetime.date(2009, 12, 31))
            )
        finally:
            deactivate()

        # Russian locale (with E as month)
        activate('ru')
        try:
            self.assertEqual(
                    u'<select name="mydate_day" id="id_mydate_day">\n<option value="1">1</option>\n<option value="2">2</option>\n<option value="3">3</option>\n<option value="4">4</option>\n<option value="5">5</option>\n<option value="6">6</option>\n<option value="7">7</option>\n<option value="8">8</option>\n<option value="9">9</option>\n<option value="10">10</option>\n<option value="11">11</option>\n<option value="12">12</option>\n<option value="13">13</option>\n<option value="14">14</option>\n<option value="15">15</option>\n<option value="16">16</option>\n<option value="17">17</option>\n<option value="18">18</option>\n<option value="19">19</option>\n<option value="20">20</option>\n<option value="21">21</option>\n<option value="22">22</option>\n<option value="23">23</option>\n<option value="24">24</option>\n<option value="25">25</option>\n<option value="26">26</option>\n<option value="27">27</option>\n<option value="28">28</option>\n<option value="29">29</option>\n<option value="30">30</option>\n<option value="31" selected="selected">31</option>\n</select>\n<select name="mydate_month" id="id_mydate_month">\n<option value="1">\u042f\u043d\u0432\u0430\u0440\u044c</option>\n<option value="2">\u0424\u0435\u0432\u0440\u0430\u043b\u044c</option>\n<option value="3">\u041c\u0430\u0440\u0442</option>\n<option value="4">\u0410\u043f\u0440\u0435\u043b\u044c</option>\n<option value="5">\u041c\u0430\u0439</option>\n<option value="6">\u0418\u044e\u043d\u044c</option>\n<option value="7">\u0418\u044e\u043b\u044c</option>\n<option value="8">\u0410\u0432\u0433\u0443\u0441\u0442</option>\n<option value="9">\u0421\u0435\u043d\u0442\u044f\u0431\u0440\u044c</option>\n<option value="10">\u041e\u043a\u0442\u044f\u0431\u0440\u044c</option>\n<option value="11">\u041d\u043e\u044f\u0431\u0440\u044c</option>\n<option value="12" selected="selected">\u0414\u0435\u043a\u0430\u0431\u0440\u044c</option>\n</select>\n<select name="mydate_year" id="id_mydate_year">\n<option value="2009" selected="selected">2009</option>\n<option value="2010">2010</option>\n<option value="2011">2011</option>\n<option value="2012">2012</option>\n<option value="2013">2013</option>\n<option value="2014">2014</option>\n<option value="2015">2015</option>\n<option value="2016">2016</option>\n<option value="2017">2017</option>\n<option value="2018">2018</option>\n</select>',
                    SelectDateWidget(years=range(2009, 2019)).render('mydate', datetime.date(2009, 12, 31))
            )
        finally:
            deactivate()

        # English locale
        activate('en')
        try:
            self.assertEqual('N j, Y', get_format('DATE_FORMAT'))
            self.assertEqual(0, get_format('FIRST_DAY_OF_WEEK'))
            self.assertEqual('.', get_format('DECIMAL_SEPARATOR'))
            self.assertEqual(u'Dec. 31, 2009', date_format(self.d))
            self.assertEqual(u'December 2009', date_format(self.d, 'YEAR_MONTH_FORMAT'))
            self.assertEqual(u'12/31/2009 8:50 p.m.', date_format(self.dt, 'SHORT_DATETIME_FORMAT'))
            self.assertEqual(u'No localizable', localize('No localizable'))

            settings.USE_THOUSAND_SEPARATOR = True
            self.assertEqual(u'66,666.666', localize(self.n))
            self.assertEqual(u'99,999.999', localize(self.f))
            self.assertEqual(u'10,000', localize(self.l))

            settings.USE_THOUSAND_SEPARATOR = False
            self.assertEqual(u'66666.666', localize(self.n))
            self.assertEqual(u'99999.999', localize(self.f))
            self.assertEqual(u'10000', localize(self.l))
            self.assertEqual(u'Dec. 31, 2009', localize(self.d))
            self.assertEqual(u'Dec. 31, 2009, 8:50 p.m.', localize(self.dt))

            settings.USE_THOUSAND_SEPARATOR = True
            self.assertEqual(u'66,666.666', Template('{{ n }}').render(self.ctxt))
            self.assertEqual(u'99,999.999', Template('{{ f }}').render(self.ctxt))
            self.assertEqual(u'10,000', Template('{{ l }}').render(self.ctxt))

            settings.USE_THOUSAND_SEPARATOR = False
            self.assertEqual(u'66666.666', Template('{{ n }}').render(self.ctxt))
            self.assertEqual(u'99999.999', Template('{{ f }}').render(self.ctxt))
            self.assertEqual(u'Dec. 31, 2009', Template('{{ d }}').render(self.ctxt))
            self.assertEqual(u'Dec. 31, 2009, 8:50 p.m.', Template('{{ dt }}').render(self.ctxt))
            self.assertEqual(u'66666.67', Template('{{ n|floatformat:2 }}').render(self.ctxt))
            self.assertEqual(u'100000.0', Template('{{ f|floatformat }}').render(self.ctxt))
            self.assertEqual(u'12/31/2009', Template('{{ d|date:"SHORT_DATE_FORMAT" }}').render(self.ctxt))
            self.assertEqual(u'12/31/2009 8:50 p.m.', Template('{{ dt|date:"SHORT_DATETIME_FORMAT" }}').render(self.ctxt))

            form5 = I18nForm({
                'decimal_field': u'66666.666',
                'float_field': u'99999.999',
                'date_field': u'12/31/2009',
                'datetime_field': u'12/31/2009 20:50',
                'time_field': u'20:50',
                'integer_field': u'1234',
            })
            self.assertEqual(True, form5.is_valid())
            self.assertEqual(decimal.Decimal('66666.666'), form5.cleaned_data['decimal_field'])
            self.assertEqual(99999.999, form5.cleaned_data['float_field'])
            self.assertEqual(datetime.date(2009, 12, 31), form5.cleaned_data['date_field'])
            self.assertEqual(datetime.datetime(2009, 12, 31, 20, 50), form5.cleaned_data['datetime_field'])
            self.assertEqual(datetime.time(20, 50), form5.cleaned_data['time_field'])
            self.assertEqual(1234, form5.cleaned_data['integer_field'])

            form6 = SelectDateForm({
                'date_field_month': u'12',
                'date_field_day': u'31',
                'date_field_year': u'2009'
            })
            self.assertEqual(True, form6.is_valid())
            self.assertEqual(datetime.date(2009, 12, 31), form6.cleaned_data['date_field'])
            self.assertEqual(
                u'<select name="mydate_month" id="id_mydate_month">\n<option value="1">January</option>\n<option value="2">February</option>\n<option value="3">March</option>\n<option value="4">April</option>\n<option value="5">May</option>\n<option value="6">June</option>\n<option value="7">July</option>\n<option value="8">August</option>\n<option value="9">September</option>\n<option value="10">October</option>\n<option value="11">November</option>\n<option value="12" selected="selected">December</option>\n</select>\n<select name="mydate_day" id="id_mydate_day">\n<option value="1">1</option>\n<option value="2">2</option>\n<option value="3">3</option>\n<option value="4">4</option>\n<option value="5">5</option>\n<option value="6">6</option>\n<option value="7">7</option>\n<option value="8">8</option>\n<option value="9">9</option>\n<option value="10">10</option>\n<option value="11">11</option>\n<option value="12">12</option>\n<option value="13">13</option>\n<option value="14">14</option>\n<option value="15">15</option>\n<option value="16">16</option>\n<option value="17">17</option>\n<option value="18">18</option>\n<option value="19">19</option>\n<option value="20">20</option>\n<option value="21">21</option>\n<option value="22">22</option>\n<option value="23">23</option>\n<option value="24">24</option>\n<option value="25">25</option>\n<option value="26">26</option>\n<option value="27">27</option>\n<option value="28">28</option>\n<option value="29">29</option>\n<option value="30">30</option>\n<option value="31" selected="selected">31</option>\n</select>\n<select name="mydate_year" id="id_mydate_year">\n<option value="2009" selected="selected">2009</option>\n<option value="2010">2010</option>\n<option value="2011">2011</option>\n<option value="2012">2012</option>\n<option value="2013">2013</option>\n<option value="2014">2014</option>\n<option value="2015">2015</option>\n<option value="2016">2016</option>\n<option value="2017">2017</option>\n<option value="2018">2018</option>\n</select>',
                SelectDateWidget(years=range(2009, 2019)).render('mydate', datetime.date(2009, 12, 31))
            )
        finally:
            deactivate()

    def test_sub_locales(self):
        """
        Check if sublocales fall back to the main locale
        """
        settings.USE_L10N = True
        activate('de-at')
        settings.USE_THOUSAND_SEPARATOR = True
        try:
            self.assertEqual(u'66.666,666', Template('{{ n }}').render(self.ctxt))
        finally:
            deactivate()

        activate('es-us')
        try:
            self.assertEqual(u'31 de diciembre de 2009', date_format(self.d))
        finally:
            deactivate()

    def test_localized_input(self):
        """
        Tests if form input is correctly localized
        """
        settings.USE_L10N = True
        activate('de-at')
        try:
            form6 = CompanyForm({
                'name': u'acme',
                'date_added': datetime.datetime(2009, 12, 31, 6, 0, 0),
                'cents_payed': decimal.Decimal('59.47'),
                'products_delivered': 12000,
            })
            self.assertEqual(True, form6.is_valid())
            self.assertEqual(
                form6.as_ul(),
                u'<li><label for="id_name">Name:</label> <input id="id_name" type="text" name="name" value="acme" maxlength="50" /></li>\n<li><label for="id_date_added">Date added:</label> <input type="text" name="date_added" value="31.12.2009 06:00:00" id="id_date_added" /></li>\n<li><label for="id_cents_payed">Cents payed:</label> <input type="text" name="cents_payed" value="59,47" id="id_cents_payed" /></li>\n<li><label for="id_products_delivered">Products delivered:</label> <input type="text" name="products_delivered" value="12000" id="id_products_delivered" /></li>'
            )
            self.assertEqual(localize_input(datetime.datetime(2009, 12, 31, 6, 0, 0)), '31.12.2009 06:00:00')
            self.assertEqual(datetime.datetime(2009, 12, 31, 6, 0, 0), form6.cleaned_data['date_added'])
            settings.USE_THOUSAND_SEPARATOR = True
            # Checking for the localized "products_delivered" field
            self.assertTrue(u'<input type="text" name="products_delivered" value="12.000" id="id_products_delivered" />' in form6.as_ul())
        finally:
            deactivate()

    def test_iter_format_modules(self):
        """
        Tests the iter_format_modules function.
        """
        activate('de-at')
        old_format_module_path = settings.FORMAT_MODULE_PATH
        try:
            settings.USE_L10N = True
            de_format_mod = import_module('django.conf.locale.de.formats')
            self.assertEqual(list(iter_format_modules('de')), [de_format_mod])
            settings.FORMAT_MODULE_PATH = 'regressiontests.i18n.other.locale'
            test_de_format_mod = import_module('regressiontests.i18n.other.locale.de.formats')
            self.assertEqual(list(iter_format_modules('de')), [test_de_format_mod, de_format_mod])
        finally:
            settings.FORMAT_MODULE_PATH = old_format_module_path
            deactivate()

    def test_iter_format_modules_stability(self):
        """
        Tests the iter_format_modules function always yields format modules in
        a stable and correct order in presence of both base ll and ll_CC formats.
        """
        settings.USE_L10N = True
        en_format_mod = import_module('django.conf.locale.en.formats')
        en_gb_format_mod = import_module('django.conf.locale.en_GB.formats')
        self.assertEqual(list(iter_format_modules('en-gb')), [en_gb_format_mod, en_format_mod])

    def test_get_format_modules_stability(self):
        activate('de')
        old_format_module_path = settings.FORMAT_MODULE_PATH
        settings.FORMAT_MODULE_PATH = 'regressiontests.i18n.other.locale'
        try:
            settings.USE_L10N = True
            old = "%r" % get_format_modules(reverse=True)
            new = "%r" % get_format_modules(reverse=True) # second try
            self.assertEqual(new, old, 'Value returned by get_formats_modules() must be preserved between calls.')
        finally:
            settings.FORMAT_MODULE_PATH = old_format_module_path
            deactivate()

    def test_localize_templatetag_and_filter(self):
        """
        Tests the {% localize %} templatetag
        """
        context = Context({'value': 3.14 })
        template1 = Template("{% load l10n %}{% localize %}{{ value }}{% endlocalize %};{% localize on %}{{ value }}{% endlocalize %}")
        template2 = Template("{% load l10n %}{{ value }};{% localize off %}{{ value }};{% endlocalize %}{{ value }}")
        template3 = Template('{% load l10n %}{{ value }};{{ value|unlocalize }}')
        template4 = Template('{% load l10n %}{{ value }};{{ value|localize }}')
        output1 = '3,14;3,14'
        output2 = '3,14;3.14;3,14'
        output3 = '3,14;3.14'
        output4 = '3.14;3,14'
        old_localize = settings.USE_L10N
        try:
            activate('de')
            settings.USE_L10N = False
            self.assertEqual(template1.render(context), output1)
            self.assertEqual(template4.render(context), output4)
            settings.USE_L10N = True
            self.assertEqual(template1.render(context), output1)
            self.assertEqual(template2.render(context), output2)
            self.assertEqual(template3.render(context), output3)
        finally:
            deactivate()
            settings.USE_L10N = old_localize

class MiscTests(TestCase):

    def test_parse_spec_http_header(self):
        """
        Testing HTTP header parsing. First, we test that we can parse the
        values according to the spec (and that we extract all the pieces in
        the right order).
        """
        from django.utils.translation.trans_real import parse_accept_lang_header
        p = parse_accept_lang_header
        # Good headers.
        self.assertEqual([('de', 1.0)], p('de'))
        self.assertEqual([('en-AU', 1.0)], p('en-AU'))
        self.assertEqual([('*', 1.0)], p('*;q=1.00'))
        self.assertEqual([('en-AU', 0.123)], p('en-AU;q=0.123'))
        self.assertEqual([('en-au', 0.5)], p('en-au;q=0.5'))
        self.assertEqual([('en-au', 1.0)], p('en-au;q=1.0'))
        self.assertEqual([('da', 1.0), ('en', 0.5), ('en-gb', 0.25)], p('da, en-gb;q=0.25, en;q=0.5'))
        self.assertEqual([('en-au-xx', 1.0)], p('en-au-xx'))
        self.assertEqual([('de', 1.0), ('en-au', 0.75), ('en-us', 0.5), ('en', 0.25), ('es', 0.125), ('fa', 0.125)], p('de,en-au;q=0.75,en-us;q=0.5,en;q=0.25,es;q=0.125,fa;q=0.125'))
        self.assertEqual([('*', 1.0)], p('*'))
        self.assertEqual([('de', 1.0)], p('de;q=0.'))
        self.assertEqual([], p(''))

        # Bad headers; should always return [].
        self.assertEqual([], p('en-gb;q=1.0000'))
        self.assertEqual([], p('en;q=0.1234'))
        self.assertEqual([], p('en;q=.2'))
        self.assertEqual([], p('abcdefghi-au'))
        self.assertEqual([], p('**'))
        self.assertEqual([], p('en,,gb'))
        self.assertEqual([], p('en-au;q=0.1.0'))
        self.assertEqual([], p('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXZ,en'))
        self.assertEqual([], p('da, en-gb;q=0.8, en;q=0.7,#'))
        self.assertEqual([], p('de;q=2.0'))
        self.assertEqual([], p('de;q=0.a'))
        self.assertEqual([], p(''))

    def test_parse_literal_http_header(self):
        """
        Now test that we parse a literal HTTP header correctly.
        """
        from django.utils.translation.trans_real import get_language_from_request
        g = get_language_from_request
        from django.http import HttpRequest
        r = HttpRequest
        r.COOKIES = {}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'pt-br'}
        self.assertEqual('pt-br', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'pt'}
        self.assertEqual('pt', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'es,de'}
        self.assertEqual('es', g(r))

        r.META = {'HTTP_ACCEPT_LANGUAGE': 'es-ar,de'}
        self.assertEqual('es-ar', g(r))

        # Python 2.3 and 2.4 return slightly different results for completely
        # bogus locales, so we omit this test for that anything below 2.4.
        # It's relatively harmless in any cases (GIGO). This also means this
        # won't be executed on Jython currently, but life's like that
        # sometimes. (On those platforms, passing in a truly bogus locale
        # will get you the default locale back.)
        if sys.version_info >= (2, 5):
            # This test assumes there won't be a Django translation to a US
            # variation of the Spanish language, a safe assumption. When the
            # user sets it as the preferred language, the main 'es'
            # translation should be selected instead.
            r.META = {'HTTP_ACCEPT_LANGUAGE': 'es-us'}
            self.assertEqual(g(r), 'es')

        # This tests the following scenario: there isn't a main language (zh)
        # translation of Django but there is a translation to variation (zh_CN)
        # the user sets zh-cn as the preferred language, it should be selected
        # by Django without falling back nor ignoring it.
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'zh-cn,de'}
        self.assertEqual(g(r), 'zh-cn')

    def test_parse_language_cookie(self):
        """
        Now test that we parse language preferences stored in a cookie correctly.
        """
        from django.utils.translation.trans_real import get_language_from_request
        g = get_language_from_request
        from django.http import HttpRequest
        r = HttpRequest
        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'pt-br'}
        r.META = {}
        self.assertEqual('pt-br', g(r))

        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'pt'}
        r.META = {}
        self.assertEqual('pt', g(r))

        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'es'}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'de'}
        self.assertEqual('es', g(r))

        # Python 2.3 and 2.4 return slightly different results for completely
        # bogus locales, so we omit this test for that anything below 2.4.
        # It's relatively harmless in any cases (GIGO). This also means this
        # won't be executed on Jython currently, but life's like that
        # sometimes. (On those platforms, passing in a truly bogus locale
        # will get you the default locale back.)
        if sys.version_info >= (2, 5):
            # This test assumes there won't be a Django translation to a US
            # variation of the Spanish language, a safe assumption. When the
            # user sets it as the preferred language, the main 'es'
            # translation should be selected instead.
            r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'es-us'}
            r.META = {}
            self.assertEqual(g(r), 'es')

        # This tests the following scenario: there isn't a main language (zh)
        # translation of Django but there is a translation to variation (zh_CN)
        # the user sets zh-cn as the preferred language, it should be selected
        # by Django without falling back nor ignoring it.
        r.COOKIES = {settings.LANGUAGE_COOKIE_NAME: 'zh-cn'}
        r.META = {'HTTP_ACCEPT_LANGUAGE': 'de'}
        self.assertEqual(g(r), 'zh-cn')

class ResolutionOrderI18NTests(TestCase):

    def setUp(self):
        from django.utils.translation import trans_real
        # Okay, this is brutal, but we have no other choice to fully reset
        # the translation framework
        trans_real._active = local()
        trans_real._translations = {}
        activate('de')

    def tearDown(self):
        deactivate()

    def assertUgettext(self, msgid, msgstr):
        result = ugettext(msgid)
        self.assertTrue(msgstr in result, ("The string '%s' isn't in the "
            "translation of '%s'; the actual result is '%s'." % (msgstr, msgid, result)))

class AppResolutionOrderI18NTests(ResolutionOrderI18NTests):

    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = ['regressiontests.i18n.resolution'] + list(settings.INSTALLED_APPS)
        super(AppResolutionOrderI18NTests, self).setUp()

    def tearDown(self):
        settings.INSTALLED_APPS = self.old_installed_apps
        super(AppResolutionOrderI18NTests, self).tearDown()

    def test_app_translation(self):
        self.assertUgettext('Date/time', 'APP')

class LocalePathsResolutionOrderI18NTests(ResolutionOrderI18NTests):

    def setUp(self):
        self.old_locale_paths = settings.LOCALE_PATHS
        settings.LOCALE_PATHS += (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'other', 'locale'),)
        super(LocalePathsResolutionOrderI18NTests, self).setUp()

    def tearDown(self):
        settings.LOCALE_PATHS = self.old_locale_paths
        super(LocalePathsResolutionOrderI18NTests, self).tearDown()

    def test_locale_paths_translation(self):
        self.assertUgettext('Time', 'LOCALE_PATHS')

    def test_locale_paths_override_app_translation(self):
        old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['regressiontests.i18n.resolution']
        try:
            self.assertUgettext('Time', 'LOCALE_PATHS')
        finally:
            settings.INSTALLED_APPS = old_installed_apps

    def test_locale_paths_override_project_translation(self):
        old_settings_module = settings.SETTINGS_MODULE
        settings.SETTINGS_MODULE = 'regressiontests'
        try:
            self.assertUgettext('Date/time', 'LOCALE_PATHS')
        finally:
            settings.SETTINGS_MODULE = old_settings_module

class ProjectResolutionOrderI18NTests(ResolutionOrderI18NTests):

    def setUp(self):
        self.old_settings_module = settings.SETTINGS_MODULE
        settings.SETTINGS_MODULE = 'regressiontests'
        super(ProjectResolutionOrderI18NTests, self).setUp()

    def tearDown(self):
        settings.SETTINGS_MODULE = self.old_settings_module
        super(ProjectResolutionOrderI18NTests, self).tearDown()

    def test_project_translation(self):
        self.assertUgettext('Date/time', 'PROJECT')

    def test_project_override_app_translation(self):
        old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['regressiontests.i18n.resolution']
        try:
            self.assertUgettext('Date/time', 'PROJECT')
        finally:
            settings.INSTALLED_APPS = old_installed_apps

class DjangoFallbackResolutionOrderI18NTests(ResolutionOrderI18NTests):

    def test_django_fallback(self):
        self.assertEqual(ugettext('Date/time'), 'Datum/Zeit')


class TestModels(TestCase):
    def test_lazy(self):
        tm = TestModel()
        tm.save()

    def test_safestr(self):
        c = Company(cents_payed=12, products_delivered=1)
        c.name = SafeUnicode(u'Iñtërnâtiônàlizætiøn1')
        c.save()
        c.name = SafeString(u'Iñtërnâtiônàlizætiøn1'.encode('utf-8'))
        c.save()


class TestLanguageInfo(TestCase):
    def test_localized_language_info(self):
        li = get_language_info('de')
        self.assertEqual(li['code'], 'de')
        self.assertEqual(li['name_local'], u'Deutsch')
        self.assertEqual(li['name'], 'German')
        self.assertEqual(li['bidi'], False)


class MultipleLocaleActivationTests(TestCase):
    """
    Tests for template rendering behavior when multiple locales are activated
    during the lifetime of the same process.
    """
    def setUp(self):
        self._old_language = get_language()

    def tearDown(self):
        activate(self._old_language)

    def test_single_locale_activation(self):
        """
        Simple baseline behavior with one locale for all the supported i18n constructs.
        """
        activate('fr')
        self.assertEqual(Template("{{ _('Yes') }}").render(Context({})), 'Oui')
        self.assertEqual(Template("{% load i18n %}{% trans 'Yes' %}").render(Context({})), 'Oui')
        self.assertEqual(Template("{% load i18n %}{% blocktrans %}Yes{% endblocktrans %}").render(Context({})), 'Oui')

    # Literal marked up with _() in a filter expression

    def test_multiple_locale_filter(self):
        activate('de')
        t = Template("{% load i18n %}{{ 0|yesno:_('yes,no,maybe') }}")
        activate(self._old_language)
        activate('nl')
        self.assertEqual(t.render(Context({})), 'nee')

    def test_multiple_locale_filter_deactivate(self):
        activate('de')
        t = Template("{% load i18n %}{{ 0|yesno:_('yes,no,maybe') }}")
        deactivate()
        activate('nl')
        self.assertEqual(t.render(Context({})), 'nee')

    def test_multiple_locale_filter_direct_switch(self):
        activate('de')
        t = Template("{% load i18n %}{{ 0|yesno:_('yes,no,maybe') }}")
        activate('nl')
        self.assertEqual(t.render(Context({})), 'nee')

    # Literal marked up with _()

    def test_multiple_locale(self):
        activate('de')
        t = Template("{{ _('No') }}")
        activate(self._old_language)
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_deactivate(self):
        activate('de')
        t = Template("{{ _('No') }}")
        deactivate()
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_direct_switch(self):
        activate('de')
        t = Template("{{ _('No') }}")
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    # Literal marked up with _(), loading the i18n template tag library

    def test_multiple_locale_loadi18n(self):
        activate('de')
        t = Template("{% load i18n %}{{ _('No') }}")
        activate(self._old_language)
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_loadi18n_deactivate(self):
        activate('de')
        t = Template("{% load i18n %}{{ _('No') }}")
        deactivate()
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_loadi18n_direct_switch(self):
        activate('de')
        t = Template("{% load i18n %}{{ _('No') }}")
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    # trans i18n tag

    def test_multiple_locale_trans(self):
        activate('de')
        t = Template("{% load i18n %}{% trans 'No' %}")
        activate(self._old_language)
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_deactivate_trans(self):
        activate('de')
        t = Template("{% load i18n %}{% trans 'No' %}")
        deactivate()
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_direct_switch_trans(self):
        activate('de')
        t = Template("{% load i18n %}{% trans 'No' %}")
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    # blocktrans i18n tag

    def test_multiple_locale_btrans(self):
        activate('de')
        t = Template("{% load i18n %}{% blocktrans %}No{% endblocktrans %}")
        activate(self._old_language)
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_deactivate_btrans(self):
        activate('de')
        t = Template("{% load i18n %}{% blocktrans %}No{% endblocktrans %}")
        deactivate()
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')

    def test_multiple_locale_direct_switch_btrans(self):
        activate('de')
        t = Template("{% load i18n %}{% blocktrans %}No{% endblocktrans %}")
        activate('nl')
        self.assertEqual(t.render(Context({})), 'Nee')
