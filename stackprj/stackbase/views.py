from django.db import models
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import Question, Comment, Tag, Category, Report
from .forms import CommentForm, ReportForm
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from urllib.parse import unquote
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from django.http import QueryDict
from django.views import View
import csv
from urllib.parse import urlencode
from django.utils.encoding import smart_str
from io import StringIO
from django.utils.safestring import mark_safe
from django.contrib import messages
from stackusers.models import Profile
from django.db.models import F

def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


# CRUD Function
def like_view(request, pk):
    post = get_object_or_404(Question, id=request.POST.get("question_id"))
    liked = False
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    user_profile = Profile.objects.get(user=request.user)
    user_profile.update_score()
    return HttpResponseRedirect(reverse("stackbase:question-detail", args=[str(pk)]))


def like_comment(request, pk):
    comment = get_object_or_404(Comment, id=pk)
    liked = False
    if comment.likes.filter(id=request.user.id).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    user_profile = Profile.objects.get(user=request.user)
    user_profile.update_score()
    return HttpResponseRedirect(
        reverse("stackbase:question-detail", args=[str(comment.question.pk)])
    )


class QuestionListView(ListView):
    model = Question
    context_object_name = "questions"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_input = self.request.GET.get("search-bar") or ""
        if search_input:
            # Extract tags and titles using regex pattern matching
            import re

            pattern = r"\[([^]]+)\]"
            tags = re.findall(pattern, search_input)
            titles = re.sub(pattern, "", search_input).strip().split()

            # Generate queries for tags and titles
            tag_query = Q(tags__name__in=tags)
            title_query = Q()
            for title in titles:
                title_query |= Q(title__icontains=title)

            # Apply filters to the questions queryset
            if tags:
                context["questions"] = context["questions"].filter(
                    tag_query & title_query
                )
            else:
                context["questions"] = context["questions"].filter(title_query)

            context["search_input"] = search_input

        context["tab"] = self.request.GET.get("tab", None)
        return context

    def get_queryset(self):
        tab = self.request.GET.get("tab", None)
        if tab == "today":
            # Filter questions from today
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=1)
            queryset = Question.objects.filter(
                date_created__gte=start_date, date_created__lt=end_date
            ).order_by("-date_created")
        elif tab == "week":
            # Filter questions from the past week
            start_date = datetime.now() - timedelta(weeks=1)
            queryset = Question.objects.filter(date_created__gte=start_date).order_by(
                "-date_created"
            )
        elif tab == "month":
            # Filter questions from the past month
            start_date = datetime.now() - timedelta(days=30)
            queryset = Question.objects.filter(date_created__gte=start_date).order_by(
                "-date_created"
            )
        else:
            # Default: Show all questions
            queryset = Question.objects.all().order_by("-date_created")

        return queryset


class QuestionDetailView(DetailView):
    model = Question

    def get_context_data(self, *args, **kwargs):
        context = super(QuestionDetailView, self).get_context_data()
        something = get_object_or_404(Question, id=self.kwargs["pk"])
        total_likes = something.total_likes()
        liked = False
        if something.likes.filter(id=self.request.user.id).exists():
            liked = True

        context["total_likes"] = total_likes
        context["liked"] = liked
        return context


def is_valid_text(text):
    # List of words that are not allowed in the text
    blacklist_words = [
        "fuck",
        "bitch",
        "whore",
        "asshole",
        "shit",
        "bastard",
        "cunt",
        "dick",
        "pussy",
        "cock",
        "retard",
        "slut",
        "wanker",
        "jerk",
        "prick",
        "twat",
        "douche",
        "douchebag",
        "moron",
        "idiot",
        "dumbass",
        "dipshit",
        "motherfucker",
        "sonofabitch",
        "bullshit",
        "crap",
        "arse",
        "bollocks",
        "frick",
        "tits",
        "boobs",
    ]

    # Minimum length required for the text
    min_length = 10

    # Check if the text contains any blacklisted words
    for word in blacklist_words:
        if word.lower() in text.lower():
            return False

    # Check if the text meets the minimum length requirement
    if len(text) < min_length:
        return False

    # If the text passes all checks, it is considered valid
    return True


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    fields = ["title", "content", "category", "tags"]
    context_object_name = "question"

    def form_valid(self, form):
        if form.instance.category is None:
            form.add_error("category", "Please select a category.")
            return self.form_invalid(form)

        # Validate question title and content
        if not is_valid_text(form.cleaned_data["title"]):
            messages.error(self.request, "Invalid question title.")
            return self.form_invalid(form)
        if not is_valid_text(form.cleaned_data["content"]):
            messages.error(self.request, "Invalid question content.")
            return self.form_invalid(form)

        form.instance.user = self.request.user
        # Call the update_score function to increase the user's score by 1
        user_profile = Profile.objects.get(user=self.request.user)
        user_profile.update_score()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.method == "POST":
            category_id = self.request.POST.get("category")
            if category_id:
                category = Category.objects.get(id=category_id)
                form.fields["tags"].queryset = category.tags.all()
            else:
                form.fields["tags"].queryset = Tag.objects.none()
        else:
            form.fields["tags"].queryset = Tag.objects.none()
        return form


class QuestionUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
    model = Question
    fields = ["title", "content", "category", "tags"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True  # Set is_update to True for update view
        return context

    def test_func(self):
        question = self.get_object()
        if self.request.user == question.user:
            return True
        return False

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.method == "POST":
            category_id = self.request.POST.get("category")
            if category_id:
                category = Category.objects.get(id=category_id)
                form.fields["tags"].queryset = category.tags.all()
            else:
                form.fields["tags"].queryset = Tag.objects.none()
        else:
            form.fields["tags"].queryset = Tag.objects.none()
        return form

    def get_success_url(self):
        return reverse_lazy("stackbase:question-detail", kwargs={"pk": self.object.pk})


class QuestionDeleteView(UserPassesTestMixin, LoginRequiredMixin, DeleteView):
    model = Question
    context_object_name = "question"
    success_url = "/"

    def test_func(self):
        question = self.get_object()
        user = self.request.user
        if user == question.user or user.is_superuser:
            return True
        return False


class CommentDetailView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "stackbase/question-detail.html"

    def form_valid(self, form):
        form.instance.question_id = self.kwargs["pk"]
        return super().form_valid(form)

    success_url = reverse_lazy("stackbase:question-detail")


class AddCommentView(CreateView):
    model = Comment
    form_class = CommentForm

    template_name = "stackbase/question-answer.html"

    def form_valid(self, form):
        if not is_valid_text(form.cleaned_data["content"]):
            messages.error(self.request, "Invalid comment content.")
            return self.form_invalid(form)

        form.instance.question_id = self.kwargs['pk']
        form.instance.name = self.request.user.username
        response = super().form_valid(form)

        # Call the update_score function to increase the commenter's score by 1
        commenter_profile = Profile.objects.get(user=self.request.user)
        commenter_profile.update_score()

        # Display a success message
        messages.success(self.request, "Comment successfully added!")

        return response
    
    def get_success_url(self):
        return reverse_lazy(
            "stackbase:question-detail", kwargs={"pk": self.kwargs["pk"]}
        )





class TagQuestionListView(ListView):
    model = Question
    template_name = "stackbase/question_list.html"
    context_object_name = "questions"
    ordering = ["-date_created"]

    def get_queryset(self):
        tag = self.kwargs["tag"]
        tab = self.request.GET.get("tab", None)
        query_params = QueryDict(mutable=True)
        query_params.update(self.request.GET)
        query_params.pop(
            "tag", None
        )  # Remove the 'tag' parameter from the query params
        query_string = query_params.urlencode()

        if tab == "today":
            # Filter questions from today with the specified tag
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=1)
            queryset = Question.objects.filter(
                tags__name=tag, date_created__gte=start_date, date_created__lt=end_date
            ).order_by("-date_created")
        elif tab == "week":
            # Filter questions from the past week with the specified tag
            start_date = datetime.now() - timedelta(weeks=1)
            queryset = Question.objects.filter(
                tags__name=tag, date_created__gte=start_date
            ).order_by("-date_created")
        elif tab == "month":
            # Filter questions from the past month with the specified tag
            start_date = datetime.now() - timedelta(days=30)
            queryset = Question.objects.filter(
                tags__name=tag, date_created__gte=start_date
            ).order_by("-date_created")
        else:
            # Show all questions with the specified tag
            queryset = Question.objects.filter(tags__name=tag).order_by("-date_created")

        # Add the 'tab' parameter back to the query string
        if tab:
            query_string += f"&tab={tab}"
        queryset = queryset.order_by("-date_created")
        return queryset


class CategoryQuestionListView(ListView):
    model = Question
    template_name = (
        "stackbase/question_list.html"  # Replace with your actual template name
    )
    context_object_name = "questions"
    ordering = ["-date_created"]

    def get_queryset(self):
        category_name = self.kwargs["category"]
        tab = self.request.GET.get("tab", None)
        query_params = QueryDict(mutable=True)
        query_params.update(self.request.GET)
        query_params.pop(
            "category", None
        )  # Remove the 'category' parameter from the query params
        query_string = query_params.urlencode()

        if tab == "today":
            # Filter questions from today with the specified category
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=1)
            queryset = Question.objects.filter(
                category__name=category_name,
                date_created__gte=start_date,
                date_created__lt=end_date,
            ).order_by("-date_created")
        elif tab == "week":
            # Filter questions from the past week with the specified category
            start_date = datetime.now() - timedelta(weeks=1)
            queryset = Question.objects.filter(
                category__name=category_name, date_created__gte=start_date
            ).order_by("-date_created")
        elif tab == "month":
            # Filter questions from the past month with the specified category
            start_date = datetime.now() - timedelta(days=30)
            queryset = Question.objects.filter(
                category__name=category_name, date_created__gte=start_date
            ).order_by("-date_created")
        else:
            # Show all questions with the specified category
            queryset = Question.objects.filter(category__name=category_name).order_by(
                "-date_created"
            )

        # Add the 'tab' parameter back to the query string
        if tab:
            query_string += f"&tab={tab}"
        queryset = queryset.order_by("-date_created")
        return queryset


def get_tags(request):
    if request.method == "GET":
        category_id = request.GET.get("category_id")
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                tags = category.tags.all()
                data = [{"id": tag.id, "name": tag.name} for tag in tags]
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
    response[
        "Content-Disposition"
    ] = f"attachment; filename=question_{question_id}_comments.txt"

    return response


class ExportDataView(View):
    def get(self, request, *args, **kwargs):
        # Create a StringIO buffer to hold CSV data
        buffer = StringIO()
        writer = csv.writer(buffer)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="questions_data.csv"'

        # Write the BOM (Byte Order Mark) to the response to indicate UTF-8 encoding
        response.write("\ufeff")

        writer.writerow(
            [
                "Title",
                "Content",
                "Asked By",
                "Date Asked",
                "Category",
                "Tags",
                "Comment",
                "Commented By",
            ]
        )

        category_name = self.kwargs.get("category")
        tag_name = self.kwargs.get("tag")

        if category_name:
            category = get_object_or_404(Category, name=category_name)
            questions = Question.objects.filter(category=category)
        elif tag_name:
            tags = get_object_or_404(Tag, name=tag_name)
            questions = Question.objects.filter(tags=tags)
        else:
            questions = Question.objects.all()

        for question in questions:
            title = smart_str(
                question.title
            )  # Use smart_str to ensure correct encoding of title
            content = smart_str(question.content)
            asked_by = smart_str(question.user.username)
            date_asked = question.date_created.strftime("%Y-%m-%d %H:%M:%S")
            category = smart_str(question.category.name if question.category else "")
            tags = ", ".join([smart_str(tag.name) for tag in question.tags.all()])

            comments = Comment.objects.filter(question=question)
            if comments.exists():
                for comment in comments:
                    comment_content = smart_str(comment.content)
                    commented_by = smart_str(comment.name)
                    writer.writerow(
                        [
                            title,
                            content,
                            asked_by,
                            date_asked,
                            category,
                            tags,
                            comment_content,
                            commented_by,
                        ]
                    )
            else:
                writer.writerow(
                    [title, content, asked_by, date_asked, category, tags, "", ""]
                )

        # Set the CSV data to the response and return
        response.write(buffer.getvalue())
        return response


class ReportDetailView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = "stackbase/Report_detail.html"

    def form_valid(self, form):
        if not is_valid_text(form.cleaned_data["description"]):
            messages.error(self.request, "Invalid report description.")
            return self.form_invalid(form)

        question = get_object_or_404(Question, pk=self.kwargs["pk"])
        form.instance.user = self.request.user
        form.instance.question = question
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Report submitted successfully.")
        return reverse_lazy(
            "stackbase:question-detail", kwargs={"pk": self.kwargs["pk"]}
        )

def leaderboard(request):
    # Get user profiles ordered by score in descending order
    profiles = Profile.objects.annotate(rank=F('score')).order_by('-score')

    return render(request, 'stackbase/chart.html', {'profiles': profiles})