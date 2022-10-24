from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
import uuid
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db.models import (CASCADE, BooleanField, CharField, DateTimeField,
                              ForeignKey, IntegerField, JSONField,
                              ManyToManyField, Model, OneToOneField, URLField, ImageField)
#from django.utils.timezone import now
#we need node
url_max = 200
char_max = 200

class Node(Model): 
    api_domain = URLField(primary_key=True)
    api_prefix = CharField(max_length=200, blank=True, null=True)
    username = CharField(max_length=200)
    password = CharField(max_length=200)

"""
class NodeUserManager(BaseUserManager):
    def create_user(self, username, password):
        if not username:
            raise ValueError('Username is required.')
        if not password:
            raise ValueError('Password is required.')
        user = self.model(
            username=username
        )

        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self, username, password):
        user = self.create_user(username, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user
class NodeUser(AbstractBaseUser, PermissionsMixin):
    username = CharField(max_length=20, blank=False, null=False, unique=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_admin = BooleanField(default=False)

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = []

    objects = NodeUserManager()
    """

class Author(models.Model):
    userId = URLField(primary_key=True, max_length= url_max)
    username = models.CharField(unique=True, max_length=20, blank=False, null=False)
    type = models.CharField(default="author", max_length=200)
    
    url = models.CharField(max_length=char_max, blank=True)
    host = models.CharField(max_length=char_max, blank=True)
    displayName = models.CharField(max_length=char_max, blank =False)
    github = models.CharField(max_length=char_max, blank=True)
    profileImage = models.URLField(max_length=url_max, null=True, blank=True)
    #user = ForeignKey(NodeUser, on_delete=CASCADE, null=True)
    followers = ManyToManyField('self', symmetrical=False)

    @property
    def type(self):
        return 'author'
    
    def get_absolute_url(self):
        return self.userId

    def __str__(self):
        return self.displayName

    def to_dict(self):
        return {
            'type': self.type,
            'id': self.userId,
            'url': self.url,
            'host': self.host,
            'displayName': self.displayName,
            'github': self.github,
            'profileImage': self.profileImage,
        }




        }
class Post(models.Model):
    id = URLField(primary_key=True, blank=True)
    title = CharField(max_length=50, blank=True)
    source = URLField(blank=True)
    origin = URLField(blank=True)
    description = CharField(max_length=50, blank=True)
    content_type = CharField(blank=True, max_length=255, null=True)
    content = CharField(blank=True, max_length=5000, null=True)
    author = ForeignKey(Author, on_delete=CASCADE, null=True)
    #image = ImageField(upload_to=path, blank=True, null=True)
    image_id = URLField(blank=True)
    categories = CharField(max_length=255, blank=True, null=True)
    count = IntegerField(default=0)
    comments = URLField(blank=True)
    comments_src = URLField(blank=True, null=True)

class Comment(models.Model):
    author = ForeignKey(Author, on_delete=CASCADE)
    comment = CharField(max_length=500)
    id = URLField(primary_key=True, blank=True)
    post = ForeignKey(Post, on_delete=CASCADE, null=True)

    @property
    def type(self):
        return 'comment'

class Follow(models.Model):
    actor = ForeignKey(Author, on_delete=CASCADE, related_name='sender')
    object = ForeignKey(Author, on_delete=CASCADE, related_name='recipient')
    class Meta:
        pass
    @property
    def type(self):
        return 'follow'

class Like(models.Model):
    object = URLField(blank=True)
    author = ForeignKey(Author, on_delete=CASCADE, null=True)

    @property
    def type(self):
        return 'like'

class Inbox(models.Model):
    author  = OneToOneField(Author, on_delete=CASCADE, related_name='author_inbox')
    posts = ManyToManyField(Post, related_name='inbox_posts')
    comments = ManyToManyField(Comment)
    likes = ManyToManyField(Like)
    follows = ManyToManyField(Follow)

    @property
    def type(self):
        return 'inbox'


