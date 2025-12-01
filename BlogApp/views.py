# BlogApp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.urls import reverse_lazy
from django.contrib.auth import login,logout
from django.contrib.auth.models import Group,User
from .forms import WriterRegistrationForm
from .forms import UserUpdateForm, ProfileUpdateForm # <-- ADD THIS
from django.contrib import messages # <-- ADD THIS
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.http import JsonResponse
# ... (existing imports) ...
from django.db.models import Count, Sum
from .models import Post
from .models import Profile # <-- Make sure this is imported
from django.db.models import Q
# --- Helper Function for Decorators ---

def is_writer(user):
    """Checks if the user is in the 'Writers' group"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='Writers').exists()

# Decorators for the Writer Panel
writer_required = user_passes_test(is_writer, login_url=reverse_lazy('post_list'))
login_and_writer_required = [login_required, writer_required]


# --- Reader Panel Views (Public) ---

class PostListView(View):
    """
    Reader Panel: View all published posts in a single list.
    """
    def get(self, request, *args, **kwargs):
        # This gets all posts
        all_posts = Post.objects.all().order_by('-created_at')
        
        # This passes them to the template as a variable named 'posts'
        context = {
            'posts': all_posts
        }
        return render(request, 'BlogApp/post_list.html', context)

class PostDetailView(View):
    """
    Reader Panel: View a single post and its comments.
    Handles GET (viewing) and POST (commenting).
    """
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        comments = post.comments.all()
        comment_form = CommentForm()
        
        context = {
            'post': post,
            'comments': comments,
            'comment_form': comment_form
        }
        return render(request, 'BlogApp/post_detail.html', context)

    def post(self, request, pk, *args, **kwargs):
        """
        This method handles the POST request for adding a comment.
        """
        if not request.user.is_authenticated:
            return redirect('login')
        
        post = get_object_or_404(Post, pk=pk)
        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            new_comment.save()
            return redirect('post_detail', pk=post.pk)
        else:
            # If form is invalid, re-render the page with the errors
            comments = post.comments.all()
            context = {
                'post': post,
                'comments': comments,
                'comment_form': comment_form # Pass the invalid form back
            }
            return render(request, 'BlogApp/post_detail.html', context)

# --- Writer Panel Views (Protected) ---

@method_decorator(login_and_writer_required, name='dispatch')
class PostCreateView(View):
    """
    Writer Panel: Create a new blog post.
    """
    def get(self, request, *args, **kwargs):
        form = PostForm()
        context = {'form': form, 'type': 'Create'}
        return render(request, 'BlogApp/post_form.html', context)

    def post(self, request, *args, **kwargs):
        # --- THIS IS THE CHANGE: Pass request.FILES ---
        form = PostForm(request.POST, request.FILES) 
        
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
        
        context = {'form': form, 'type': 'Create'}
        return render(request, 'BlogApp/post_form.html', context)

@method_decorator(login_and_writer_required, name='dispatch')
class PostUpdateView(View):
    """
    Writer Panel: Edit an existing blog post.
    """
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        
        if post.author != request.user:
            return redirect('post_list')

        form = PostForm(instance=post)
        context = {'form': form, 'type': 'Update'}
        return render(request, 'BlogApp/post_form.html', context)

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)

        if post.author != request.user:
            return redirect('post_list')
        
        # --- THIS IS THE CHANGE: Pass request.FILES ---
        form = PostForm(request.POST, request.FILES, instance=post)
        
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=post.pk)

        context = {'form': form, 'type': 'Update'}
        return render(request, 'BlogApp/post_form.html', context)
@method_decorator(login_and_writer_required, name='dispatch')
class PostDeleteView(View):
    """
    Writer Panel: Delete a post.
    Handles GET (show confirmation) and POST (confirm delete).
    """
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        
        # Security check: Only the author can delete
        if post.author != request.user:
            return redirect('post_list')
        
        return render(request, 'BlogApp/post_confirm_delete.html', {'post': post})

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)

        # Security check: Only the author can delete
        if post.author != request.user:
            return redirect('post_list')

        post.delete()
        return redirect('post_list')

class RegisterView(View):
    """
    Handles new writer registration.
    GET: Shows the registration form.
    POST: Creates a new user, adds them to the 'Writers' group, and logs them in.
    """
    def get(self, request, *args, **kwargs):
        # If user is already logged in, redirect them
        if request.user.is_authenticated:
            return redirect('post_list')
        
        form = WriterRegistrationForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('post_list')
        
        form = WriterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # Create the new user account
            
            try:
                # --- THIS IS THE KEY PART ---
                # Find the 'Writers' group and add the new user to it.
                writer_group = Group.objects.get(name='Writers')
                user.groups.add(writer_group)
            except Group.DoesNotExist:
                # This is a server configuration error.
                # The 'Writers' group MUST be created in the admin panel.
                print("CRITICAL: 'Writers' group not found. User was created but NOT added to the 'Writers' group.")
                pass 
            
            login(request, user) # Log the new user in
            return redirect('post_list')
        else:
            # If form is invalid, re-render the page with the form and its errors
            return render(request, 'registration/register.html', {'form': form})
        


def custom_logout_view(request):
    """
    Logs the user out on a GET request and redirects to the homepage.
    """
    logout(request)
    # This will use the LOGOUT_REDIRECT_URL from your settings.py
    return redirect('post_list')

@method_decorator(login_and_writer_required, name='dispatch')
class MyPostsView(View):
    """
    Writer Panel: Show a list of posts written *only* by the logged-in user.
    """
    def get(self, request, *args, **kwargs):
        # Filter posts where the author is the currently logged-in user
        my_posts = Post.objects.filter(author=request.user).order_by('-created_at')
        
        context = {
            'posts': my_posts
        }
        return render(request, 'BlogApp/my_posts.html', context)
    

@method_decorator(login_required, name='dispatch')
class PostVoteView(View):
    """
    Handles liking and disliking a post.
    A user can only like or dislike, not both.
    """
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        vote_type = request.POST.get('vote') # Will be 'like' or 'dislike'

        if vote_type == 'like':
            if user in post.likes.all():
                # User already liked it, so remove the like
                post.likes.remove(user)
            else:
                # Add the like
                post.likes.add(user)
                # If user had disliked it, remove the dislike
                if user in post.dislikes.all():
                    post.dislikes.remove(user)
        
        elif vote_type == 'dislike':
            if user in post.dislikes.all():
                # User already disliked it, so remove the dislike
                post.dislikes.remove(user)
            else:
                # Add the dislike
                post.dislikes.add(user)
                # If user had liked it, remove the like
                if user in post.likes.all():
                    post.likes.remove(user)

        # Redirect back to the post detail page
        return redirect('post_detail', pk=post.pk)
    

# ... (all your other views) ...

# --- ADD THIS NEW VIEW AT THE END ---
@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    """
    Display and update the user's OWN profile.
    """
    def get(self, request, *args, **kwargs):
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # --- CALCULATE STATS ---
        # This is the code your editor says is missing
        user_posts = Post.objects.filter(author=request.user)
        post_count = user_posts.count()

        stats = user_posts.annotate(
            num_likes=Count('likes'),
            num_comments=Count('comments')
        ).aggregate(
            total_likes=Sum('num_likes'),
            total_comments=Sum('num_comments')
        )
        total_likes = stats['total_likes'] or 0
        total_comments = stats['total_comments'] or 0
        # --- END STATS CALCULATION ---
        
        # --- GET FOLLOWER STATS ---
        follower_count = profile.followers.count()
        following_count = profile.following.count()
        # ---

        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

        context = {
            'u_form': u_form,
            'p_form': p_form,
            'post_count': post_count,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'follower_count': follower_count,
            'following_count': following_count
        }
        return render(request, 'BlogApp/profile.html', context)

    def post(self, request, *args, **kwargs):
        profile, created = Profile.objects.get_or_create(user=request.user)

        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, 
                                   request.FILES, 
                                   instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            # --- THIS IS THE FIX FROM BEFORE ---
            # We must re-calculate all stats if the form is invalid
            user_posts = Post.objects.filter(author=request.user)
            post_count = user_posts.count()
            
            stats = user_posts.annotate(
                num_likes=Count('likes'),
                num_comments=Count('comments')
            ).aggregate(
                total_likes=Sum('num_likes'),
                total_comments=Sum('num_comments')
            )
            total_likes = stats['total_likes'] or 0
            total_comments = stats['total_comments'] or 0
            
            follower_count = profile.followers.count()
            following_count = profile.following.count()
            # --- END OF FIX ---

            context = {
                'u_form': u_form,
                'p_form': p_form,
                'post_count': post_count,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'follower_count': follower_count,
                'following_count': following_count
            }
            return render(request, 'BlogApp/profile.html', context)
class PublicProfileView(View):
    """
    Display a read-only public profile for any user.
    """
    def get(self, request, username, *args, **kwargs):
        # Find the user by their username
        profile_user = get_object_or_404(User, username=username)
        profile, created = Profile.objects.get_or_create(user=profile_user)
        
        # Get their posts
        user_posts = Post.objects.filter(author=profile_user).order_by('-created_at')
        
        # Get their stats
        post_count = user_posts.count()
        stats = user_posts.annotate(num_likes=Count('likes')).aggregate(total_likes=Sum('num_likes'))
        total_likes = stats['total_likes'] or 0
        
        # Get follower stats
        follower_count = profile.followers.count()
        following_count = profile.following.count()
        
        # Check if the logged-in user is following this profile
        is_following = False
        if request.user.is_authenticated:
            # Check if the user's profile is in the logged-in user's 'following' list
            is_following = request.user.profile.following.filter(user=profile_user).exists()

        context = {
            'profile_user': profile_user, # The user we are looking at
            'profile': profile,        # Their profile
            'posts': user_posts,
            'post_count': post_count,
            'total_likes': total_likes,
            'follower_count': follower_count,
            'following_count': following_count,
            'is_following': is_following
        }
        return render(request, 'BlogApp/public_profile.html', context)


# --- ADD THIS NEW VIEW (FOLLOW/UNFOLLOW LOGIC) ---
@method_decorator(login_required, name='dispatch')
class FollowView(View):
    """
    Handles the logic for following and unfollowing a user.
    """
    def post(self, request, username, *args, **kwargs):
        # User to follow
        user_to_toggle = get_object_or_404(User, username=username)
        
        # Logged-in user's profile
        current_user_profile = request.user.profile
        
        # Prevent following yourself
        if user_to_toggle == request.user:
            return redirect('public_profile', username=username)

        # Check if we are already following this user's profile
        if current_user_profile.following.filter(user=user_to_toggle).exists():
            # If yes, unfollow
            current_user_profile.following.remove(user_to_toggle.profile)
        else:
            # If no, follow
            current_user_profile.following.add(user_to_toggle.profile)
            
        return redirect('public_profile', username=username)
    

# --- ADD THIS NEW VIEW CLASS AT THE END ---
class CheckUsernameView(View):
    """
    This view is called by JavaScript to check if a username is available.
    """
    def get(self, request, *args, **kwargs):
        # Get the username from the
        # URL (e.g., /check-username/?username=alex)
        username = request.GET.get('username', None)
        
        if not username:
            return JsonResponse({'error': 'Username not provided'}, status=400)

        # Check if a user with this username already exists (case-insensitive)
        is_available = not User.objects.filter(username__iexact=username).exists()
        
        # Return the result as JSON
        return JsonResponse({'is_available': is_available})
    


# --- ADD THIS NEW VIEW CLASS AT THE END ---
class SearchView(View):
    """
    Handles the search query and displays a results page.
    """
    def get(self, request, *args, **kwargs):
        # Get the search query from the URL (e.g., /search/?q=myquery)
        query = request.GET.get('q', '')
        
        results = [] # Start with an empty list

        if query:
            # If a query exists, search the Post model
            # Q() objects allow us to use OR logic
            # __icontains = case-insensitive "contains"
            results = Post.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            ).distinct().order_by('-created_at')
        
        context = {
            'results': results, # The list of posts found
            'query': query      # The original search term
        }
        return render(request, 'BlogApp/search_results.html', context)