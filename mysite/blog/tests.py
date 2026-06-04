from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Post


class BlogViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.author = User.objects.create_user(
            username="testauthor",
            email="author@test.com",
            password="testpass123",
        )
        cls.post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            author=cls.author,
            body="Hello **world**",
            status=Post.Status.PUBLISHED,
        )

    def setUp(self):
        self.client = Client()

    def test_root_redirects_to_blog(self):
        r = self.client.get("/", follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("blog:post_list"))

    def test_post_list(self):
        r = self.client.get(reverse("blog:post_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Post")

    def test_post_detail_and_markdown(self):
        url = reverse("blog:post_detail", args=[self.post.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<strong>world</strong>", html=False)

    def test_post_share_get(self):
        url = reverse("blog:post_share", args=[self.post.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_comment_post_redirects(self):
        url = reverse("blog:post_detail", args=[self.post.id])
        r = self.client.post(
            url,
            {
                "name": "Reader",
                "email": "reader@example.com",
                "body": "Nice article.",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, self.post.get_absolute_url())
        detail = self.client.get(self.post.get_absolute_url())
        self.assertContains(detail, "Nice article.")


class BlogCollaborationTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="writer",
            email="writer@test.com",
            password="securepassword123",
        )

    def test_registration_view(self):
        r = self.client.get(reverse("blog:register"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Create Account")

        # Test post registration
        r = self.client.post(
            reverse("blog:register"),
            {
                "username": "newuser",
                "email": "newuser@test.com",
                "password1": "testpass999!",
                "password2": "testpass999!",
            },
        )
        self.assertEqual(r.status_code, 302)
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_logout_flow(self):
        r = self.client.get(reverse("blog:login"))
        self.assertEqual(r.status_code, 200)

        # Log in
        self.client.login(username="writer", password="securepassword123")

        # Access dashboard
        r = self.client.get(reverse("blog:dashboard_view"))
        self.assertEqual(r.status_code, 200)

    def test_profile_view_and_edit(self):
        # View profile of writer
        r = self.client.get(reverse("blog:profile_view", args=["writer"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "@writer")

        # Edit profile requires login
        r = self.client.get(reverse("blog:profile_edit"))
        self.assertEqual(r.status_code, 302)  # Redirect to login

        # Login and edit
        self.client.login(username="writer", password="securepassword123")
        r = self.client.get(reverse("blog:profile_edit"))
        self.assertEqual(r.status_code, 200)

        # POST update profile bio
        r = self.client.post(
            reverse("blog:profile_edit"),
            {
                "first_name": "Writer",
                "last_name": "One",
                "email": "writer@test.com",
                "bio": "I am a blogger.",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "I am a blogger.")

    def test_post_crud(self):
        self.client.login(username="writer", password="securepassword123")

        # Get creation page
        r = self.client.get(reverse("blog:post_create"))
        self.assertEqual(r.status_code, 200)

        # Create post (slug blank to test auto-generation!)
        r = self.client.post(
            reverse("blog:post_create"),
            {
                "title": "My Awesome Story",
                "body": "This is content.",
                "status": "PB",
                "tags": "test, cool",
            },
        )
        self.assertEqual(r.status_code, 302)

        # Verify post is created and slug auto-generated
        post = Post.objects.get(title="My Awesome Story")
        self.assertEqual(post.slug, "my-awesome-story")
        self.assertEqual(post.author, self.user)
