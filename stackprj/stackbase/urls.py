from django.urls import path
from . import views

app_name = 'stackbase'

urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),

    # CRUD Function
    path('questions/', views.QuestionListView.as_view(), name="question-lists"),
    path('questions/new/', views.QuestionCreateView.as_view(), name="question-create"),
    path('questions/<int:pk>/', views.QuestionDetailView.as_view(), name="question-detail"),
    path('questions/<int:pk>/update/', views.QuestionUpdateView.as_view(), name="question-update"),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name="question-delete"),
    path('questions/<int:pk>/comment/', views.AddCommentView.as_view(), name="question-comment"),
    path('like/<int:pk>', views.like_view, name="like_post"),
    path('questions/tags/<str:tag>/', views.TagQuestionListView.as_view(), name="tag-question-lists"),
    path('get_tags/', views.get_tags, name='get_tags'),
    path('questions/category/<str:category>/', views.CategoryQuestionListView.as_view(), name="category-question-lists"),
    path('questions/<int:question_id>/export/', views.export_question_comments, name="export_question_comments"),

    path('questions/category/<str:category>/export_data/', views.ExportDataView.as_view(), name="export-data-category"),
    path('questions/tags/<str:tag>/export_data/', views.ExportDataView.as_view(), name="export-data-tag"),
    path('questions/export_data/', views.ExportDataView.as_view(), name="export-data"),
    
    path('like-comment/<int:pk>/', views.like_comment, name="like_comment"),

]
