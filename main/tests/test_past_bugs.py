from test_process import TestSite


class TestCSVExport(TestSite):
    """
    We had a problem when two users published the same form that the
    CSV export would break.
    """

    def test_process(self):
        TestSite.test_process(self)
        TestSite.test_process(self, "doug", "doug")
