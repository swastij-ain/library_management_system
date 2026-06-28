# Library Management System

A Frappe + ERPNext app for running a library — manage books, members, issue/return books, calculate fines automatically, and post all fine income into proper accounting books with zero manual entry.

Built on **Frappe v14** and **ERPNext v14**.

---

## What this app does (in plain words)

A library has 4 day-to-day jobs:
1. Keep a list of books and how many copies are available
2. Keep a list of members
3. Issue books out and accept them back
4. Charge a small fine if someone returns late

This app does all four, **and** automatically writes the fine into the company's accounting books (no double entry). Reports and dashboards show what's happening at any time.

---

## Modules

### 1. Book Catalog
Where every book in the library is recorded.

- **Book Category** — Fiction, Science, Reference, etc. Just a group name.
- **Book** — Title, Author, ISBN, Category, Rack location, Total copies, Available copies.
  - When a book is issued, `Available Copies` goes down by 1.
  - When it's returned, it goes back up by 1.
  - `Status` flips between **Available** and **Out of Stock** automatically.

### 2. Member Management
Where library members are kept track of.

- **Library Member** — Name, member type (Student / Staff / Public), email, phone, membership start & end dates.
  - When you create a member, the app **auto-creates an ERPNext Customer** for that member behind the scenes. This is what makes accounting integration possible.
  - `Membership Status` (Active / Expired) is updated automatically based on the end date.
  - `Outstanding Fine` shows the total unpaid fine for that member at any moment.

### 3. Book Issue & Return
The lending desk.

- **Book Issue** is a submittable document. You pick the member + the book + the issue date and submit.
  - Due Date fills in automatically using the loan period from Library Settings (default 14 days).
  - The system **blocks** the issue if no copies are available, or if the member's membership has expired.
  - After submit, a **Return Book** button appears on the form.
- Click **Return Book** when the book comes back. The system:
  - Marks return date = today, status = Returned
  - Adds 1 back to the book's available copies
  - **If today is past the due date**, automatically creates a Fine

### 4. Fine Management
Fines are calculated and posted on their own.

- **Fine** (submittable) — Auto-created when a book is returned late. Amount = overdue days × fine per day (from Library Settings).
  - On submit, a **Journal Entry** is posted in the accounting books: `Dr Debtors / Cr Library Fine Income` (against the member's Customer record).
- **Fine Payment** (submittable) — Records the member paying the fine. Pick the fine, pick mode of payment, submit.
  - On submit, a second **Journal Entry** is posted: `Dr Cash / Cr Debtors`. Fine status flips to **Paid**.
- **Waive** — From a submitted Fine, click the **Waive** button + give a reason. The fine status flips to **Waived** and the original accounting entry is cancelled.

### 5. Accounting Integration
This is the "no double entry" promise.

Library staff never touch the accounting module. Every fine raise and every payment automatically becomes a Journal Entry in ERPNext. The standard ERPNext reports — **Accounts Receivable**, **General Ledger**, **Trial Balance**, **Profit & Loss** — all include library activity automatically because the fines post against the member's auto-created Customer.

### 6. Reports
Five built-in reports under the **Library** workspace:

- **Overdue Books** — books currently out past their due date
- **Outstanding Fines Summary** — total unpaid fines per member
- **Fine Collection Report** — raised vs collected vs waived in any date range
- **Member Activity Report** — issues, returns, currently overdue per member
- **Book Utilization Report** — which books are issued most / least

Plus a **Dashboard** with two charts: Fine Collection Trend (line) and Top Books (bar).

### 7. User Roles
Access is by role:

| Role | What they can do |
|---|---|
| Library Administrator | Full access — catalog, members, settings, fines, reports |
| Library Staff | Issue/return books, accept fine payments, view members |
| Accounts Staff | Read-only view of fines, payments, financial reports |
| Management | Read-only view of all reports and dashboards |

---

## End-to-End Flow Example

**Scene:** A student named Alice borrows a book and returns it 3 days late.

1. **Admin creates the member** — A new Library Member "Alice" is created. The system automatically creates a Customer called "Alice" in ERPNext too.
2. **Staff issues the book** — New Book Issue → pick Alice + book "Sapiens" → submit. The book's available copies drops from 3 → 2. Due date is auto-set to today + 14.
3. **3 days after the due date, Alice returns the book** — Staff opens the Book Issue → clicks **Return Book**.
4. **The app does 4 things automatically:**
   - Sets return date = today, status = Returned
   - Available copies back to 3
   - Creates a **Fine** for 3 × ₹10 = ₹30, submitted
   - Posts a **Journal Entry**: Dr Debtors ₹30 (party = Alice's Customer), Cr Library Fine Income ₹30
5. **Alice pays the fine** — Staff opens the Fine → clicks **Record Payment** → confirms ₹30 cash → submits.
6. **The app does 2 things:**
   - Fine status → Paid
   - Posts a second Journal Entry: Dr Cash ₹30, Cr Debtors ₹30
7. **Accounting team sees this in their reports** — Trial Balance shows ₹30 in Library Fine Income. Cash account shows the inflow. Alice's customer ledger shows the receivable raised then settled.

Library staff never touched the Accounts module. Books are accurate. Cash is accounted for.

---

## Setup

### Prerequisites
- Frappe v14 bench with ERPNext v14 installed
- A Company set up in ERPNext (with a Chart of Accounts)
- Three leaf accounts in the CoA:
  - A **Receivable** account (e.g. `Debtors - <abbr>`)
  - A **Library Fine Income** account under Income
  - A **Cash** or **Bank** account

### Install
```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/<your-fork>/library_management_system
bench --site <your-site> install-app library_management_system
```

### Configure Library Settings (one-time)
Search "Library Settings" in the sidebar. Set:
- **Default Loan Period (Days)** — e.g. 14
- **Fine Per Day** — e.g. 10
- **Company** — your ERPNext company
- **Default Receivable Account** — your Debtors leaf account
- **Default Library Fine Income Account** — your income leaf account
- **Default Cash/Bank Account** — your cash leaf account

Save. You're done.

---

## How the scheduler works

Two jobs run **daily** (Frappe's scheduler):

- `mark_overdue` — flips submitted Book Issues to **Overdue** when their due date is past.
- `expire_memberships` — flips members to **Expired** once their membership end date is past.

Make sure the scheduler is on:
```bash
bench --site <your-site> enable-scheduler
```

---

## Email Notifications

An "Library Overdue Reminder" notification is shipped (disabled by default). It fires "Days After due_date" and emails the member. To enable:

1. Configure an Email Domain + Email Account in ERPNext (outgoing SMTP).
2. Open the **Library Overdue Reminder** Notification → toggle **Enabled** ON → Save.

---

## What's not built (yet)

- Partial fine payments (full payment only for now)
- Multi-currency
- Member self-service portal
- Auto-creation of Chart of Accounts entries (user picks existing accounts)

---

## License

MIT