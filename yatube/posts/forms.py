from django.forms import ModelForm
from posts.models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Сообщение поста', 'group': 'Группа'}
        help_texts = {'text': 'Введите текст', 'group': 'Выберите группу'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
