import os
import fitz  # PyMuPDF
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.core.files import File
from .models import Book
from .forms import BookForm
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

# ===============================
# Helper untuk konversi PDF -> Images
# ===============================
def convert_pdf_to_images(pdf_path, output_dir, dpi=150):
    """
    Convert PDF file into PNG images, one per page.
    Returns list of saved image file paths.
    """
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))

        filename = f"page_{page_num + 1}.png"
        file_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)

        pix.save(file_path)
        image_paths.append(file_path)

    doc.close()
    return image_paths

# ===============================
# Upload Book + Konversi PDF
# ===============================
@login_required
def upload_book(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("pdf")
        title = request.POST.get("title")
        description = request.POST.get("description", "")
        author = request.POST.get("author", "")
        year = request.POST.get("year", "")
        genre = request.POST.get("genre", "")

        if not pdf_file:
            messages.error(request, "PDF file must be uploaded.")
            return redirect("books:upload")

        # Simpan PDF ke media
        book = Book.objects.create(
            title=title,
            description=description,
            author=author,
            year=year,
            genre=genre,
            pdf=pdf_file,
            uploader=request.user,
        )

        pdf_path = os.path.join(settings.MEDIA_ROOT, book.pdf.name)
        output_dir = os.path.join(settings.MEDIA_ROOT, "books", "pages", str(book.id))

        # Convert PDF ke images
        image_paths = convert_pdf_to_images(pdf_path, output_dir)

        # Ambil halaman pertama sebagai cover
        if image_paths:
            with open(image_paths[0], "rb") as f:
                book.cover.save(f"cover_{book.id}.png", File(f), save=True)

        messages.success(request, "Book successfully uploaded & converted!")
        return redirect("books:detail", slug=book.slug)

    return render(request, "books/upload.html")

# ===============================
# CRUD Views
# ===============================
@login_required
def book_create(request):
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.uploader = request.user
            book.save()

            # convert pdf jika ada
            if book.pdf:
                pdf_path = os.path.join(settings.MEDIA_ROOT, book.pdf.name)
                output_dir = os.path.join(settings.MEDIA_ROOT, "books", "pages", str(book.id))
                image_paths = convert_pdf_to_images(pdf_path, output_dir)

                if image_paths:
                    with open(image_paths[0], "rb") as f:
                        book.cover.save(f"cover_{book.id}.png", File(f), save=True)

            messages.success(request, "Book successfully uploaded & converted.")
            return redirect("books:detail", slug=book.slug)
    else:
        form = BookForm()

    return render(request, "books/form.html", {"form": form, "title": "Upload Buku"})

@login_required
def book_edit(request, slug):
    book = get_object_or_404(Book, slug=slug)

    if request.method == "POST":
        file = request.FILES.get("file")
        book.title = request.POST.get("title")
        book.description = request.POST.get("description")
        book.author = request.POST.get("author")
        book.year = request.POST.get("year")
        book.genre = request.POST.get("genre")

        if file:
            book.pdf = file
            book.cover.delete(save=False)
            book.save()

            pdf_path = os.path.join(settings.MEDIA_ROOT, book.pdf.name)
            output_dir = os.path.join(settings.MEDIA_ROOT, "books", "pages", str(book.id))
            image_paths = convert_pdf_to_images(pdf_path, output_dir)

            if image_paths:
                with open(image_paths[0], "rb") as f:
                    book.cover.save(f"cover_{book.id}.png", File(f), save=True)
        else:
            book.save()

        messages.success(request, "Book updated successfully!")
        return redirect("books:detail", slug=book.slug)

    return render(request, "books/book_edit.html", {"book": book})

@login_required
def book_delete(request, slug):
    book = get_object_or_404(Book, slug=slug)

    if book.uploader != request.user and not request.user.is_superuser:
        messages.warning(request, "You don’t have permission to delete this book.")
        return redirect("books:detail", slug=slug)

    if request.method == "POST":
        book.delete()
        messages.success(request, "The book was successfully deleted.")
        return redirect("books:catalog")

    return render(request, "books/delete_confirm.html", {"book": book})

# ===============================
# Favorites
# ===============================
@login_required
def toggle_favorite(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if book.favorited_by.filter(id=request.user.id).exists():
        book.favorited_by.remove(request.user)
    else:
        book.favorited_by.add(request.user)

    return redirect(request.META.get("HTTP_REFERER", "books:catalog"))

# ===============================
# List & Detail Views
# ===============================
class BookListView(ListView):
    model = Book
    template_name = "books/catalog.html"
    context_object_name = "books"
    paginate_by = 5

    def get_queryset(self):
        queryset = Book.objects.all()
        user = self.request.user

        # search
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(author__icontains=q))

        # filter favorite
        favorite = self.request.GET.get("favorite")
        if favorite == "1" and user.is_authenticated:
            queryset = queryset.filter(favorited_by=user)

        # filter genre
        genre = self.request.GET.get("genre")
        if genre and genre not in ["All Genres", "", None]:
            queryset = queryset.filter(genre__iexact=genre)

        return queryset.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["favorite"] = self.request.GET.get("favorite", "0")
        context["genre"] = self.request.GET.get("genre", "All Genres")

        user = self.request.user
        for b in context["books"]:
            b.is_favorited = (
                user.is_authenticated and b.favorited_by.filter(id=user.id).exists()
            )
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = "books/detail.html"
    context_object_name = "book"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.object
        request = self.request

        context["can_edit"] = request.user.is_authenticated and (
            book.uploader == request.user or request.user.is_superuser
        )
        context["absolute_pdf_url"] = (
            request.build_absolute_uri(book.pdf.url) if book.pdf else None
        )
        context["is_favorite"] = book.is_favorite(request.user)
        return context

# ===============================
# Analyze (placeholder)
# ===============================
nltk.download("stopwords")
from nltk.corpus import stopwords

@login_required
def book_analyze(request, slug):
    book = get_object_or_404(Book, slug=slug)

    # Baca isi PDF
    pdf_path = os.path.join(settings.MEDIA_ROOT, book.pdf.name)
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()

    if not text.strip():
        messages.warning(request, "No text found in this PDF for analysis.")
        return redirect("books:detail", slug=slug)

    # Ekstraksi kata kunci dengan TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english", max_features=20)
    X = vectorizer.fit_transform([text])
    scores = X.toarray()[0]

    keywords = sorted(
        zip(vectorizer.get_feature_names_out(), scores),
        key=lambda x: x[1],
        reverse=True,
    )

    # Masukkan ke context manual (ubah skor ke persen)
    return render(
        request,
        "books/detail.html",
        {
            "book": book,
            "can_edit": request.user == book.uploader or request.user.is_superuser,
            "absolute_pdf_url": request.build_absolute_uri(book.pdf.url),
            "is_favorite": book.is_favorite(request.user),
            "keywords": [
                {"word": w, "score": round(s * 100, 2)} for w, s in keywords
            ],
        },
    )

# ===============================
# Preview Buku
# ===============================
class BookPreviewView(DetailView):
    model = Book
    template_name = "books/preview.html"
    context_object_name = "book"
    slug_field = "slug"
    slug_url_kwarg = "slug"
