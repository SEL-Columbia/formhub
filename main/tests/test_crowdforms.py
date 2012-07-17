from test_base import MainTestCase

class TestCrowdforms(MainTestCase):

    def setUp(self):
        MainTestCase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()

        # turn on crowd forms for this form
        self.xform.is_crowd_form = True
        self.xform.save()

    def test_owner_can_submit_form(self):
        self._make_submissions(add_uuid=True)

    def test_other_user_can_submit_form(self):
        self._create_user_and_login('alice', 'alice')
        self._make_submissions(add_uuid=True)

    def test_anonymous_can_submit(self):
        self._logout()
        self._make_submissions('crowdforms', add_uuid=True)
