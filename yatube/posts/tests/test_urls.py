from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.not_author = User.objects.create_user(username='not_auth_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author.force_login(self.not_author)
        cache.clear()

    def test_all_users_urls_access(self):
        """Страницы доступные всем пользователям."""
        url_names = (
            '/',
            '/group/test_slug/',
            '/profile/auth_user/',
            f'/posts/{self.post.id}/'
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_user_urls_access(self):
        """Страницы доступные авторизованному пользователю."""
        url_names = (
            '/',
            '/group/test_slug/',
            '/profile/auth_user/',
            f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/edit/',
            '/create/'
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_url_redirect_guest(self):
        """Редирект гостя на страницу входа."""
        url_names_redirects = {
            f'/posts/{self.post.id}/edit/': (
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            ),
            '/create/': '/auth/login/?next=/create/',
        }
        for address, redirect_address in url_names_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_list_url_redirect_not_author(self):
        """Редирект не автора поста на страницу поста."""
        response = self.authorized_client_not_author.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_urls_users_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth_user/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }

        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_not_found(self):
        """Страница не найдена."""
        response_url = {
            self.guest_client: '/unexisting_page/',
            self.authorized_client: '/unexisting_page/',
        }
        for client, url in response_url.items():
            with self.subTest(client=client):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
