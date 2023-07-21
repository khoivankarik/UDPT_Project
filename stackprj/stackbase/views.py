from django.db import models
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import Question, Comment, Tag, Category
from .forms import CommentForm
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from urllib.parse import unquote
from django.http import JsonResponse,HttpResponse

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

# CRUD Function
def like_view(request, pk):
    post = get_object_or_404(Question, id=request.POST.get('question_id'))
    liked = False
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return HttpResponseRedirect(reverse('stackbase:question-detail', args=[str(pk)]))

class QuestionListView(ListView):
    model = Question
    context_object_name = 'questions'
    ordering = ['-date_created']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_input = self.request.GET.get('search-bar') or ""
        if search_input:
            # Extract tags and titles using regex pattern matching
            import re
            pattern = r'\[([^]]+)\]'
            tags = re.findall(pattern, search_input)
            titles = re.sub(pattern, '', search_input).strip().split()

            # Generate queries for tags and titles
            tag_query = Q(tags__name__in=tags)
            title_query = Q()
            for title in titles:
                title_query |= Q(title__icontains=title)

            # Apply filters to the questions queryset
            if tags:
                context['questions'] = context['questions'].filter(tag_query & title_query)
            else:
                context['questions'] = context['questions'].filter(title_query)

            context['search_input'] = search_input
        return context


class QuestionDetailView(DetailView):
    model = Question

    def get_context_data(self, *args, **kwargs):
        context = super(QuestionDetailView, self).get_context_data()
        something = get_object_or_404(Question, id=self.kwargs['pk'])
        total_likes = something.total_likes()
        liked = False
        if something.likes.filter(id=self.request.user.id).exists():
            liked = True

        context['total_likes'] = total_likes
        context['liked'] = liked
        return context

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    fields = ['title', 'content', 'category', 'tags']
    context_object_name = 'question'

    def form_valid(self, form):
        if form.instance.category is None:
            # Handle case where category is not selected
            form.add_error('category', 'Please select a category.')
            return self.form_invalid(form)
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.method == 'POST':
            category_id = self.request.POST.get('category')
            if category_id:
                category = Category.objects.get(id=category_id)
                form.fields['tags'].queryset = category.tags.all()
            else:
                form.fields['tags'].queryset = Tag.objects.none()
        else:
            form.fields['tags'].queryset = Tag.objects.none()
        return form

class QuestionUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    model = Question
    fields = ['title', 'content', 'category', 'tags']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def test_func(self):
        question = self.get_object()
        if self.request.user == question.user:
            return True
        return False

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.method == 'POST':
            category_id = self.request.POST.get('category')
            if category_id:
                category = Category.objects.get(id=category_id)
                form.fields['tags'].queryset = category.tags.all()
            else:
                form.fields['tags'].queryset = Tag.objects.none()
        else:
            form.fields['tags'].queryset = Tag.objects.none()
        return form

class QuestionDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    model = Question
    context_object_name =  'question'
    success_url = "/"

    def test_func(self):
        questions = self.get_object()
        if self.request.user == questions.user:
            return True
        return False

class CommentDetailView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'stackbase/question-detail.html'
    
    def form_valid(self, form):
        form.instance.question_id = self.kwargs['pk']
        return super().form_valid(form)
    success_url = reverse_lazy('stackbase:question-detail')

class AddCommentView(CreateView):
    model = Comment
    form_class = CommentForm
    
    template_name = 'stackbase/question-answer.html'

    def form_valid(self, form):
        form.instance.question_id = self.kwargs['pk']
        return super().form_valid(form)
    success_url = reverse_lazy('stackbase:question-lists')

class TagQuestionListView(ListView):
    model = Question
    template_name = 'stackbase/question_list.html'  # Replace with your actual template name
    context_object_name = 'questions'
    ordering = ['-date_created']

    def get_queryset(self):
        tag = self.kwargs['tag']
        return Question.objects.filter(tags__name=tag)
    
class CategoryQuestionListView(ListView):
    model = Question
    template_name = 'stackbase/question_list.html'  # Replace with your actual template name
    context_object_name = 'questions'
    ordering = ['-date_created']

    def get_queryset(self):
        category_name = self.kwargs['category']
        return Question.objects.filter(category__name=category_name)
    
def get_tags(request):
    if request.method == 'GET':
        category_id = request.GET.get('category_id')
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                tags = category.tags.all()
                data = [{'id': tag.id, 'name': tag.name} for tag in tags]
                return JsonResponse(data, safe=False)
            except Category.DoesNotExist:
                pass
    return JsonResponse([], safe=False)

def export_question_comments(request, question_id):
    # Fetch the question and its comments from the database
    question = get_object_or_404(Question, id=question_id)
    comments = question.comment.all()

    # Create the content of the file (you can customize this based on your requirement)
    content = f"Question Title: {question.title}\n\nQuestion Content:\n{question.content}\n\nComments:\n"

    for comment in comments:
        content += f"- {comment.content}\n"

    # Create the HttpResponse with appropriate headers to trigger a download
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename=question_{question_id}_comments.txt"

    return response