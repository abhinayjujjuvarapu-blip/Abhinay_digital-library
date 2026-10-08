from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from .models import Author, Book, Member, CirculationRecord, DAILY_FINE_RATE, DEFAULT_LOAN_DAYS


class DigitalLibraryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()

        # Create Author
        self.author = Author.objects.create(
            name="Arthur Conan Doyle",
            biography="Creator of Sherlock Holmes."
        )

        # Create Books
        self.book_available = Book.objects.create(
            title="A Study in Scarlet",
            author=self.author,
            isbn="978-0141040370",
            genre="Mystery & Thriller",
            total_copies=3,
            available_copies=2,
            cover_url="https://example.com/cover.jpg"
        )

        self.book_zero_copies = Book.objects.create(
            title="The Sign of the Four",
            author=self.author,
            isbn="978-0141040387",
            genre="Mystery & Thriller",
            total_copies=2,
            available_copies=0,
            cover_url="https://example.com/cover2.jpg"
        )

        # Create Member
        self.member = Member.objects.create(
            name="John Watson",
            member_id="MEM-701",
            email="watson@bakerstreet.com",
            phone="+44 20 7946 0919",
            joined_date=self.today - timedelta(days=30)
        )

    def test_book_model_properties(self):
        self.assertTrue(self.book_available.is_available)
        self.assertEqual(self.book_available.borrowed_copies, 1)

        self.assertFalse(self.book_zero_copies.is_available)
        self.assertEqual(self.book_zero_copies.borrowed_copies, 2)

    def test_issue_workflow_business_logic(self):
        # 1. Issue available book
        issue_date = self.today
        expected_due_date = issue_date + timedelta(days=DEFAULT_LOAN_DAYS)

        response = self.client.post(reverse('issue_book'), {
            'member': self.member.id,
            'book': self.book_available.id,
            'issue_date': issue_date.isoformat(),
            'due_date': expected_due_date.isoformat(),
        })

        self.assertEqual(response.status_code, 302)

        # Verify available copies decremented from 2 to 1
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 1)

        # Verify circulation record created
        record = CirculationRecord.objects.get(book=self.book_available, member=self.member, returned=False)
        self.assertEqual(record.due_date, expected_due_date)
        self.assertFalse(record.returned)

    def test_cannot_issue_when_available_copies_zero(self):
        # Attempt to issue book with 0 available copies
        response = self.client.post(reverse('issue_book'), {
            'member': self.member.id,
            'book': self.book_zero_copies.id,
            'issue_date': self.today.isoformat(),
            'due_date': (self.today + timedelta(days=14)).isoformat(),
        })

        # Form should reject because book queryset filters out 0 copies or clean() raises error
        self.assertEqual(self.book_zero_copies.available_copies, 0)
        self.assertFalse(CirculationRecord.objects.filter(book=self.book_zero_copies, member=self.member).exists())

    def test_return_workflow_on_time_zero_fine(self):
        # Create active loan
        loan = CirculationRecord.objects.create(
            book=self.book_available,
            member=self.member,
            issue_date=self.today - timedelta(days=10),
            due_date=self.today + timedelta(days=4),
            returned=False
        )
        initial_available = self.book_available.available_copies

        # Return on time (today <= due_date)
        response = self.client.post(reverse('return_book', kwargs={'record_id': loan.id}), {
            'return_date': self.today.isoformat(),
        })
        self.assertEqual(response.status_code, 302)

        loan.refresh_from_db()
        self.assertTrue(loan.returned)
        self.assertEqual(loan.return_date, self.today)
        self.assertEqual(loan.fine_amount, Decimal('0.00'))

        # Verify available copies incremented
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, initial_available + 1)

    def test_return_workflow_overdue_fine_calculation(self):
        # Loan issued 20 days ago, due 6 days ago
        due_date = self.today - timedelta(days=6)
        loan = CirculationRecord.objects.create(
            book=self.book_available,
            member=self.member,
            issue_date=self.today - timedelta(days=20),
            due_date=due_date,
            returned=False
        )
        initial_available = self.book_available.available_copies

        # Return today (6 days overdue)
        response = self.client.post(reverse('return_book', kwargs={'record_id': loan.id}), {
            'return_date': self.today.isoformat(),
        })
        self.assertEqual(response.status_code, 302)

        loan.refresh_from_db()
        self.assertTrue(loan.returned)
        self.assertEqual(loan.return_date, self.today)
        expected_fine = Decimal('6') * DAILY_FINE_RATE
        self.assertEqual(loan.fine_amount, expected_fine)

        # Verify copies incremented
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, initial_available + 1)

    def test_all_pages_render_successfully(self):
        # Catalog
        res_cat = self.client.get(reverse('catalog'))
        self.assertEqual(res_cat.status_code, 200)
        self.assertContains(res_cat, "A Study in Scarlet")

        # Book detail
        res_detail = self.client.get(reverse('book_detail', kwargs={'pk': self.book_available.id}))
        self.assertEqual(res_detail.status_code, 200)

        # Members list & dashboard
        res_members = self.client.get(reverse('members_list'))
        self.assertEqual(res_members.status_code, 200)
        res_dash = self.client.get(reverse('member_dashboard', kwargs={'member_id': self.member.id}))
        self.assertEqual(res_dash.status_code, 200)

        # Calculator
        res_calc = self.client.get(reverse('calculator'))
        self.assertEqual(res_calc.status_code, 200)
        self.assertContains(res_calc, "Interactive Due-Date & Fine Calculator")

    def test_api_fine_calculation_endpoint(self):
        due = self.today - timedelta(days=5)
        ret = self.today
        res = self.client.get(reverse('api_fine_calculation'), {
            'due_date': due.isoformat(),
            'return_date': ret.isoformat(),
            'rate': '1.00',
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['days_overdue'], 5)
        self.assertEqual(data['fine_amount'], 5.0)
        self.assertTrue(data['is_overdue'])
