from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from dmt.claim.models import Claim, PMTUser
from dmt.main.models import Item
from .factories import ProjectFactory, MilestoneFactory, ItemFactory
from .factories import EventFactory, CommentFactory


class BasicTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_root(self):
        response = self.c.get("/")
        self.assertEquals(response.status_code, 200)

    def test_smoketest(self):
        response = self.c.get("/smoketest/")
        self.assertEquals(response.status_code, 200)
        assert "PASS" in response.content

    def test_search(self):
        response = self.c.get("/search/?q=foo")
        self.assertEquals(response.status_code, 200)

    def test_search_empty(self):
        response = self.c.get("/search/?q=")
        self.assertEquals(response.status_code, 200)
        self.assertTrue("alert-error" in response.content)


class TestProjectViews(TestCase):
    def setUp(self):
        self.c = Client()

    def test_all_projects_page(self):
        p = ProjectFactory()
        r = self.c.get("/project/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(p.name in r.content)
        self.assertTrue(p.get_absolute_url() in r.content)

    def test_project_page(self):
        p = ProjectFactory()
        r = self.c.get(p.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(p.name in r.content)


class TestMilestoneViews(TestCase):
    def setUp(self):
        self.c = Client()

    def test_project_page(self):
        m = MilestoneFactory()
        r = self.c.get(m.project.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(m.name in r.content)
        self.assertTrue(m.get_absolute_url() in r.content)

    def test_milestone_page(self):
        m = MilestoneFactory()
        r = self.c.get(m.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(m.name in r.content)


class TestItemViews(TestCase):
    def setUp(self):
        self.c = Client()

    def test_item_view(self):
        i = ItemFactory()
        r = self.c.get(i.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(i.title in r.content)

    def test_milestone_view(self):
        i = ItemFactory()
        r = self.c.get(i.milestone.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(i.title in r.content)
        self.assertTrue(i.get_absolute_url() in r.content)


class TestItemWorkflow(TestCase):
    def setUp(self):
        self.c = Client()
        self.u = User.objects.create(username="testuser")
        self.u.set_password("test")
        self.u.save()
        self.c.login(username="testuser", password="test")
        self.pu = PMTUser.objects.create(username="testpmtuser",
                                         email="testemail@columbia.edu",
                                         status="active")
        Claim.objects.create(django_user=self.u, pmt_user=self.pu)

    def test_add_comment(self):
        i = ItemFactory()
        r = self.c.post(
            i.get_absolute_url() + "comment/",
            dict(comment='this is a comment'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)

    def test_add_comment_empty(self):
        i = ItemFactory()
        r = self.c.post(
            i.get_absolute_url() + "comment/",
            dict(comment=''))
        self.assertEqual(r.status_code, 302)

    def test_resolve(self):
        i = ItemFactory()
        r = self.c.post(
            i.get_absolute_url() + "resolve/",
            dict(comment='this is a comment',
                 r_status='FIXED'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)
        self.assertTrue("RESOLVED" in r.content)
        self.assertTrue("FIXED" in r.content)

    def test_resolve_self_assigned(self):
        i = ItemFactory(owner=self.pu, assigned_to=self.pu)
        r = self.c.post(
            i.get_absolute_url() + "resolve/",
            dict(comment='this is a comment',
                 r_status='FIXED'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)
        self.assertTrue("VERIFIED" in r.content)

    def test_inprogress(self):
        i = ItemFactory()
        r = self.c.post(
            i.get_absolute_url() + "inprogress/",
            dict(comment='this is a comment'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)
        self.assertTrue("INPROGRESS" in r.content)

    def test_verify(self):
        i = ItemFactory(status='RESOLVED', r_status='FIXED')
        r = self.c.post(
            i.get_absolute_url() + "verify/",
            dict(comment='this is a comment'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)
        self.assertTrue("VERIFIED" in r.content)

    def test_reopen(self):
        i = ItemFactory(status='RESOLVED', r_status='FIXED')
        r = self.c.post(
            i.get_absolute_url() + "reopen/",
            dict(comment='this is a comment'))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("this is a comment" in r.content)
        self.assertTrue("OPEN" in r.content)

    def test_split(self):
        i = ItemFactory()
        cnt = Item.objects.all().count()
        r = self.c.post(
            i.get_absolute_url() + "split/",
            dict(title_0="sub item one",
                 title_1="sub item two",
                 title_2="sub item three"))
        self.assertEqual(r.status_code, 302)
        r = self.c.get(i.get_absolute_url())
        self.assertTrue("VERIFIED" in r.content)
        self.assertTrue("Split" in r.content)
        self.assertTrue("sub item two" in r.content)
        # make sure there are three more items now
        self.assertEqual(Item.objects.all().count(), cnt + 3)

    def test_split_bad_params(self):
        i = ItemFactory()
        r = self.c.post(
            i.get_absolute_url() + "split/",
            dict(title_0="",
                 other_param="sub item two"))
        self.assertEqual(r.status_code, 302)


class TestHistory(TestCase):
    def setUp(self):
        self.c = Client()

    def test_item_view(self):
        i = ItemFactory()
        e1 = EventFactory(item=i)
        c1 = CommentFactory(item=i, event=e1)
        e2 = EventFactory(item=i)
        c2 = CommentFactory(item=i, event=e2)
        r = self.c.get(i.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(c2.comment in r.content)
        self.assertTrue(c1.comment in r.content)


class TestFeeds(TestCase):
    def setUp(self):
        self.c = Client()

    def test_forum_feed(self):
        r = self.c.get("/feeds/forum/rss/")
        self.assertEquals(r.status_code, 200)


class TestDRFViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.u = User.objects.create(username="testuser")
        self.u.set_password("test")
        self.u.save()
        self.c.login(username="testuser", password="test")

    def test_clients_list(self):
        r = self.c.get("/drf/clients/")
        self.assertEqual(r.status_code, 200)

    def test_projects_list(self):
        r = self.c.get("/drf/projects/")
        self.assertEqual(r.status_code, 200)

    def test_users_list(self):
        r = self.c.get("/drf/users/")
        self.assertEqual(r.status_code, 200)

    def test_milestones_list(self):
        r = self.c.get("/drf/milestones/")
        self.assertEqual(r.status_code, 200)

    def test_items_list(self):
        r = self.c.get("/drf/items/")
        self.assertEqual(r.status_code, 200)

    def test_project_milestones_list(self):
        p = ProjectFactory()
        r = self.c.get("/drf/projects/%d/milestones/" % p.pid)
        self.assertEqual(r.status_code, 200)

    def test_milestone_items_list(self):
        m = MilestoneFactory()
        r = self.c.get("/drf/milestones/%d/items/" % m.mid)
        self.assertEqual(r.status_code, 200)
