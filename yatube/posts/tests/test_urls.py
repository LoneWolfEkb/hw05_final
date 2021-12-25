from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User

AUTHORIZED = 'another'
AUTHOR = 'auth'
POSTER = 'poster'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
POST_TEXT = 'Тестовый текст'
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR})
UNEXISTING_URL = '/unexisting_page/'
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow',
                     kwargs={'username': POSTER})
UNFOLLOW_URL = reverse('posts:profile_unfollow',
                       kwargs={'username': POSTER})


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
        self.POST_EDIT_URL = reverse('posts:post_edit',
                                     kwargs={'post_id': self.post.id})
        self.POST_DETAIL_URL = reverse('posts:post_detail',
                                       kwargs={'post_id': self.post.id})
        self.ADD_COMMENT_URL = reverse('posts:add_comment',
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
            [self.ADD_COMMENT_URL, self.guest, 302],
            [FOLLOW_INDEX_URL, self.guest, 302],
            [FOLLOW_URL, self.another, 302],
            [POST_CREATE_URL, self.another, 200],
            [self.POST_EDIT_URL, self.another, 302],
            [self.ADD_COMMENT_URL, self.another, 200],
            [FOLLOW_INDEX_URL, self.another, 200],
            [FOLLOW_URL, self.another, 200],
            [UNFOLLOW_URL, self.another, 200],
            [self.POST_EDIT_URL, self.author, 200],
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
            self.POST_EDIT_URL: 'posts/create_post.html',
            self.ADD_COMMENT_URL: 'posts/post_detail.html',
            FOLLOW_URL: 'posts/profile.html',
            UNFOLLOW_URL: 'posts/profile.html',
            FOLLOW_INDEX_URL: 'posts/follow_index.html'
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
            [self.ADD_COMMENT_URL, f'{LOGIN_URL}?next={self.ADD_COMMENT_URL}',
             self.guest],
            [FOLLOW_INDEX_URL, f'{LOGIN_URL}?next={FOLLOW_INDEX_URL}',
             self.guest],
            [FOLLOW_URL, f'{LOGIN_URL}?next={self.FOLLOW_URL}',
             self.guest],
            [self.POST_EDIT_URL, self.POST_DETAIL_URL, self.another],
        ]
        for url, redirect, user in urls_to_redirect:
            with self.subTest(url=url, user=user):
                self.assertRedirects(user.get(url, follow=True), redirect)
