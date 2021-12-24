from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .settings import POSTS_PER_PAGE


def pagination(request, posts):
    return(Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page')))


def index(request):
    posts = Post.objects.all()
    return render(request, 'posts/index.html', {
        'page_obj': pagination(request, posts)})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': pagination(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    follow = Follow.objects.filter(user=request.user, author=author)
    if (request.user.is_authenticated and follow.exists()):
        following = True
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': pagination(request, author.posts.all()),
        'following': following
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html', {
        'form': form, 'is_edit': True, 'post_id': post_id})


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_follow = Post.objects.filter(author__following__user=request.user)
    return render(request, 'posts/follow.html', {
        'page_obj': pagination(request, posts_follow)})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
