import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, User, Group, Comment

AUTHOR = 'auth'
ANOTHER = 'another'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
NEW_GROUP_TITLE = 'Новая группа'
NEW_GROUP_SLUG = 'new-slug'
POST_TEXT = 'Тестовый текст'
NEW_TEXT = 'Новый текст'
NEW_COMMENT = 'Новый комментарий'
PROFILE_URL = reverse('posts:profile', kwargs={'username': AUTHOR})
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.uploaded_two = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.another = User.objects.create_user(username=ANOTHER)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
        )
        cls.new_group = Group.objects.create(
            title=NEW_GROUP_TITLE,
            slug=NEW_GROUP_SLUG,
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.guest_client = Client()
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.another_client = Client()
        cls.another_client.force_login(cls.another)
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.id})
        cls.ADD_COMMENT_URL = reverse('posts:add_comment',
                                      kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_form_create(self):
        """Проверка создания нового поста"""
        # Если просто поставить self.uploaded в form_data, то пост не создастся
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posts = set(Post.objects.all())
        post_count = Post.objects.count()
        form_data = {
            'text': NEW_TEXT,
            'group': self.group.id,
            'image': uploaded
        }
        self.author_client.post(POST_CREATE_URL,
                                data=form_data,
                                follow=True)
        # Редиректы мы уже проверяем в url, а здесь они только создают проблемы
        self.assertEqual(Post.objects.count(), post_count + 1)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = (posts).pop()
        self.assertEqual(self.author, post.author)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(form_data['image'], uploaded)

    def test_add_comment_auth_user(self):
        """Проверка создания нового коммента авторизованным"""
        comments = set(Comment.objects.all())
        comment_count = Comment.objects.count()
        self.author_client.post(self.ADD_COMMENT_URL,
                                {'text': NEW_COMMENT},
                                follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        comments = set(Comment.objects.all()) - comments
        self.assertEqual(len(comments), 1)
        comment = (comments).pop()
        self.assertEqual(comment.text, NEW_COMMENT)

    def test_add_comment_guest_user(self):
        """Проверка создания нового коммента гостем"""
        comment_count = Comment.objects.count()
        self.guest_client.post(self.ADD_COMMENT_URL, {'text': NEW_TEXT})
        self.assertEqual(Comment.objects.count(), comment_count)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_post_edit(self):
        """Проверка редактирования поста автором"""
        form_data = {
            'text': NEW_TEXT,
            'group': self.new_group.id,
            'image': self.uploaded_two
        }
        past_author = self.post.author
        self.author_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(form_data['text'], NEW_TEXT,)
        self.assertEqual(form_data['image'], self.uploaded_two)
        self.assertEqual(form_data['group'], self.new_group.id)
        self.assertEqual(self.post.author, past_author)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def test_post_deny_edit(self):
        """Проверка редактирования поста гостем или неавтором"""
        form_data = {
            'text': NEW_TEXT,
            'group': self.new_group.id,
            'image': self.uploaded
        }
        users_redirects = {
            self.guest_client: f'{LOGIN_URL}?next={self.POST_EDIT_URL}',
            self.another_client: self.POST_DETAIL_URL
        }
        for user, url in users_redirects.items():
            past_author = self.post.author
            user.post(
                self.POST_EDIT_URL,
                data=form_data,
                follow=True
            )
        self.post.refresh_from_db()
        self.assertEqual(POST_TEXT, self.post.text)
        self.assertEqual(self.group.id, self.post.group.id)
        self.assertEqual(self.post.author, past_author)
        self.assertEqual(form_data['image'], self.uploaded)

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
