from django.contrib import admin
from .models import Author, Book, Member, CirculationRecord


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'book_count')
    search_fields = ('name', 'biography')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'genre', 'total_copies', 'available_copies')
    list_filter = ('genre', 'author')
    search_fields = ('title', 'isbn', 'author__name')
    readonly_fields = ()


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_id', 'email', 'phone', 'joined_date', 'active_loans_count')
    search_fields = ('name', 'member_id', 'email', 'phone')
    list_filter = ('joined_date',)


@admin.register(CirculationRecord)
class CirculationRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'issue_date', 'due_date', 'return_date', 'fine_amount', 'returned', 'is_overdue')
    list_filter = ('returned', 'issue_date', 'due_date')
    search_fields = ('book__title', 'member__name', 'member__member_id')
    readonly_fields = ('fine_amount',)
