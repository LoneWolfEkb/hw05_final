from django.test import TestCase
from django.urls import reverse

USERNAME = 'username'
GROUP_SLUG = 'slug'
POST_ID = 1


class RoutesModelTest(TestCase):

    def test_routes(self):
        """Проверяем маршруты"""
        routes = [
            ['/', 'index', None],
            [f'/group/{GROUP_SLUG}/', 'group_list', [GROUP_SLUG]],
            [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
            [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
            ['/create/', 'post_create', None],
            [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]]
        ]
        for url, name, arg in routes:
            self.assertEqual(url, reverse(f'posts:{name}', args=arg))