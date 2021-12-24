from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, User, Group, Comment

AUTHOR = 'auth'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
NEW_GROUP_TITLE = 'Новая группа'
NEW_GROUP_SLUG = 'new-slug'
UNIQUE_GROUP_TITLE = 'Очищаемая группа'
UNIQUE_GROUP_SLUG = 'clean-slug'
POST_TEXT = 'Тестовый текст'
NEW_TEXT = 'Новый текст'
POST_EDIT_VIEW = 'posts:post_edit'
POST_DETAIL_VIEW = 'posts:post_detail'
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR})
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')


class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
        )
        cls.new_group = Group.objects.create(
            title=NEW_GROUP_TITLE,
            slug=NEW_GROUP_SLUG,
        )
        cls.unique_group = Group.objects.create(
            title=UNIQUE_GROUP_TITLE,
            slug=UNIQUE_GROUP_SLUG,
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.POST_EDIT_URL = reverse(POST_EDIT_VIEW,
                                     kwargs={'post_id': self.post.id})
        self.POST_DETAIL_URL = reverse(POST_DETAIL_VIEW,
                                       kwargs={'post_id': self.post.id})
        self.ADD_COMMENT_URL = reverse('posts:add_comment',
                                       kwargs={'post_id': self.post.id})

    def test_form_create(self):
        """Проверка создания нового поста"""
        posts = set(Post.objects.all())
        post_count = Post.objects.count()
        form_data = {
            'text': NEW_TEXT,
            'group': self.unique_group.id,
            'image': self.uploaded
        }
        response = self.author_client.post(POST_CREATE_URL,
                                           data=form_data,
                                           follow=True)
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), post_count + 1)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = (posts).pop()
        self.assertEqual(self.author, post.author)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(form_data['image'], self.uploaded)

    def test_add_comment_only_auth_user_appears_at_desired_location(self):
        """Проверка создания нового коммента"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': NEW_TEXT,
        }
        response_logined = self.author_client.post(self.ADD_COMMENT_URL,
                                                   data=form_data,
                                                   follow=True)
        self.assertRedirects(response_logined,
                             self.POST_DETAIL_URL)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response_logined.context['post_comments'][0].text,
                         NEW_TEXT)
        response_unlogined = self.author_client.post(self.ADD_COMMENT_URL,
                                                     data=form_data)
        self.assertRedirects(response_unlogined,
                             f'{LOGIN_URL}?next={self.POST_DETAIL_URL}')
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_post_edit(self):
        """Проверка редактирования поста"""
        form_data = {
            'text': NEW_TEXT,
            'group': self.new_group.id,
        }
        past_author = self.post.author
        response = self.author_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.post.refresh_from_db()
        self.assertEqual(form_data['text'], self.post.text)
        self.assertEqual(form_data['group'], self.post.group.id)
        self.assertEqual(self.post.author, past_author)

    def test_post_create_edit_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        urls = (
            self.POST_EDIT_URL,
            POST_CREATE_URL
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                for value, expected in form_fields.items():
                    with self.subTest(url=url):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)
