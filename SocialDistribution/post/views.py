from functools import partial
import json
from re import A
import re

import requests
from . import utils
from django.shortcuts import render, redirect
from django.http.request import HttpRequest
from rest_framework import generics, mixins, response, status
from django.shortcuts import get_object_or_404
from django.http.response import Http404
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from base64 import b64encode

from follower.models import Follower
from comment.models import Comment
from like.models import Like
from comment.serializer import CommentSerializer

from comment.models import *
from rest_framework.generics import  ListCreateAPIView
from author.views import id_cleaner


class PostLike(ListCreateAPIView):
    queryset=Like.objects.all()
    serializer_class=LikeSerializer
    permission_classes = [AllowAny]
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["author"] = Author.objects.filter(id=self.kwargs['uuidOfAuthor'])[0]
        context["object_id"] = self.kwargs['uuidOfPost']
        return context
    def post(self, request,  *args, **kwargs):
        return self.create(request)
        
    def get(self, request, *args, **kwargs):
        try:
            queryset = Like.objects.filter(author__id=self.kwargs['uuidOfAuthor'], object_id=self.kwargs['uuidOfPost'])[0]
            serializers =  LikeSerializer(queryset)
            return Response(serializers.data, 200)
        except:
            return Response(404)

@api_view(["GET"])
def getAllCommentLikes(request, uuidOfAuthor, uuidOfPost, uuidOfComment):
    # Get all likes of that comment
    allLikes = Like.objects.filter(object_id=uuidOfComment)
    serializer = LikeSerializer(allLikes, many=True)
    return response.Response(serializer.data)


@api_view(["GET"])
def getAllAuthorLiked(request, uuidOfAuthor):
    # Get everything that author liked
    allLikes = Like.objects.filter(author__id=uuidOfAuthor)
    serializer = LikeSerializer(allLikes, many=True)
    return response.Response(serializer.data)

class PostSingleDetailView(generics.RetrieveUpdateDestroyAPIView, generics.CreateAPIView):

    queryset = Post.objects.all()
    serializer_class = PostSerializer

    # adding extra data to context object becoz we need author(finding the correct author by uuid) to create the post
    # and we take in the user inputed uuid
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'PUT':
            # can also do get_object_or_404..
            context['author'] = Author.objects.filter(
                id=self.kwargs['uuidOfAuthor']).first()
            context['id'] = self.kwargs['uuidOfPost']
        return context

    '''
        Check if the current user is allowed to access that individual post
        check 1 if it is the post made by same author then return it or the post is public post
        check 2 if the author who made the request is the follower of the author who made the post
    '''

    def get(self, request, *args, **kwargs):
        queryset = Post.objects.filter(id=kwargs['uuidOfPost']).first()

        if (kwargs['uuidOfAuthor'] == queryset.author.id) or queryset.visibility == 'PUBLIC':
            serializer = self.serializer_class(queryset, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif (queryset.visibility == 'FRIENDS') and bool(Follower.objects.filter(follower__id=kwargs['uuidOfAuthor'], following__id=queryset.author.id)):
            serializer = self.serializer_class(queryset, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"Error: Follower and Following relatioship does not exists"}, status=status.HTTP_400_BAD_REQUEST)

    '''
        Method says it is post but does the work of editing the post (no by choice but needed by requirements)
    '''

    def post(self, request, *args, **kwargs):
        queryset = Post.objects.filter(id=kwargs['uuidOfPost']).first()
        serializer = self.serializer_class(queryset, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    '''
        Creating new post based on uuid for post provided by the user
    '''

    def put(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    '''
        Deleting a specified post
    '''

    def delete(self, request, *args, **kwargs):
        queryset = Post.objects.filter(id=kwargs['uuidOfPost']).first()
        if queryset.author.id == kwargs['uuidOfAuthor']:
            queryset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class PostMutipleDetailView(generics.ListCreateAPIView):

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_author(self, author_id):
        # Validate given author
        try:
            author = get_object_or_404(Author.objects.all(), id=author_id)
            return author
        except:
            raise Http404()

    def get(self, request, *args, **kwargs):
        queryset = Post.objects.filter(author__id=kwargs['uuidOfAuthor'])
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # adding extra data to context object becoz we need to author to create the post

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == 'POST':
            # can also do get_object_or_404..
            context['author'] = Author.objects.filter(
                id=self.kwargs['uuidOfAuthor']).first()
        return context

    # by default does the same as this
    def post(self, request: HttpRequest, *args, **kwargs):
        return self.create(request, *args, **kwargs)
        


class PostAllPublicPost(generics.ListAPIView):

    queryset = Post.objects.all()
    serializer_class = PostSerializer

    '''
           Sends all the public post and post in which a relation of follower and follwoing exists between the authors
           all_post_objects has a list of all public and friend post after filtering the unlisted post
           Cannot do image encoding here becoz broweser compalian about large files
       '''

    def get(self, request, *args, **kwargs):
        # author__ becoz the author is named author in the post model and serializer
        # to get all author posts
        # author__id=kwargs['uuidOfAuthor']

        all_post_objects = []
        queryset = Post.objects.all().exclude(unlisted=True)
        for obj in queryset:
            # adding  the all public post objects anf author self create post
            if (kwargs.get('uuidOfAuthor')) == obj.author.id or obj.visibility == 'PUBLIC':
                all_post_objects.append(obj)
            # if the connection does not exist then it is false or else true (so we add to post when connection exists)
            elif obj.visibility == 'FRIENDS' and bool(Follower.objects.filter(follower__id=kwargs['uuidOfAuthor'], following__id=obj.author.id)):
                all_post_objects.append(obj)
        serializer = self.serializer_class(all_post_objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET", "POST", "DELETE"])
# @permission_classes([IsAuthenticated])
def handleInboxRequests(request, author_id):
    if request.method == "GET":
        try:
            # Auth check
            # if not request.user.is_authenticated or request.user.id != author_id:
            #     return response.Response({"message": "Unauthenticated!"}, status.HTTP_401_UNAUTHORIZED)
            # Retrieve all posts
            allPostIDsInThisAuthorsInbox = Inbox.objects.filter(
                author__id=author_id, object_type="post")
            setOfIds = set([o.object_id for o in allPostIDsInThisAuthorsInbox])
            allPosts = Post.objects.filter(id__in=setOfIds)
            items = PostSerializer(allPosts, many=True)
            resp = {
                "type": "inbox",
                "author": request.user.url(),
                "items": items.data
            }
            return response.Response(resp, 200)
        except:
            return response.Response({"message": "Something went wrong!"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == "POST":
        try:
            try:
                message = "None"
                postType = str(request.data["type"]).lower()
                if not postType in {"post", "comment", "like", "follow", "share"}:
                    raise KeyError("Invalid post type!")
 
                if postType == "like":
                    print(request.data)
                    data = {
                        "object_type": request.data["data"]["type"],
                        "author": request.data["data"]["author"],
                        "object_id": request.data["data"]["id"],
                    }
                    print(request.data["data"]["author_id"])
                    serializer = LikeSerializer(
                        data=data, partial=True)
                 
                    if not serializer.is_valid(raise_exception=True):
                        raise KeyError("like object not valid!")

                    authorID, postID, commentID = utils.getAuthorIDandPostIDFromLikeURL(
                        serializer.data["object_id"])

                    if authorID != None and postID != None and commentID != None:
                        message = f'{request.user.username} liked your comment {request.data["data"]["comment"]}'
                        l = Like.objects.get_or_create(
                            author_id=request.user.id, object_type="comment", object_id=commentID)
                    elif authorID != None and postID != None:
                        message = f'{request.user.username} liked your post {request.data["data"]["title"]}'
                        l = Like.objects.get_or_create(
                            author_id=request.user.id, object_type="post", object_id=postID)
                    else:
                        raise KeyError("like object not valid!")
                    idOfItem = l[0].id
                 
                    Inbox.objects.create(author_id=request.data["data"]["title"],
                                     object_type=postType, object_id=idOfItem, message=message)

                else:
                    
             
                    type = request.data["type"].lower()
                    
                    if type == "comment":
                        message = f'{request.data["author"]["username"]}  commented on your post'
                    elif type == "post":
                        message = f'{request.data["author"]["username"]} added a new post {request.data["title"]}'
                    elif type == "share":
                        message = f'{request.GET.get("username")} shared a post with you.'
                        postType = 'post'
                    elif type == "follow":
 
                        print(author_id)
                        message = f'{request.data["data"]["sender"]["displayName"]} send you a follow request.'
                        postType = "follow"
                     
                    Inbox.objects.create(author_id=author_id,
                                     object_type=postType, object_id=request.data["data"]["id"], message=message)
                return response.Response({"message": message}, status.HTTP_201_CREATED)
            except Exception as e:
                return response.Response({"message": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response.Response({"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == "DELETE":
        try:
            Inbox.objects.filter(author__id=author_id).delete()
            return response.Response({"message": "Inbox cleared!"}, status.HTTP_200_OK)
        except:
            return response.Response({"message": "Something went wrong!"}, status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "DELETE"])
# @permission_classes([IsAuthenticated])
def getEntireInboxRequests(request, author_id):
    if request.method == "GET":
        try:
            # Auth check
            # if request.user.id != author_id:
            #     return response.Response({"message": "Can't retreive someone else's inbox!"}, status.HTTP_401_UNAUTHORIZED)
            # Get inbox
            inboxObjects = Inbox.objects.filter(author__id=author_id)

            # Make return object!

            def helperFunc(obj: Inbox):
                serializerClass = None
                objectToSerialize = None
                data = None
                if obj.object_type == "post":
                    objectToSerialize = Post.objects.get(id=obj.object_id)
                    serializerClass = PostSerializer
                elif obj.object_type == "comment":
                    objectToSerialize = Comment.objects.get(id=obj.object_id)
                    serializerClass = CommentSerializer
                elif obj.object_type == "like":
                    objectToSerialize = Like.objects.get(id=obj.object_id)
                    serializerClass = LikeSerializer
                elif obj.object_type == "follow":
                    objectToSerialize = Author.objects.get(id=obj.object_id)
                    serializerClass = GetAuthorSerializer
                if objectToSerialize is None and obj.object_type == "following":
                    # "authors/" becoz in the frontent we split at authors/ for id
                    # sending the id of the person who accepted the follow request becoz
                    # in the frontend we can link to the redirect to profile on click
                    data = {"type": "follow",
                            "author" : { "id" : "authors/"+str(obj.object_id)}
                            }
                else:
                    s = serializerClass(objectToSerialize)

                return {"data": data or s.data, "message": obj.message}

            items = list(map(helperFunc, inboxObjects))
            resp = {
                "type": "inbox",
                "author": request.user.url(),
                "items": items,
            }
            return response.Response(resp, 200)

        except Exception as e:
            return response.Response({"message": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == "DELETE":
        print(request.data)
        id = utils.getUUID(request.data["id"])
        try:
            Inbox.objects.filter(author__id=author_id, object_id=id).delete()
            return response.Response({"message": "Inbox cleared!"}, status.HTTP_204_NO_CONTENT)
        except:
            return response.Response({"message": "Something went wrong!"}, status.HTTP_500_INTERNAL_SERVER_ERROR)

# def get_post_likes(post_id):
#     likes = Like.objects.filter(post=post_id)
#     return likes



def postIndex(request: HttpRequest):
    host = request.scheme + "://" + request.get_host()
    posts = Post.objects.filter(visibility="PUBLIC", unlisted=False)

    for post in posts:
        post.numberOfLikes =  0 #len(get_post_likes(post.id)) 
        #post.topComments = get_latest_comments(post.id)
    context = {
        'posts': posts,
        'host' : host,
        }
    return render(request, 'index.html', context)

def myPosts(request: HttpRequest):
    if request.user.is_anonymous or not (request.user.is_authenticated):
        return render(request,'index.html')
    author = Author.objects.get(id=request.user.id)
    posts = Post.objects.filter(author=author)
    host = request.scheme + "://" + request.get_host()
    for post in posts:
        post.numberOfLikes = 0 #len(get_post_likes(post.id)) 
        #post.topComments = get_latest_comments(post.id)
    context = {
        'posts': posts,
        'userAuthor': author,
        'host': host,
        }
    return render(request, 'index.html', context)

def createpost(request: HttpRequest):
    author = Author.objects.filter(id=request.user.id).first()
    host = request.scheme + "://" + request.get_host()
    context = {
            'author' : author,
            'host': host,
        }
    return render(request,'create.html',context)


def Inboxs(request: HttpRequest):
    if request.user.is_anonymous or not (request.user.is_authenticated):
        return render(request,'index.html')
    author = Author.objects.get(id=request.user.id)
    posts = Inbox.objects.filter(author=author)
    host = request.scheme + "://" + request.get_host()
    context = {
        'posts': posts,
        'host': host,
        }
    
    return render(request, 'Inboxs.html', context)

def editpost(request: HttpRequest, post_id: str):
    if request.user.is_anonymous or not (request.user.is_authenticated):
        return render(request,'edit.html')
    author=Author.objects.get(id = request.user.id)
    post = Post.objects.get(id=post_id)
    host = request.scheme + "://" + request.get_host()
    context = {'author' : author, 'post': post, 'host': host}
    return render(request,'edit.html',context)

def deletepost(request: HttpRequest, post_id: str):
    if request.user.is_anonymous or not (request.user.is_authenticated):
        return render(request,'index.html')
    author=Author.objects.get(id = request.user.id)
    post = Post.objects.get(id=post_id)
    if post.author.id == author.id:
        post.delete()
    return redirect('post:index')

class getAllPostLikes(generics.ListAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.queryset.filter(object_id = kwargs.get('uuidOfPost'))
        serializers = self.serializer_class(queryset, many= True)

        return Response(serializers.data, 200)


@api_view(["GET"])
def getForeignPosts(request):
    '''
    Used to get all the foreign posts
    connected with team 8 and team 7
    '''
    combined_author = []

    team8 = 'https://c404-team8.herokuapp.com/api/'
    team7 = 'https://cmput404-social.herokuapp.com/service/' 
    team17 = 'https://cmput404f22t17.herokuapp.com/'   
    #local_Authors = Author.objects.all()
    
    t8_remote_response = requests.get(f'{team8}authors/')
    print(t8_remote_response)
    team7_remote_response = requests.get(f'{team7}authors/')
    team17_remote_response = requests.get(f'{team17}authors/')

    #serializer = GetAuthorSerializer(local_Authors, many=True)
    #combined_author = serializer.data

    if t8_remote_response.status_code == 200:
        print('connect to team 8')
        team8_data = t8_remote_response.json()
        team8_Authors = team8_data['items']
        team8_Authors = id_cleaner(team8_Authors)
        combined_author.extend(team8_Authors)

    if team7_remote_response.status_code == 200:
        print('connect to team 7')
        team7_data = team7_remote_response.json()
        team7_Authors = team7_data['items']
        combined_author.extend(team7_Authors)

    if team17_remote_response.status_code == 200:
        print('connect to team 17')
        team17_data = team17_remote_response.json()
        team17_Authors = team17_data['items']
        team17_Authors = id_cleaner(team17_Authors)
        combined_author.extend(team17_Authors)
    
    context = {
        "type": "authors",
        "items": combined_author
    }

    data = []
    authorId=[]
    posts = []

    finalPost = {}


    for result in context['items']:
        authorId.append(result['id'])

    for i in authorId:
        response = requests.get(f"{team8}authors/{i}/posts", params=request.GET)
        
        if response.status_code == 200:
            posts = response.json()['items']
            data.append(posts)


    for post in data:
        if len(post) == 0:
            data.remove(post)
    
    
    finalPost = {
        "posts": data
    }

    print(finalPost["posts"])

    
    return render(request, 'foreignPosts.html', finalPost)
