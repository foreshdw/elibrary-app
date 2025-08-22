from django.urls import path
from . import views
from .views import BookPreviewView

app_name = "books"

urlpatterns = [
    path("upload/", views.upload_book, name="upload"),
    path("book/create/", views.book_create, name="create"),
    path("book/<slug:slug>/edit/", views.book_edit, name="edit"),
    path("book/<slug:slug>/delete/", views.book_delete, name="delete"),
    path("catalog/", views.BookListView.as_view(), name="catalog"),
    path("book/<slug:slug>/", views.BookDetailView.as_view(), name="detail"),
    path("book/<slug:slug>/toggle-favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("<slug:slug>/analyze/", views.book_analyze, name="analyze"),
    path("<slug:slug>/preview/", BookPreviewView.as_view(), name="preview"),
]
