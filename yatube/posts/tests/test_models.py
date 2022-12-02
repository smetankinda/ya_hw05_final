from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост!!!!!!!!!!!!!!!!!!!!',
            author=cls.user,
            group=cls.group
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = self.post.text[:15]
        self.assertEqual(expected_object_name, str(self.post))
        new_post = Post.objects.last()
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_post_verbose_name(self):
        """Проверка verbose_name у post."""
        field_verboses = {
            'text': 'Содержание поста',
            'pub_date': 'Дата',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        """Проверка help_text у post."""
        feild_help_texts = {
            'text': 'Текст поста',
            'group': 'Группа поста',
        }
        for value, expected in feild_help_texts.items():
            with self.subTest(value=value):
                help_text = self.post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей группы корректно работает __str__."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = self.comment.text[:15]
        self.assertEqual(expected_object_name, str(self.comment))

    def test_сomment_verbose_name(self):
        """Проверка verbose_name у сomment."""
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Комментарий',
            'created': 'Создан комментарий',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_help_text(self):
        """Проверка help_text у comment."""
        feild_help_texts = {
            'text': 'Текст комментария',
            'created': 'Создание комментария',
        }
        for value, expected in feild_help_texts.items():
            with self.subTest(value=value):
                help_text = self.comment._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_first = User.objects.create_user(username='auth_first')
        cls.user_second = User.objects.create_user(username='auth_second')
        cls.follow = Follow.objects.create(
            user=cls.user_first,
            author=cls.user_second
        )

    def test_models_have_correct_object_names(self):
        self.assertEqual(
            f'{self.user_first} оформил подписку на {self.user_second}',
            str(self.follow))

    def test_follow_verbose_name(self):
        """Проверка verbose_name у follow."""
        field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_follow_help_text(self):
        """Проверка help_text у follow."""
        feild_help_texts = {
            'user': 'Подписчик',
            'author': 'Блоггер',
        }
        for value, expected in feild_help_texts.items():
            with self.subTest(value=value):
                help_text = self.follow._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)
