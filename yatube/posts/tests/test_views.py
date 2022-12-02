import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()
POSTS_FIRST_PAGE = 10
POSTS_SECOND_PAGE = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.user_second = User.objects.create_user(username='second_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test description'
        )
        cls.group_second = Group.objects.create(
            title='second_group',
            slug='second_slug',
            description='second description'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth_user'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Шаблон posts/index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(self.post.image, self.post.image)

    def test_posts_group_page_show_correct_context(self):
        """Шаблон posts/group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(self.post.image, self.post.image)

    def test_posts_profile_page_show_correct_context(self):
        """Шаблон posts/profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth_user'})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(self.post.image, self.post.image)

    def test_posts_detail_page_show_correct_context(self):
        """Шаблон posts/post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context.get('post')
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(self.post.image, self.post.image)

    def test_posts_create_post_page_show_correct_context(self):
        """Шаблон posts/create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_group_page_not_include_incorect_post(self):
        """Шаблон posts/group_list содержит ожидаемые посты."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'second_slug'})
        )
        for secong_group_post in response.context['page_obj']:
            self.assertNotEqual(secong_group_post.pk, self.post[0].id)

    def test_cache_index_page(self):
        """Тест для проверки кеширования главной страницы."""
        post = Post.objects.create(
            text='Пост для кеширования',
            author=self.user
        )
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_del = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_del)
        cache.clear()
        content_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)

    def test_authorized_user_add_comment(self):
        """Добавление комментария авторизованным пользователем."""
        self.authorized_client.post(
            f'/posts/{self.post.id}/comment/',
            {'text': 'Тестовый комментарий'}
        )
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertContains(response, 'Тестовый комментарий')

    def test_quest_add_comment(self):
        """Добавление комментария неавторизованным пользователем."""
        self.guest_client.post(
            f'/posts/{self.post.id}/comment/',
            {'text': 'Тестовый комментарий'}
        )
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertNotContains(response, 'Тестовый комментарий')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test description'
        )
        cls.posts = []
        for num_post in range(13):
            cls.posts.append(Post(
                text=f'Текст тестового поста №{num_post}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_first_index_page_contains_ten_posts(self):
        """Шаблон posts/index первая страница содержит 10 результатов."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_FIRST_PAGE)

    def test_second_index_page_contains_three_posts(self):
        """Шаблон posts/index вторая страница содержит 3 результата."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_SECOND_PAGE)

    def test_first_group_list_contains_ten_posts(self):
        """Шаблон posts/group_list первая страница содержит 10 результатов."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_FIRST_PAGE)

    def test_second_group_list_contains_ten_posts(self):
        """Шаблон posts/group_list вторая страница содержит 3 результата."""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_SECOND_PAGE)

    def test_first_profile_page_contains_ten_posts(self):
        """Шаблон posts/profile первая страница содержит 10 результатов."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth_user'})
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_FIRST_PAGE)

    def test_second_profile_page_contains_ten_posts(self):
        """Шаблон posts/profile первая страница содержит 3 результатов."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'auth_user'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), POSTS_SECOND_PAGE)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.follower = User.objects.create(username='follower')
        cls.post = Post.objects.create(
            text='Тестовый текст чтоб подписались',
            author=cls.author
        )

    def setUp(self):
        self.author_client = Client()
        self.follower_client = Client()
        self.author_client.force_login(self.author)
        self.follower_client.force_login(self.follower)
        cache.clear()

    def test_follow_on_author(self):
        """Проверка подписки на автора постов."""
        follower_count = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            )
        )
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), follower_count + 1)
        self.assertEqual(follow.author_id, self.author.id)
        self.assertEqual(follow.user_id, self.follower.id)

    def test_unfollow_on_author(self):
        """Проверка отписки от автора постов."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        follower_count = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            )
        )
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_follow_feed(self):
        """Проверка ленты подписанных."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_unfollow_feed(self):
        """Проверка ленты неподписанных."""
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(self.post, response.context['page_obj'].object_list)
