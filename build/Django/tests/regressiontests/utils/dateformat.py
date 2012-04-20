from datetime import datetime, date
import os
import time

from django.utils.dateformat import format
from django.utils import dateformat, translation, unittest
from django.utils.tzinfo import FixedOffset, LocalTimezone


class DateFormatTests(unittest.TestCase):
    def setUp(self):
        self.old_TZ = os.environ.get('TZ')
        os.environ['TZ'] = 'Europe/Copenhagen'
        translation.activate('en-us')

        try:
            # Check if a timezone has been set
            time.tzset()
            self.tz_tests = True
        except AttributeError:
            # No timezone available. Don't run the tests that require a TZ
            self.tz_tests = False

    def tearDown(self):
        if self.old_TZ is None:
            del os.environ['TZ']
        else:
            os.environ['TZ'] = self.old_TZ

        # Cleanup - force re-evaluation of TZ environment variable.
        if self.tz_tests:
            time.tzset()

    def test_date(self):
        d = date(2009, 5, 16)
        self.assertEqual(date.fromtimestamp(int(format(d, 'U'))), d)

    def test_naive_datetime(self):
        dt = datetime(2009, 5, 16, 5, 30, 30)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U'))), dt)

    def test_datetime_with_local_tzinfo(self):
        ltz = LocalTimezone(datetime.now())
        dt = datetime(2009, 5, 16, 5, 30, 30, tzinfo=ltz)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U')), ltz), dt)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U'))), dt.replace(tzinfo=None))

    def test_datetime_with_tzinfo(self):
        tz = FixedOffset(-510)
        ltz = LocalTimezone(datetime.now())
        dt = datetime(2009, 5, 16, 5, 30, 30, tzinfo=tz)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U')), tz), dt)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U')), ltz), dt)
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U'))), dt.astimezone(ltz).replace(tzinfo=None))
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U')), tz).utctimetuple(), dt.utctimetuple())
        self.assertEqual(datetime.fromtimestamp(int(format(dt, 'U')), ltz).utctimetuple(), dt.utctimetuple())

    def test_epoch(self):
        utc = FixedOffset(0)
        udt = datetime(1970, 1, 1, tzinfo=utc)
        self.assertEqual(format(udt, 'U'), u'0')

    def test_empty_format(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, ''), u'')

    def test_am_pm(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, 'a'), u'p.m.')

    def test_date_formats(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)
        timestamp = datetime(2008, 5, 19, 11, 45, 23, 123456)

        self.assertEqual(dateformat.format(my_birthday, 'A'), u'PM')
        self.assertEqual(dateformat.format(timestamp, 'c'), u'2008-05-19T11:45:23.123456')
        self.assertEqual(dateformat.format(my_birthday, 'd'), u'08')
        self.assertEqual(dateformat.format(my_birthday, 'j'), u'8')
        self.assertEqual(dateformat.format(my_birthday, 'l'), u'Sunday')
        self.assertEqual(dateformat.format(my_birthday, 'L'), u'False')
        self.assertEqual(dateformat.format(my_birthday, 'm'), u'07')
        self.assertEqual(dateformat.format(my_birthday, 'M'), u'Jul')
        self.assertEqual(dateformat.format(my_birthday, 'b'), u'jul')
        self.assertEqual(dateformat.format(my_birthday, 'n'), u'7')
        self.assertEqual(dateformat.format(my_birthday, 'N'), u'July')

    def test_time_formats(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, 'P'), u'10 p.m.')
        self.assertEqual(dateformat.format(my_birthday, 's'), u'00')
        self.assertEqual(dateformat.format(my_birthday, 'S'), u'th')
        self.assertEqual(dateformat.format(my_birthday, 't'), u'31')
        self.assertEqual(dateformat.format(my_birthday, 'w'), u'0')
        self.assertEqual(dateformat.format(my_birthday, 'W'), u'27')
        self.assertEqual(dateformat.format(my_birthday, 'y'), u'79')
        self.assertEqual(dateformat.format(my_birthday, 'Y'), u'1979')
        self.assertEqual(dateformat.format(my_birthday, 'z'), u'189')

    def test_dateformat(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)

        self.assertEqual(dateformat.format(my_birthday, r'Y z \C\E\T'), u'1979 189 CET')

        self.assertEqual(dateformat.format(my_birthday, r'jS o\f F'), u'8th of July')

    def test_futuredates(self):
        the_future = datetime(2100, 10, 25, 0, 00)
        self.assertEqual(dateformat.format(the_future, r'Y'), u'2100')

    def test_timezones(self):
        my_birthday = datetime(1979, 7, 8, 22, 00)
        summertime = datetime(2005, 10, 30, 1, 00)
        wintertime = datetime(2005, 10, 30, 4, 00)
        timestamp = datetime(2008, 5, 19, 11, 45, 23, 123456)

        if self.tz_tests:
            self.assertEqual(dateformat.format(my_birthday, 'O'), u'+0100')
            self.assertEqual(dateformat.format(my_birthday, 'r'), u'Sun, 8 Jul 1979 22:00:00 +0100')
            self.assertEqual(dateformat.format(my_birthday, 'T'), u'CET')
            self.assertEqual(dateformat.format(my_birthday, 'U'), u'300315600')
            self.assertEqual(dateformat.format(timestamp, 'u'), u'123456')
            self.assertEqual(dateformat.format(my_birthday, 'Z'), u'3600')
            self.assertEqual(dateformat.format(summertime, 'I'), u'1')
            self.assertEqual(dateformat.format(summertime, 'O'), u'+0200')
            self.assertEqual(dateformat.format(wintertime, 'I'), u'0')
            self.assertEqual(dateformat.format(wintertime, 'O'), u'+0100')
