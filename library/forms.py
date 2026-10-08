from django import forms
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import Author, Book, Member, CirculationRecord, DEFAULT_LOAN_DAYS


class BookIssueForm(forms.ModelForm):
    class Meta:
        model = CirculationRecord
        fields = ['member', 'book', 'issue_date', 'due_date']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select', 'id': 'id_member'}),
            'book': forms.Select(attrs={'class': 'form-select', 'id': 'id_book'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        preselected_book_id = kwargs.pop('book_id', None)
        super().__init__(*args, **kwargs)
        
        # Only show books with available copies > 0 in dropdown
        self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0).order_by('title')
        
        today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        default_due = today + timedelta(days=DEFAULT_LOAN_DAYS)
        
        if not self.initial.get('issue_date'):
            self.initial['issue_date'] = today
        if not self.initial.get('due_date'):
            self.initial['due_date'] = default_due

        if preselected_book_id:
            try:
                selected_book = Book.objects.get(pk=preselected_book_id)
                self.initial['book'] = selected_book
            except Book.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        book = cleaned_data.get('book')
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')

        if book and book.available_copies <= 0:
            raise forms.ValidationError(f"Cannot issue '{book.title}': No available copies left.")

        if issue_date and due_date and due_date < issue_date:
            raise forms.ValidationError("Due date cannot be earlier than issue date.")

        return cleaned_data


class BookReturnForm(forms.Form):
    return_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_return_date'})
    )


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'genre', 'total_copies', 'available_copies', 'cover_url', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. The Great Gatsby'}),
            'author': forms.Select(attrs={'class': 'form-select'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 978-0743273565'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cover_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief synopsis'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies')
        available = cleaned_data.get('available_copies')
        if total is not None and available is not None and available > total:
            raise forms.ValidationError("Available copies cannot exceed total copies.")
        return cleaned_data


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name', 'member_id', 'email', 'phone', 'joined_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'member_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MEM-101'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 000-0000'}),
            'joined_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('joined_date'):
            self.initial['joined_date'] = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author full name'}),
            'biography': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Biography or background'}),
        }
