/**
 * LibriVerse - Main JavaScript
 * Handles instant search, dynamic filter, due-date calculator, and fine estimation
 */

document.addEventListener('DOMContentLoaded', function () {
    initInstantSearch();
    initDueDateCalculator();
    initReturnFineCalculator();
    initIssueDateSync();
});

/**
 * Instant Search and Live Filtering for Book Catalog
 */
function initInstantSearch() {
    const searchInput = document.getElementById('instantSearchInput');
    const genreFilter = document.getElementById('genreFilterSelect');
    const availabilityRadios = document.querySelectorAll('input[name="filterAvailability"]');
    const bookCards = document.querySelectorAll('.book-item-card');
    const resultsCountEl = document.getElementById('resultsCount');
    const noResultsEl = document.getElementById('noResultsContainer');

    if (!bookCards.length) return;

    function applyFilters() {
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const selectedGenre = (genreFilter ? genreFilter.value : '').toLowerCase();
        let selectedAvailability = 'all';

        if (availabilityRadios.length) {
            availabilityRadios.forEach(r => {
                if (r.checked) selectedAvailability = r.value;
            });
        }

        let visibleCount = 0;

        bookCards.forEach(card => {
            const title = (card.dataset.title || '').toLowerCase();
            const author = (card.dataset.author || '').toLowerCase();
            const genre = (card.dataset.genre || '').toLowerCase();
            const isbn = (card.dataset.isbn || '').toLowerCase();
            const availableCopies = parseInt(card.dataset.available || '0', 10);

            // Text search match: title, author, genre, or ISBN
            const matchesQuery = !query || 
                title.includes(query) || 
                author.includes(query) || 
                genre.includes(query) || 
                isbn.includes(query);

            // Genre filter match
            const matchesGenre = !selectedGenre || genre === selectedGenre;

            // Availability filter match
            let matchesAvailability = true;
            if (selectedAvailability === 'available') {
                matchesAvailability = availableCopies > 0;
            } else if (selectedAvailability === 'unavailable') {
                matchesAvailability = availableCopies === 0;
            }

            if (matchesQuery && matchesGenre && matchesAvailability) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (resultsCountEl) {
            resultsCountEl.textContent = visibleCount;
        }

        if (noResultsEl) {
            noResultsEl.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
        // Add clear button handler if present
        const clearBtn = document.getElementById('clearSearchBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                applyFilters();
                searchInput.focus();
            });
        }
    }

    if (genreFilter) {
        genreFilter.addEventListener('change', applyFilters);
    }

    if (availabilityRadios.length) {
        availabilityRadios.forEach(radio => radio.addEventListener('change', applyFilters));
    }
}

/**
 * Interactive Due-Date and Fine Calculator Tool
 */
function initDueDateCalculator() {
    const calcIssueDate = document.getElementById('calcIssueDate');
    const calcLoanDays = document.getElementById('calcLoanDays');
    const calcLoanDaysValue = document.getElementById('calcLoanDaysValue');
    const calcReturnDate = document.getElementById('calcReturnDate');
    const calcFineRate = document.getElementById('calcFineRate');

    // Output elements
    const outDueDate = document.getElementById('outDueDate');
    const outStatusBadge = document.getElementById('outStatusBadge');
    const outDaysDifference = document.getElementById('outDaysDifference');
    const outFineAmount = document.getElementById('outFineAmount');
    const outSummaryText = document.getElementById('outSummaryText');

    if (!calcIssueDate || !outDueDate) return;

    function recalculate() {
        const issueDateVal = calcIssueDate.value;
        const loanDays = parseInt(calcLoanDays ? calcLoanDays.value : 14, 10);
        const returnDateVal = calcReturnDate ? calcReturnDate.value : null;
        const fineRate = parseFloat(calcFineRate ? calcFineRate.value : 1.00);

        if (calcLoanDaysValue && calcLoanDays) {
            calcLoanDaysValue.textContent = `${calcLoanDays.value} days`;
        }

        if (!issueDateVal) return;

        const issueDate = new Date(issueDateVal + 'T00:00:00');
        const dueDate = new Date(issueDate);
        dueDate.setDate(dueDate.getDate() + loanDays);

        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        outDueDate.textContent = dueDate.toLocaleDateString('en-US', options);

        if (returnDateVal) {
            const returnDate = new Date(returnDateVal + 'T00:00:00');
            const diffTime = returnDate.getTime() - dueDate.getTime();
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays > 0) {
                // Overdue
                const totalFine = diffDays * fineRate;
                outStatusBadge.className = 'badge bg-danger fs-6 px-3 py-2';
                outStatusBadge.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i> Overdue (${diffDays} days late)`;
                outDaysDifference.textContent = `${diffDays} days past due date`;
                outFineAmount.textContent = `$${totalFine.toFixed(2)}`;
                outFineAmount.className = 'calc-fine-number is-overdue';
                outSummaryText.textContent = `Returned ${diffDays} days after deadline. Overdue fine rate is $${fineRate.toFixed(2)}/day.`;
            } else if (diffDays === 0) {
                // Due today / exactly on time
                outStatusBadge.className = 'badge bg-success fs-6 px-3 py-2';
                outStatusBadge.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Returned Exactly on Due Date`;
                outDaysDifference.textContent = '0 days (On Time)';
                outFineAmount.textContent = '$0.00';
                outFineAmount.className = 'calc-fine-number';
                outSummaryText.textContent = 'Book returned on the exact due date. No overdue fine applied!';
            } else {
                // Returned early
                const earlyDays = Math.abs(diffDays);
                outStatusBadge.className = 'badge bg-success fs-6 px-3 py-2';
                outStatusBadge.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i> Returned Early (+${earlyDays} days early)`;
                outDaysDifference.textContent = `${earlyDays} days before due date`;
                outFineAmount.textContent = '$0.00';
                outFineAmount.className = 'calc-fine-number';
                outSummaryText.textContent = `Returned ${earlyDays} days in advance. No overdue fine applied!`;
            }
        }
    }

    if (calcIssueDate) calcIssueDate.addEventListener('change', recalculate);
    if (calcLoanDays) calcLoanDays.addEventListener('input', recalculate);
    if (calcReturnDate) calcReturnDate.addEventListener('change', recalculate);
    if (calcFineRate) calcFineRate.addEventListener('input', recalculate);

    // Initial calculation
    recalculate();
}

/**
 * Real-Time Fine Calculator on Return Book Workflow
 */
function initReturnFineCalculator() {
    const returnDateInput = document.getElementById('id_return_date');
    const dueDateData = document.getElementById('loanDueDateData');
    const fineRateData = document.getElementById('dailyFineRateData');
    const liveOverdueDays = document.getElementById('liveOverdueDays');
    const liveFineAmount = document.getElementById('liveFineAmount');
    const liveFineBanner = document.getElementById('liveFineBanner');

    if (!returnDateInput || !dueDateData) return;

    const dueDateStr = dueDateData.value;
    const fineRate = parseFloat(fineRateData ? fineRateData.value : '1.00');

    function updateFine() {
        if (!returnDateInput.value) return;
        const returnDate = new Date(returnDateInput.value + 'T00:00:00');
        const dueDate = new Date(dueDateStr + 'T00:00:00');

        const diffTime = returnDate.getTime() - dueDate.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays > 0) {
            const fine = diffDays * fineRate;
            if (liveOverdueDays) liveOverdueDays.textContent = `${diffDays} days`;
            if (liveFineAmount) liveFineAmount.textContent = `$${fine.toFixed(2)}`;
            if (liveFineBanner) {
                liveFineBanner.className = 'alert alert-danger d-flex align-items-center mb-4';
                liveFineBanner.innerHTML = `
                    <i class="bi bi-exclamation-triangle-fill fs-3 me-3 text-danger"></i>
                    <div>
                        <strong class="d-block">Overdue Penalty Notice</strong>
                        This book is <strong>${diffDays} day(s) overdue</strong>. 
                        A fine of <strong>$${fine.toFixed(2)}</strong> ($${fineRate.toFixed(2)}/day) will be registered upon return.
                    </div>
                `;
            }
        } else {
            if (liveOverdueDays) liveOverdueDays.textContent = '0 days (On Time)';
            if (liveFineAmount) liveFineAmount.textContent = '$0.00';
            if (liveFineBanner) {
                liveFineBanner.className = 'alert alert-success d-flex align-items-center mb-4';
                liveFineBanner.innerHTML = `
                    <i class="bi bi-check-circle-fill fs-3 me-3 text-success"></i>
                    <div>
                        <strong class="d-block">On-Time Return</strong>
                        No overdue penalty applies. Thank you for returning this item on schedule!
                    </div>
                `;
            }
        }
    }

    returnDateInput.addEventListener('change', updateFine);
    returnDateInput.addEventListener('input', updateFine);
}

/**
 * Automatically adjust Due Date to Issue Date + 14 Days on Issue Form
 */
function initIssueDateSync() {
    const issueDateInput = document.getElementById('id_issue_date');
    const dueDateInput = document.getElementById('id_due_date');

    if (!issueDateInput || !dueDateInput) return;

    issueDateInput.addEventListener('change', function () {
        if (!issueDateInput.value) return;
        const issue = new Date(issueDateInput.value + 'T00:00:00');
        const due = new Date(issue);
        due.setDate(due.getDate() + 14);

        const yyyy = due.getFullYear();
        const mm = String(due.getMonth() + 1).padStart(2, '0');
        const dd = String(due.getDate()).padStart(2, '0');

        dueDateInput.value = `${yyyy}-${mm}-${dd}`;
    });
}
