from django.test import Client, TestCase
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from posts.models import Post, User

AUTHOR = 'auth'
POST_TEXT = 'Тестовый текст'
INDEX_URL = reverse('posts:index')

class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_index_cache(self):
        response = self.author_client.get(INDEX_URL) 
        content_one = response.content
        self.post.delete()
        response_two = self.author_client.get(INDEX_URL)
        content_two = response_two.content
        self.assertEqual(content_one, content_two)
