from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User, Follow

FOLLOWER = 'follower'
POSTER = 'poster'
NEW_FOLLOWER = 'new_follower'
NOT_FOLLOWER = 'not_follower'
POST_TEXT = 'Тестовый текст'
POST_CREATE_URL = reverse('posts:post_create')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow',
                                     kwargs={'username': POSTER})
UNFOLLOW_URL = reverse('posts:profile_unfollow',
                                     kwargs={'username': POSTER})

class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username=FOLLOWER)
        cls.notfollower = User.objects.create_user(username=NOT_FOLLOWER)
        cls.poster = User.objects.create_user(username=POSTER)
        cls.new_follower = User.objects.create_user(username=NEW_FOLLOWER)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.poster
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.poster
        )

    def setUp(self):
        self.notfollower_client = Client()
        self.notfollower_client.force_login(self.notfollower)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.new_follower_client = Client()
        self.new_follower_client.force_login(self.new_follower)

    def test_new_post_appears_in_follow_list(self):
        response = self.follower_client.get(FOLLOW_INDEX_URL)
        self.assertEqual((len(response.context['page_obj'])), 1)
        post = response.context['page_obj'][0]
        self.assertEqual(self.post, post)
        response = self.notfollower_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(self.post, post)
        
    def test_subscribe_unsubscribe(self):
        follows_before = Follow.objects.count()
        self.new_follower_client.get(FOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follows_before + 1)
        self.assertTrue( 
            Follow.objects.filter( 
                user = self.new_follower, 
                author=self.poster 
            ).exists() 
        )
        self.new_follower_client.get(UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follows_before)
        self.assertFalse( 
            Follow.objects.filter( 
                user = self.new_follower, 
                author=self.poster 
            ).exists() 
        )
        

        
        
        