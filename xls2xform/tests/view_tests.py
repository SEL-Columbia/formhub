from django.test import TestCase
from django.test.client import Client


class TestIndexView(TestCase):
    def setUp(self):
        admin = User.objects.create(username="admin")
        admin.set_password("pass")
        admin.save()
        self.c = Client()
        #log in
        self.c.login(username="admin", password="pass")

    def post_new_form(self, root_name, title):
        response = self.c.post("/", {
            'root_name': root_name,
            'title': title,
        }, follow=True)
        if len(response.redirect_chain)==0:
            import pdb
            pdb.set_trace()
        self.assertTrue(len(response.redirect_chain) > 0)
        def spaces_subbed(str):
            import re
            return re.sub(" ", "_", str)
        self.assertEquals(response.redirect_chain[0][0], "http://testserver/edit/%s" % spaces_subbed(root_name))

    def test_new_forms(self):
        inputs = [
            ('root_name1', 'title1'),
            ('id string2', 'title2'), # definitely wont pass
            ('root_name3', 'title with space'),
            #('', 'title'), # definitely wont pass
            #('root_name', ''), # definitely wont pass
            ]
        for input in inputs:
            # Survey.objects.create({
            #     'root_name': input[0],
            #     'title': input[1]
            # })
            self.post_new_form(*input)