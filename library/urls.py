from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('catalog/', views.catalog_view, name='catalog_alt'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/new/', views.book_create_view, name='book_create'),
    path('issue/', views.book_issue_view, name='issue_book'),
    path('issue/<int:book_id>/', views.book_issue_view, name='issue_book_preselected'),
    path('return/', views.book_return_view, name='return_book_select'),
    path('return/<int:record_id>/', views.book_return_view, name='return_book'),
    path('members/', views.member_dashboard_view, name='member_dashboard_default'),
    path('members/<int:member_id>/', views.member_dashboard_view, name='member_dashboard'),
    path('members/directory/', views.members_list_view, name='members_list'),
    path('members/new/', views.member_create_view, name='member_create'),
    path('authors/new/', views.author_create_view, name='author_create'),
    path('calculator/', views.calculator_view, name='calculator'),
    
    # API endpoints
    path('api/fine-calculation/', views.api_fine_calculation, name='api_fine_calculation'),
    path('api/search/', views.api_book_search, name='api_book_search'),
]
