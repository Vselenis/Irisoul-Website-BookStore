from django.db.models import Count, Prefetch, Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from products.models import Product


from .forms import CommentForm
from .models import Category, Comment, Post, Tag

# Create your views here.


class BlogSidebarMixin:
    discover_count = 3

    def get_sidebar_categories(self):

        return list(
            Category.objects.annotate(post_count=Count('posts', filter=Q(posts__is_published=True)))
            .filter(post_count__gt=0)
        )

    def get_sidebar_tags(self):
        return list(Tag.objects.filter(posts__is_published= True).distinct())

    def get_discover_books(self):
        return list(
            Product.objects.filter(product_type=Product.ProductType.BOOK)
            .available()
            .select_related('bundle')
            .prefetch_related('categories')
            .order_by('?')[:self.discover_count]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sidebar_categories': self.get_sidebar_categories(),
            'sidebar_tags': self.get_sidebar_tags(),
            'discover_books': self.get_discover_books(),
            'search_query': self.request.GET.get('q', '').strip(),
        })
        return context


class PostListView(BlogSidebarMixin, ListView):
    template_name='blog/post_list.html'
    context_object_name='posts'
    paginate_by = 3

    def get_queryset(self):
        posts = Post.objects.published().select_related('author', 'category').annotate(
            comment_count=Count('comments', distinct=True),
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            posts = posts.filter(title__icontains=query)
        category = self.request.GET.get('category')
        if category:
            posts = posts.filter(category__slug=category)
        tag = self.request.GET.get('tag')
        if tag:
            posts = posts.filter(tags__slug=tag)
        return posts


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_range'] = context['paginator'].get_elided_page_range(
            context['page_obj'].number,
            on_each_side=1,
            on_ends=1,
        )

        return context


class PostDetailView(BlogSidebarMixin, DetailView):
    template_name ='blog/post_detail.html'
    context_object_name = 'post'
    related_count=2

    def get_queryset(self):
        return Post.objects.published().select_related('author', 'category').prefetch_related('tags')

    def get_comments(self):
        return list(
            self.object.comments.filter(parent__isnull=True)
            .select_related('user')
            .prefetch_related(Prefetch('replies', queryset=Comment.objects.select_related('user')))
        )

    def get_comment_count(self):
        return self.object.comments.count()

    def get_related_posts(self):
        return list(
            Post.objects.published()
            .exclude(pk=self.object.pk)
            .select_related('author')
            .order_by('?')[:self.related_count]
        )

    def get_reply_target(self, value):
        if not str(value or '').isdigit():
            return None

        return self.object.comments.select_related('user').filter(pk=value).first()

    def get_context_data(self, **kwargs):
        kwargs.setdefault('form', CommentForm())
        if 'reply_to' not in kwargs:
            kwargs['reply_to'] = self.get_reply_target(self.request.GET.get('reply_to'))
        context = super().get_context_data(**kwargs)
        context.update({
            'comments': self.get_comments(),
            'comment_count': self.get_comment_count(),
            'related_posts': self.get_related_posts(),
        })

        return context

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        reply_to = self.get_reply_target(request.POST.get('reply_to'))
        if not request.user.is_authenticated:
            return self.render_to_response(self.get_context_data(reply_to=reply_to))
        form = CommentForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, reply_to=reply_to))
        form.instance.post = self.object
        form.instance.user = request.user
        if reply_to is not None:
            form.instance.parent_id = reply_to.parent_id or reply_to.pk
        comment = form.save()
        return redirect(f'{self.object.get_absolute_url()}#comment-{comment.pk}')
