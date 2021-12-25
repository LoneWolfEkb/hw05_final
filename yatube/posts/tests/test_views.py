from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User, Group

AUTHOR = 'auth'
POSTER = 'poster' # лучше было бы 'followee', но слово не совсем существует
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
OTHER_GROUP = 'Вторая группа'
OTHER_GROUP_SLUG = 'second-slug'
POST_TEXT = 'Тестовый текст'
OTHER_TEXT = 'Другой текст, для более точной проверки'
INDEX_URL = reverse('posts:index')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
OTHER_GROUP_LIST_URL = reverse('posts:group_list',
                               kwargs={'slug': OTHER_GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR})
FOLLOW_INDEX_URL = reverse('posts:follow_index')

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.author_client = Client()
        cls.author_client.force_login(self.author)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG
        )
        cls.other_group = Group.objects.create(
            title=OTHER_GROUP,
            slug=OTHER_GROUP_SLUG
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.other_post = Post.objects.create(
            text=OTHER_TEXT,
            author=cls.poster,
            group=cls.other_group,
            image=cls.uploaded
        )
        cls.poster = User.objects.create_user(username=POSTER)
        cls.poster_client = Client()
        cls.poster_client.force_login(self.follower)
        cls.follow = Follow.objects.create(
            user=cls.author,
            author=cls.poster
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                       kwargs={'post_id': self.post.id})

    def test_post_pages_use_correct_context(self):
        """Контекст на страницах с группами и постами"""
        urls_posts = [
            [INDEX_URL, self.post],
            [GROUP_LIST_URL, self.post],
            [PROFILE_URL, self.post],
            [self.POST_DETAIL_URL, self.post],
            [FOLLOW_INDEX_URL, self.other_post]
        ]
        for url, post_type in urls_posts:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                if url == self.POST_DETAIL_URL:
                    post = response.context.get('post')
                else:
                    self.assertEqual((len(response.context['page_obj'])), 1)
                    post = response.context['page_obj'][0]
                self.assertEqual(post.text, post_type.text)
                self.assertEqual(post.author, post_type.author)
                self.assertEqual(post.group, post_type.group)
                self.assertEqual(post.id, post_type.id)
                self.assertEqual(post.image, post_type.image)

    def test_author_on_profile_page(self):
        response = self.author_client.get(PROFILE_URL)
        self.assertEqual(response.context.get('author'), self.author)

    def test_group_in_group_list(self):
        response = self.author_client.get(GROUP_LIST_URL)
        group = response.context.get('group')
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.id, self.group.id)

    def test_post_not_in_other_group_list_or_subscription(self):
        posts_urls = [
            [self.other.post, GROUP_LIST_URL],
            [self.post, FOLLOW_INDEX_URL]
        ]
        # так как poster не подписан обратно на author, тут логинется он
        for post_type, url in posts_urls:
            with self.subTest(url=url):
                response = self.poster.client.get(url)
                self.assertNotIn(self.other_post, response.context['page_obj'])
