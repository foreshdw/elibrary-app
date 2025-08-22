from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from books import views as book_views 

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", book_views.BookListView.as_view(), name="home"),
    path("books/", include("books.urls")),
    path("users/", include("users.urls")),
    # path("", book_views.catalog, name="home"),
    # path("auth/", include("django.contrib.auth.urls")), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
