from test_base import MainTestCase

class TestCrowdforms(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()

        # turn on crowd forms for this form
        self.xform.is_crowd_form = True
        self.xform.save()

    def _close_crowdform(self):
        self.xform.is_crowd_form = False
        self.xform.save()

    def test_owner_can_submit_form(self):
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_other_user_can_submit_form(self):
        self._create_user_and_login('alice', 'alice')
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_anonymous_can_submit(self):
        self._logout()
        self._make_submissions('submit', add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_allow_owner_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._make_submissions(add_uuid=True)
        self.assertEqual(self.response.status_code, 201)

    def test_disallow_other_user_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._create_user_and_login('alice', 'alice')
        self._make_submissions(add_uuid=True, should_store=False)
        self.assertEqual(self.response.status_code, 405)

    def test_disallow_other_user_submit_to_closed_crowdform(self):
        self._close_crowdform()
        self._logout()
        self._make_submissions('submit', add_uuid=True, should_store=False)
        self.assertEqual(self.response.status_code, 405)
