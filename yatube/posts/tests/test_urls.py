from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User

AUTHORIZED = 'another'
AUTHOR = 'auth'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
POST_TEXT = 'Тестовый текст'
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR})
UNEXISTING_URL = '/unexisting_page/'
POST_CREATE_URL = reverse('posts:post_create')
POST_EDIT_VIEW = 'posts:post_edit'
POST_DETAIL_VIEW = 'posts:post_detail'
LOGIN_URL = reverse('users:login')


class PostGroupProfileURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.another_user = User.objects.create_user(username=AUTHORIZED)
        cls.author_user = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author_user,
        )

    def setUp(self):
        self.guest = Client()
        self.another = Client()
        self.another.force_login(self.another_user)
        self.author = Client()
        self.author.force_login(self.author_user)
        self.POST_EDIT_URL = reverse(POST_EDIT_VIEW,
                                     kwargs={'post_id': self.post.id})
        self.POST_DETAIL_URL = reverse(POST_DETAIL_VIEW,
                                       kwargs={'post_id': self.post.id})

    def test_url_responses(self):
        """Тестируем доступность страниц"""
        data_list = [
            [INDEX_URL, self.guest, 200],
            [UNEXISTING_URL, self.guest, 404],
            [GROUP_LIST_URL, self.guest, 200],
            [PROFILE_URL, self.guest, 200],
            [self.POST_DETAIL_URL, self.guest, 200],
            [POST_CREATE_URL, self.guest, 302],
            [self.POST_EDIT_URL, self.guest, 302],
            [POST_CREATE_URL, self.another, 200],
            [self.POST_EDIT_URL, self.another, 302],
            [self.POST_EDIT_URL, self.author, 200]
        ]
        for url, client, status in data_list:
            with self.subTest(url=url, client=client, status=status):
                self.assertEqual(client.get(url).status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            POST_CREATE_URL: 'posts/create_post.html',
            self.POST_EDIT_URL: 'posts/create_post.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(self.author.get(adress),
                                        template)

    def test_urls_redirect_correctly(self):
        """URL-адреса перенаправляются на нужные."""
        urls_to_redirect = [
            [POST_CREATE_URL, f'{LOGIN_URL}?next={POST_CREATE_URL}',
             self.guest],
            [self.POST_EDIT_URL, f'{LOGIN_URL}?next={self.POST_EDIT_URL}',
             self.guest],
            [self.POST_EDIT_URL, self.POST_DETAIL_URL, self.another],
        ]
        for url, redirect, user in urls_to_redirect:
            with self.subTest(url=url, user=user):
                self.assertRedirects(user.get(url, follow=True), redirect)
