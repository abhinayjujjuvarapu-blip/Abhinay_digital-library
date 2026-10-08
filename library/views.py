from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from datetime import timedelta, date
from decimal import Decimal

from .models import Author, Book, Member, CirculationRecord, DAILY_FINE_RATE, DEFAULT_LOAN_DAYS
from .forms import BookIssueForm, BookReturnForm, BookForm, MemberForm, AuthorForm


def catalog_view(request):
    """Book catalog with instant search, genre filter, and availability status."""
    query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '').strip()
    selected_availability = request.GET.get('availability', '').strip()

    books = Book.objects.select_related('author').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(genre__icontains=query) |
            Q(isbn__icontains=query)
        )

    if selected_genre:
        books = books.filter(genre=selected_genre)

    if selected_availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif selected_availability == 'unavailable':
        books = books.filter(available_copies=0)

    # Statistics for dashboard summary cards
    total_titles = Book.objects.count()
    total_copies_sum = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies_sum = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
    active_loans_count = CirculationRecord.objects.filter(returned=False).count()
    
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    overdue_loans_count = CirculationRecord.objects.filter(returned=False, due_date__lt=today).count()
    total_members_count = Member.objects.count()

    genres = [choice[0] for choice in Book.GENRE_CHOICES]

    context = {
        'books': books,
        'genres': genres,
        'query': query,
        'selected_genre': selected_genre,
        'selected_availability': selected_availability,
        'total_titles': total_titles,
        'total_copies_sum': total_copies_sum,
        'available_copies_sum': available_copies_sum,
        'active_loans_count': active_loans_count,
        'overdue_loans_count': overdue_loans_count,
        'total_members_count': total_members_count,
        'today': today,
    }
    return render(request, 'library/catalog.html', context)


def book_detail_view(request, pk):
    """Detailed view for a single book including copy availability and circulation history."""
    book = get_object_or_404(Book.objects.select_related('author'), pk=pk)
    records = book.circulation_records.select_related('member').order_by('-issue_date')[:10]
    
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()

    context = {
        'book': book,
        'records': records,
        'today': today,
    }
    return render(request, 'library/book_detail.html', context)


def book_issue_view(request, book_id=None):
    """Book issue workflow: validates availability, creates loan record, decrements copies."""
    preselected_book = None
    if book_id:
        preselected_book = get_object_or_404(Book, pk=book_id)
        if preselected_book.available_copies <= 0:
            messages.error(
                request,
                f"Cannot issue '{preselected_book.title}': No copies are currently available."
            )
            return redirect('catalog')

    if request.method == 'POST':
        form = BookIssueForm(request.POST)
        if form.is_valid():
            circulation = form.save(commit=False)
            target_book = circulation.book

            # Business logic validation: Ensure copies are available
            if target_book.available_copies <= 0:
                messages.error(
                    request,
                    f"Cannot issue '{target_book.title}': Available copies are zero."
                )
                return render(request, 'library/issue_book.html', {'form': form, 'preselected_book': preselected_book})

            # Business logic: Set default due date to 14 days after issue if not set
            if not circulation.due_date:
                circulation.due_date = circulation.issue_date + timedelta(days=DEFAULT_LOAN_DAYS)

            circulation.returned = False
            circulation.fine_amount = Decimal('0.00')
            circulation.save()

            # Business logic: Decrement available copies
            target_book.available_copies = max(0, target_book.available_copies - 1)
            target_book.save()

            messages.success(
                request,
                f"Success! '{target_book.title}' was issued to {circulation.member.name}. "
                f"Due date is {circulation.due_date.strftime('%B %d, %Y')}."
            )
            return redirect('member_dashboard', member_id=circulation.member.id)
    else:
        initial_data = {}
        if preselected_book:
            initial_data['book'] = preselected_book
        form = BookIssueForm(initial=initial_data, book_id=book_id)

    context = {
        'form': form,
        'preselected_book': preselected_book,
        'default_loan_days': DEFAULT_LOAN_DAYS,
    }
    return render(request, 'library/issue_book.html', context)


def book_return_view(request, record_id=None):
    """Book return workflow: calculates overdue fine, increments copies, marks returned."""
    if record_id:
        record = get_object_or_404(CirculationRecord.objects.select_related('book', 'member'), pk=record_id)
    else:
        # If no record_id in URL, user selected from dropdown or list
        record_id = request.GET.get('record_id') or request.POST.get('record_id')
        if not record_id:
            active_records = CirculationRecord.objects.filter(returned=False).select_related('book', 'member')
            return render(request, 'library/return_selector.html', {'active_records': active_records})
        record = get_object_or_404(CirculationRecord.objects.select_related('book', 'member'), pk=record_id)

    if record.returned:
        messages.info(request, f"This loan for '{record.book.title}' was already returned on {record.return_date}.")
        return redirect('member_dashboard', member_id=record.member.id)

    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()

    if request.method == 'POST':
        form = BookReturnForm(request.POST)
        if form.is_valid():
            return_date = form.cleaned_data['return_date']

            # Business logic: Calculate final overdue fine during return
            if return_date > record.due_date:
                days_overdue = (return_date - record.due_date).days
                fine = Decimal(str(days_overdue)) * DAILY_FINE_RATE
            else:
                days_overdue = 0
                fine = Decimal('0.00')

            record.return_date = return_date
            record.fine_amount = fine
            record.returned = True
            record.save()

            # Business logic: Increase available copies
            book = record.book
            book.available_copies = min(book.total_copies, book.available_copies + 1)
            book.save()

            if fine > Decimal('0.00'):
                messages.warning(
                    request,
                    f"Book returned! '{book.title}' was {days_overdue} day(s) overdue. "
                    f"Fine assessed: ${fine:.2f} (Rate: ${DAILY_FINE_RATE}/day)."
                )
            else:
                messages.success(
                    request,
                    f"Book returned successfully on time! No overdue fine for '{book.title}'."
                )

            return redirect('member_dashboard', member_id=record.member.id)
    else:
        form = BookReturnForm(initial={'return_date': today})

    # Pre-calculate estimated fine for current preview
    days_overdue = max(0, (today - record.due_date).days)
    estimated_fine = Decimal(str(days_overdue)) * DAILY_FINE_RATE

    context = {
        'record': record,
        'form': form,
        'today': today,
        'days_overdue': days_overdue,
        'estimated_fine': estimated_fine,
        'daily_fine_rate': DAILY_FINE_RATE,
    }
    return render(request, 'library/return_book.html', context)


def member_dashboard_view(request, member_id=None):
    """Member dashboard showing borrowed books, due dates, overdue alerts, and borrowing history."""
    members = Member.objects.all().order_by('name')
    selected_member = None

    if member_id:
        selected_member = get_object_or_404(Member, pk=member_id)
    elif members.exists():
        selected_member = members.first()

    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    active_loans = []
    past_loans = []
    total_fines = Decimal('0.00')
    overdue_count = 0

    if selected_member:
        active_loans = selected_member.circulation_records.filter(returned=False).select_related('book').order_by('due_date')
        past_loans = selected_member.circulation_records.filter(returned=True).select_related('book').order_by('-return_date')
        
        for loan in active_loans:
            if loan.due_date < today:
                overdue_count += 1
                days = (today - loan.due_date).days
                loan.calc_overdue_days = days
                loan.calc_fine = Decimal(str(days)) * DAILY_FINE_RATE
            else:
                loan.calc_overdue_days = 0
                loan.calc_fine = Decimal('0.00')
                loan.days_remaining = (loan.due_date - today).days

        total_fines = sum((l.fine_amount for l in past_loans), Decimal('0.00')) + \
                      sum((getattr(l, 'calc_fine', Decimal('0.00')) for l in active_loans), Decimal('0.00'))

    context = {
        'members': members,
        'member': selected_member,
        'active_loans': active_loans,
        'past_loans': past_loans,
        'total_fines': total_fines,
        'overdue_count': overdue_count,
        'today': today,
        'daily_fine_rate': DAILY_FINE_RATE,
    }
    return render(request, 'library/member_dashboard.html', context)


def members_list_view(request):
    """List of all registered members with quick status summaries."""
    query = request.GET.get('q', '').strip()
    members = Member.objects.annotate(
        total_borrowed=Count('circulation_records'),
    ).order_by('name')

    if query:
        members = members.filter(
            Q(name__icontains=query) |
            Q(member_id__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    context = {
        'members': members,
        'query': query,
    }
    return render(request, 'library/members_list.html', context)


def member_create_view(request):
    """Register a new library member."""
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.name}' ({member.member_id}) registered successfully!")
            return redirect('member_dashboard', member_id=member.id)
    else:
        form = MemberForm()

    return render(request, 'library/member_form.html', {'form': form, 'title': 'Register New Member'})


def book_create_view(request):
    """Add a new book title to the catalog."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f"Book '{book.title}' added to catalog successfully!")
            return redirect('book_detail', pk=book.id)
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {'form': form, 'title': 'Add New Book'})


def author_create_view(request):
    """Add a new author."""
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f"Author '{author.name}' added successfully!")
            return redirect('catalog')
    else:
        form = AuthorForm()

    return render(request, 'library/author_form.html', {'form': form, 'title': 'Add New Author'})


def calculator_view(request):
    """Interactive Due-Date and Fine Calculator tool."""
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
    default_due = today + timedelta(days=DEFAULT_LOAN_DAYS)

    context = {
        'today': today,
        'default_due': default_due,
        'default_loan_days': DEFAULT_LOAN_DAYS,
        'daily_fine_rate': DAILY_FINE_RATE,
    }
    return render(request, 'library/calculator.html', context)


# -------------------------------------------------------------
# REST / JSON Helper Endpoints for JavaScript Interactivity
# -------------------------------------------------------------

def api_fine_calculation(request):
    """API endpoint to calculate overdue fine based on loan dates."""
    try:
        due_date_str = request.GET.get('due_date')
        return_date_str = request.GET.get('return_date')
        daily_rate_str = request.GET.get('rate', str(DAILY_FINE_RATE))

        if not due_date_str or not return_date_str:
            return JsonResponse({'error': 'Missing due_date or return_date parameter'}, status=400)

        due_date = date.fromisoformat(due_date_str)
        return_date = date.fromisoformat(return_date_str)
        daily_rate = Decimal(daily_rate_str)

        if return_date > due_date:
            days_overdue = (return_date - due_date).days
            fine = float(Decimal(str(days_overdue)) * daily_rate)
            is_overdue = True
        else:
            days_overdue = 0
            fine = 0.00
            is_overdue = False

        return JsonResponse({
            'due_date': due_date.isoformat(),
            'return_date': return_date.isoformat(),
            'days_overdue': days_overdue,
            'is_overdue': is_overdue,
            'fine_amount': fine,
            'formatted_fine': f"${fine:.2f}"
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_book_search(request):
    """API endpoint for live instant search JSON results."""
    query = request.GET.get('q', '').strip()
    books = Book.objects.select_related('author').all()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(genre__icontains=query) |
            Q(isbn__icontains=query)
        )
    data = [{
        'id': b.id,
        'title': b.title,
        'author': b.author.name,
        'isbn': b.isbn,
        'genre': b.genre,
        'available_copies': b.available_copies,
        'total_copies': b.total_copies,
        'is_available': b.is_available,
        'cover_url': b.cover_url,
    } for b in books[:20]]
    return JsonResponse({'results': data})
