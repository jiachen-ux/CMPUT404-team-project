from django.utils.timezone import now
from django.utils import dateparse
from django.db import models
from author.models import Author
from uuid import uuid4
from django.utils import timezone

import uuid

class Post(models.Model):
    creater = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    date_created = models.DateTimeField(default=timezone.now)
    content_text = models.TextField(max_length=140, blank=True)
    content_image = models.ImageField(upload_to='posts/', blank=True)
    likers = models.ManyToManyField(Author,blank=True , related_name='likes')
    comment_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Post user: {self.id} (creater: {self.creater})"

    def img_url(self):
        return self.content_image.url

    def append(self, name, value):
        self.name = value
