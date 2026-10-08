from django.db import models
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

DAILY_FINE_RATE = Decimal('1.00')  # $1.00 per day overdue
DEFAULT_LOAN_DAYS = 14


class Author(models.Model):
    name = models.CharField(max_length=200, help_text="Author's full name")
    biography = models.TextField(blank=True, help_text="Short author biography")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def book_count(self):
        return self.books.count()


class Book(models.Model):
    GENRE_CHOICES = [
        ('Fiction', 'Fiction'),
        ('Non-Fiction', 'Non-Fiction'),
        ('Science & Tech', 'Science & Tech'),
        ('History', 'History'),
        ('Biography', 'Biography'),
        ('Philosophy', 'Philosophy'),
        ('Fantasy & Sci-Fi', 'Fantasy & Sci-Fi'),
        ('Mystery & Thriller', 'Mystery & Thriller'),
        ('Classic Literature', 'Classic Literature'),
        ('Computer Science', 'Computer Science'),
        ('Business & Economics', 'Business & Economics'),
    ]

    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    isbn = models.CharField(max_length=20, unique=True, verbose_name="ISBN")
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, default='Fiction')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    cover_url = models.URLField(
        blank=True,
        null=True,
        help_text="Direct link to book cover image",
        default="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80"
    )
    description = models.TextField(blank=True, help_text="Synopsis or book summary")

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author.name}"

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def borrowed_copies(self):
        return max(0, self.total_copies - self.available_copies)


class Member(models.Model):
    name = models.CharField(max_length=200)
    member_id = models.CharField(max_length=50, unique=True, verbose_name="Member ID")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25, blank=True)
    joined_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.member_id})"

    @property
    def active_loans(self):
        return self.circulation_records.filter(returned=False)

    @property
    def active_loans_count(self):
        return self.active_loans.count()

    @property
    def overdue_loans(self):
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        return self.circulation_records.filter(returned=False, due_date__lt=today)

    @property
    def overdue_count(self):
        return self.overdue_loans.count()

    @property
    def total_fines_accrued(self):
        # Sum of recorded fines for returned books + estimated current overdue fines for unreturned
        returned_fines = sum(r.fine_amount for r in self.circulation_records.filter(returned=True))
        active_fines = sum(r.current_estimated_fine for r in self.active_loans)
        return returned_fines + active_fines


class CirculationRecord(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='circulation_records')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='circulation_records')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True)
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    returned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-issue_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            base_date = self.issue_date if self.issue_date else date.today()
            self.due_date = base_date + timedelta(days=DEFAULT_LOAN_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Returned" if self.returned else "Active"
        return f"{self.book.title} -> {self.member.name} [{status}]"

    @property
    def is_overdue(self):
        if self.returned:
            return False
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        return today > self.due_date

    @property
    def overdue_days(self):
        if self.returned:
            if self.return_date and self.due_date and self.return_date > self.due_date:
                return (self.return_date - self.due_date).days
            return 0
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        if today > self.due_date:
            return (today - self.due_date).days
        return 0

    @property
    def current_estimated_fine(self):
        if self.returned:
            return self.fine_amount
        return Decimal(str(self.overdue_days)) * DAILY_FINE_RATE

    def calculate_final_fine(self, actual_return_date=None):
        if not actual_return_date:
            actual_return_date = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        if actual_return_date > self.due_date:
            days = (actual_return_date - self.due_date).days
            return Decimal(str(days)) * DAILY_FINE_RATE
        return Decimal('0.00')
