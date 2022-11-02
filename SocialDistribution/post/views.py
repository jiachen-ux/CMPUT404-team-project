from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from uuid import uuid4
from .serializers import PostSerializer
from author.models import Author
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from .models import *
from follower.models import Follower
from comment.models import Comment


# Create your views here.
class PostApiView(APIView):
    def get(self, request: Request, author_id: str = None, post_id: str = None):
        if author_id == None:
            posts = list(Post.objects.filter(visibility='PUBLIC', unlisted=False).order_by('-published'))
            serializer =  PostSerializer(posts, many=True)
            res = {"items": serializer.data}
            return Response(res)
        try:
            author = Author.objects.get(userId = author_id)
        except Exception as e:
            return Response(f"Error: {e}", status=status.HTTP_404_NOT_FOUND)
        if author == None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if post_id == None:
            posts = list(Post.objects.filter(author = author).order_by("-published"))
            serializer = PostSerializer(posts, many=True)
            result = {"items": serializer.data}
            return Response(result, status=status.HTTP_200_OK)
        else:
            try:
                postObj = Post.objects.get(id = post_id, author = author, visibility='PUBLIC')
                serializer = PostSerializer(postObj)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(f"Error: {e}", status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request: Request, author_id: str, post_id: str = None):
        try:
            author = Author.objects.get(userId = author_id)
        except Exception as e:
            return Response(f"Error: {e}", status=status.HTTP_404_NOT_FOUND)
        if author == None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Update a post
        if post_id is not None:
            try: 
                author = Author.objects.get(userId=author_id)
                post = Post.objects.get(id = post_id, author=author)
                serializer = PostSerializer(post, data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(serializer.validated_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(f"Error: {e}", status=status.HTTP_404_NOT_FOUND)
        else:
            serialize = PostSerializer(data=request.data)
            if serialize.is_valid(raise_exception=True):
                try:
                    author = Author.objects.get(userId=author_id)
                    ID = str(uuid4())
                    
                    serialize.save(
                        id=ID,
                        author=author,
                        )
                    return Response(serialize.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response(f"Error: {e}", status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request: Request, author_id: str, post_id: str):
        try:
            author = Author.objects.get(userId = author_id)
        except Exception as e:
            return Response(f"Error: {e}", status=status.HTTP_404_NOT_FOUND)
        if author == None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            post = Post.objects.get(id=post_id, author=author)
            post.delete()
            return Response("Post was deleted Successfully", status.HTTP_200_OK)
        except Exception as e:
                return Response(f"Error: {e}", status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
@login_required
def create_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        try:
            post = Post.objects.create(creater=request.user, content_text=text, content_image=pic)
            return HttpResponseRedirect(reverse('index'))
        except Exception as e:
            return HttpResponse(e)
    else:
        return HttpResponse("Method must be 'POST'")

@login_required
@csrf_exempt
def edit_post(request, post_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        pic = request.FILES.get('picture')
        img_chg = request.POST.get('img_change')
        post_id = request.POST.get('id')
        post = Post.objects.get(id=post_id)
        try:
            post.content_text = text
            if img_chg != 'false':
                post.content_image = pic
            post.save()
            
            if(post.content_text):
                post_text = post.content_text
            else:
                post_text = False
            if(post.content_image):
                post_image = post.img_url()
            else:
                post_image = False
            
            return JsonResponse({
                "success": True,
                "text": post_text,
                "picture": post_image
            })
        except Exception as e:
            print('-----------------------------------------------')
            print(e)
            print('-----------------------------------------------')
            return JsonResponse({
                "success": False
            })
    else:
            return HttpResponse("Method must be 'POST'")

@csrf_exempt
def like_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unlike_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.likers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def save_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.add(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unsave_post(request, id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(pk=id)
            print(post)
            try:
                post.savers.remove(request.user)
                post.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def follow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = Author.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Follower: {request.user}......................")
            try:
                (follower, create) = Follower.objects.get_or_create(user=user)
                follower.followers.add(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def unfollow(request, username):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            user = Author.objects.get(username=username)
            print(f".....................User: {user}......................")
            print(f".....................Unfollower: {request.user}......................")
            try:
                follower = Follower.objects.get(user=user)
                follower.followers.remove(request.user)
                follower.save()
                return HttpResponse(status=204)
            except Exception as e:
                return HttpResponse(e)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def comment(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            data = json.loads(request.body)
            comment = data.get('comment_text')
            post = Post.objects.get(id=post_id)
            try:
                newcomment = Comment.objects.create(post=post,commenter=request.user,comment_content=comment)
                post.comment_count += 1
                post.save()
                print(newcomment.to_dict())
                return JsonResponse([newcomment.to_dict()], safe=False, status=201)
            except Exception as e:
                return HttpResponse(e)
    
        post = Post.objects.get(id=post_id)
        comments = Comment.objects.filter(post=post)
        comments = comments.order_by('-comment_time').all()
        return JsonResponse([comment.to_dict() for comment in comments], safe=False)
    else:
        return HttpResponseRedirect(reverse('login'))

@csrf_exempt
def delete_post(request, post_id):
    if request.user.is_authenticated:
        if request.method == 'PUT':
            post = Post.objects.get(id=post_id)
            if request.user == post.creater:
                try:
                    delet = post.delete()
                    return HttpResponse(status=201)
                except Exception as e:
                    return HttpResponse(e)
            else:
                return HttpResponse(status=404)
        else:
            return HttpResponse("Method must be 'PUT'")
    else:
        return HttpResponseRedirect(reverse('login'))
