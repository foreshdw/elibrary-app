from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import fitz, os, json
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings
from django.db.models import JSONField

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    pdf = models.FileField(upload_to="pdfs/")
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    genre = models.CharField(max_length=50, choices=[
        ("Fiction", "Fiction"),
        ("Comic", "Comic"),
        ("Motivational", "Motivational"),
    ])
    page_images_json = models.JSONField(default=list, blank=True)
    favorited_by = models.ManyToManyField(User, related_name="favorite_books", blank=True)
    keywords = JSONField(blank=True, null=True)

    def is_favorite(self, user):
        return user.is_authenticated and self.favorited_by.filter(id=user.id).exists()
    
    def delete(self, *args, **kwargs):
        # hapus file cover
        if self.cover and os.path.isfile(self.cover.path):
            os.remove(self.cover.path)
        # hapus file pdf
        if self.pdf and os.path.isfile(self.pdf.path):
            os.remove(self.pdf.path)
        super().delete(*args, **kwargs)

    meta_title = models.CharField(max_length=255, blank=True)
    meta_author = models.CharField(max_length=255, blank=True)
    num_pages = models.IntegerField(default=0)
    keywords_json = models.TextField(blank=True)

    page_images_json = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # ========================== UTILITIES ==========================

    def _extract_text(self, path: str) -> str:
        try:
            doc = fitz.open(path)
            all_text = [page.get_text("text") for page in doc]
            doc.close()
            return "\n".join(all_text)
        except Exception:
            return ""

    def _analyze_keywords(self, text: str, topk: int = 10):
        if not text.strip():
            return []
        try:
            vec = TfidfVectorizer(stop_words="indonesian", max_features=2000)
            X = vec.fit_transform([text])
            feats = vec.get_feature_names_out()
            scores = X.toarray()[0]
            ranked = sorted(zip(feats, scores), key=lambda x: x[1], reverse=True)[:topk]
            return [{"word": w, "score": round(float(s), 4)} for w, s in ranked]
        except Exception:
            return []

    def _render_pages(self, path: str):
        try:
            doc = fitz.open(path)
            if doc.page_count == 0:
                doc.close()
                return

            images = []
            out_dir = os.path.join(settings.MEDIA_ROOT, "page_images", self.slug)
            os.makedirs(out_dir, exist_ok=True)

            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=130)
                filename = f"{self.slug}_page_{i+1}.png"
                out_path = os.path.join(out_dir, filename)
                pix.save(out_path)

                # simpan relative path
                images.append(f"page_images/{self.slug}/{filename}")

                # halaman pertama jadi cover
                if i == 0:
                    self.cover.name = f"page_images/{self.slug}/{filename}"

            self.page_images_json = json.dumps(images)
            doc.close()
        except Exception:
            pass

    # ========================== OVERRIDE SAVE ==========================

    def save(self, *args, **kwargs):
        # generate slug unik
        if not self.slug:
            base = slugify(self.title) or "book"
            slug = base
            i = 1
            while Book.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
    
        super().save(*args, **kwargs)
    
        try:
            pdf_path = self.pdf.path
            doc = fitz.open(pdf_path)
    
            # ambil metadata PDF
            self.num_pages = doc.page_count
            meta = doc.metadata or {}
            self.meta_title = meta.get("title") or ""
            self.meta_author = meta.get("author") or ""
    
            # render semua halaman + cover
            self._render_pages(pdf_path)
    
            # ekstrak teks & analisis keywords
            text = self._extract_text(pdf_path)
            self.keywords_json = json.dumps(self._analyze_keywords(text, topk=10))
    
            doc.close()
    
            # update field hasil analisis
            super().save(update_fields=[
                "num_pages",
                "meta_title",
                "meta_author",
                "cover",
                "keywords_json",
                "page_images_json",
            ])
        except Exception as e:
            print("Error saat memproses PDF:", e)


    # ========================== PROPERTIES ==========================

    @property
    def keywords(self):
        try:
            return json.loads(self.keywords_json) if self.keywords_json else []
        except Exception:
            return []

    @property
    def page_images(self):
        try:
            return json.loads(self.page_images_json) if self.page_images_json else []
        except Exception:
            return []
