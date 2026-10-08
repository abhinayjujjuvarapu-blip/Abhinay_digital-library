"""
Script to create default superuser and seed demonstration data.
Executed during Render build/start and for local setup.
"""
import os
import django
from datetime import timedelta, date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from library.models import Author, Book, Member, CirculationRecord


def create_admin():
    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@library.demo')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"[create_superuser] Superuser created: {username} / {password}")
    else:
        print(f"[create_superuser] Superuser '{username}' already exists.")


def seed_library_data():
    today = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()

    if Book.objects.exists():
        print("[seed_library_data] Database already contains books. Skipping seed.")
        return

    print("[seed_library_data] Seeding initial demonstration data...")

    # 1. Create Authors
    authors_data = [
        ("F. Scott Fitzgerald", "American novelist, whose works illustrate the Jazz Age. Famous for The Great Gatsby."),
        ("George Orwell", "English novelist, essayist, and critic famous for Animal Farm and Nineteen Eighty-Four."),
        ("Jane Austen", "English novelist known primarily for her six major novels, interpreting and critiquing British landed gentry."),
        ("Isaac Asimov", "American writer and professor of biochemistry, best known for science fiction and popular science."),
        ("Harper Lee", "American novelist best known for her 1960 Pulitzer Prize-winning novel To Kill a Mockingbird."),
        ("Robert C. Martin", "Software engineer and author known as 'Uncle Bob', widely recognized for Clean Code and craftsmanship."),
        ("Yuval Noah Harari", "Israeli public intellectual, historian and author of the popular science bestsellers Sapiens and Homo Deus."),
        ("Agatha Christie", "English writer known for her 66 detective novels and 14 short story collections, especially Hercule Poirot."),
    ]

    authors = {}
    for name, bio in authors_data:
        author_obj, _ = Author.objects.get_or_create(name=name, defaults={'biography': bio})
        authors[name] = author_obj

    # 2. Create Books
    books_data = [
        {
            "title": "The Great Gatsby",
            "author": authors["F. Scott Fitzgerald"],
            "isbn": "978-0743273565",
            "genre": "Classic Literature",
            "total_copies": 4,
            "available_copies": 3,
            "cover_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=600&q=80",
            "description": "Set in Jazz Age New York, the novel depicts narrator Nick Carraway's interactions with mysterious millionaire Jay Gatsby."
        },
        {
            "title": "1984",
            "author": authors["George Orwell"],
            "isbn": "978-0451524935",
            "genre": "Fiction",
            "total_copies": 5,
            "available_copies": 3,
            "cover_url": "https://images.unsplash.com/photo-1532012164546-f432f2e37973?auto=format&fit=crop&w=600&q=80",
            "description": "A dystopian social science fiction novel and cautionary tale about totalitarianism, mass surveillance, and repressive regimentation."
        },
        {
            "title": "Pride and Prejudice",
            "author": authors["Jane Austen"],
            "isbn": "978-0141439518",
            "genre": "Classic Literature",
            "total_copies": 3,
            "available_copies": 1,
            "cover_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
            "description": "The romantic story of Elizabeth Bennet and Fitzwilliam Darcy as they overcome the titular pride and prejudice."
        },
        {
            "title": "Foundation",
            "author": authors["Isaac Asimov"],
            "isbn": "978-0553293357",
            "genre": "Fantasy & Sci-Fi",
            "total_copies": 3,
            "available_copies": 2,
            "cover_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80",
            "description": "Hari Seldon uses psychohistory to foresee the imminent collapse of the Galactic Empire and creates the Foundation."
        },
        {
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "author": authors["Robert C. Martin"],
            "isbn": "978-0132350884",
            "genre": "Computer Science",
            "total_copies": 4,
            "available_copies": 2,
            "cover_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=600&q=80",
            "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees. Master software craftsmanship."
        },
        {
            "title": "To Kill a Mockingbird",
            "author": authors["Harper Lee"],
            "isbn": "978-0060935467",
            "genre": "Fiction",
            "total_copies": 3,
            "available_copies": 0,  # Demonstrates fully checked-out book
            "cover_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=600&q=80",
            "description": "Atticus Finch defends Tom Robinson, a Black man falsely accused of raping a young white woman in Maycomb, Alabama."
        },
        {
            "title": "Sapiens: A Brief History of Humankind",
            "author": authors["Yuval Noah Harari"],
            "isbn": "978-0062316097",
            "genre": "History",
            "total_copies": 5,
            "available_copies": 4,
            "cover_url": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=600&q=80",
            "description": "Surveys the history of humankind from the Stone Age up to the twenty-first century, focusing on Homo sapiens."
        },
        {
            "title": "Murder on the Orient Express",
            "author": authors["Agatha Christie"],
            "isbn": "978-0062693662",
            "genre": "Mystery & Thriller",
            "total_copies": 3,
            "available_copies": 2,
            "cover_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80",
            "description": "Belgian detective Hercule Poirot investigates a murder aboard the lavish Orient Express stranded in snowdrift."
        },
    ]

    created_books = {}
    for b in books_data:
        book_obj = Book.objects.create(**b)
        created_books[book_obj.title] = book_obj

    # 3. Create Members
    members_data = [
        ("Alice Walker", "MEM-101", "alice.walker@example.com", "+1 (555) 234-5678", today - timedelta(days=90)),
        ("David Miller", "MEM-102", "david.miller@example.com", "+1 (555) 345-6789", today - timedelta(days=60)),
        ("Elena Rostova", "MEM-103", "elena.rostova@example.com", "+1 (555) 456-7890", today - timedelta(days=45)),
        ("Marcus Chen", "MEM-104", "marcus.chen@example.com", "+1 (555) 567-8901", today - timedelta(days=30)),
    ]

    created_members = {}
    for name, mem_id, email, phone, joined in members_data:
        m = Member.objects.create(name=name, member_id=mem_id, email=email, phone=phone, joined_date=joined)
        created_members[mem_id] = m

    # 4. Create Sample Circulation Records (Active, Overdue, Returned with Fines)
    # Record 1: Alice - Active Loan (Not Overdue, 8 days remaining)
    CirculationRecord.objects.create(
        book=created_books["The Great Gatsby"],
        member=created_members["MEM-101"],
        issue_date=today - timedelta(days=6),
        due_date=today + timedelta(days=8),
        returned=False,
    )

    # Record 2: Alice - Overdue Loan! (5 days overdue, fine accrued $5.00)
    CirculationRecord.objects.create(
        book=created_books["Pride and Prejudice"],
        member=created_members["MEM-101"],
        issue_date=today - timedelta(days=19),
        due_date=today - timedelta(days=5),
        returned=False,
    )

    # Record 3: David - Active Loan (Due soon, 2 days remaining)
    CirculationRecord.objects.create(
        book=created_books["1984"],
        member=created_members["MEM-102"],
        issue_date=today - timedelta(days=12),
        due_date=today + timedelta(days=2),
        returned=False,
    )

    # Record 4: David - Severely Overdue Loan! (12 days overdue, fine accrued $12.00)
    CirculationRecord.objects.create(
        book=created_books["Clean Code: A Handbook of Agile Software Craftsmanship"],
        member=created_members["MEM-102"],
        issue_date=today - timedelta(days=26),
        due_date=today - timedelta(days=12),
        returned=False,
    )

    # Record 5: Elena - Fully Checked Out Book Loan (Active)
    CirculationRecord.objects.create(
        book=created_books["To Kill a Mockingbird"],
        member=created_members["MEM-103"],
        issue_date=today - timedelta(days=5),
        due_date=today + timedelta(days=9),
        returned=False,
    )

    # Record 6: Elena - Completed Return with Overdue Fine Paid ($4.00)
    CirculationRecord.objects.create(
        book=created_books["Foundation"],
        member=created_members["MEM-103"],
        issue_date=today - timedelta(days=30),
        due_date=today - timedelta(days=16),
        return_date=today - timedelta(days=12),
        fine_amount=Decimal('4.00'),
        returned=True,
    )

    # Record 7: Marcus - Completed Return On Time ($0.00 fine)
    CirculationRecord.objects.create(
        book=created_books["Sapiens: A Brief History of Humankind"],
        member=created_members["MEM-104"],
        issue_date=today - timedelta(days=20),
        due_date=today - timedelta(days=6),
        return_date=today - timedelta(days=8),
        fine_amount=Decimal('0.00'),
        returned=True,
    )

    # Record 8: Marcus - Active Loan (1984)
    CirculationRecord.objects.create(
        book=created_books["1984"],
        member=created_members["MEM-104"],
        issue_date=today - timedelta(days=3),
        due_date=today + timedelta(days=11),
        returned=False,
    )

    print("[seed_library_data] Sample data successfully seeded!")


if __name__ == '__main__':
    create_admin()
    seed_library_data()
