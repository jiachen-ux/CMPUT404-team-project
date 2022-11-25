from functools import partial
import json
from re import A
import re

from django.urls import reverse
from . import utils
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render, redirect
from rest_framework import generics, mixins, response, status
from .models import *
from .serializer import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from base64 import b64encode
from post.models import Post

from comment.forms import CommentForm
from comment.models import Comment



class CommentPostView(generics.ListCreateAPIView):

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    '''
        get the author object who will comment and pass it to serializer used later for creating comment object
        get the post object on which author will comment and pass it to serializer used later for creating comment object
        becoz comment has ForeignKey on both post and author therefore required feilds
    '''

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['author'] = Author.objects.filter(
                id=self.kwargs['uuidOfAuthor']).first()
            context['post'] = Post.objects.filter(
                id=self.kwargs.get('uuidOfPost')).first()

        return context

    '''
        stuff before the return self.create is only for incrementing the count in the post object by 1 becoz count is
        number of comments on a particular post object
    '''

    def post(self, request, *args, **kwargs):
        queryset = Post.objects.filter(id=kwargs['uuidOfPost']).first()
        data = {'count': queryset.count + 1}
        serializer = PostSerializer(queryset, data=data)
        if serializer.is_valid():
            serializer.save()

        return self.create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # edit
        queryset = self.get_queryset().filter(post__id=kwargs['uuidOfPost'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CommentPostView(generics.ListCreateAPIView):

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    '''
        get the author object who will comment and pass it to serializer used later for creating comment object
        get the post object on which author will comment and pass it to serializer used later for creating comment object
        becoz comment has ForeignKey on both post and author therefore required feilds
    '''

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            context['author'] = Author.objects.filter(
                id=self.kwargs['uuidOfAuthor']).first()
            context['post'] = Post.objects.filter(
                id=self.kwargs.get('uuidOfPost')).first()

        return context

    '''
        stuff before the return self.create is only for incrementing the count in the post object by 1 becoz count is
        number of comments on a particular post object
    '''

    def post(self, request, *args, **kwargs):
        queryset = Post.objects.filter(id=kwargs['uuidOfPost']).first()
        data = {'count': queryset.count + 1}
        serializer = PostSerializer(queryset, data=data)
        if serializer.is_valid():
            serializer.save()

        return self.create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # edit
        queryset = self.get_queryset().filter(post__id=kwargs['uuidOfPost'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

def add_Comment(request, postID):

    post = get_object_or_404(Post, id = postID)
    comments = Comment.objects.filter(post=post).order_by('-published')

    #CommentForm

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            return HttpResponseRedirect(reverse("posts"), args=[postID])

        else:
            form = CommentForm()
        
        context = {
            'form': form,
            "comments": comment,
            'post': post,
        }

    return render(request, 'commentDetails', context)

def commentDetails(request, postId):

    context = {}

    post = get_object_or_404(Post, id = postId)
    context['post'] = post

    context['comments'] = post.comments

    return render (request, 'comment_details.html', context)
   