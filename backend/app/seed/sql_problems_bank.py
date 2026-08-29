"""Original SQL practice problem bank — 30 challenges for Build 4 seed."""

SQL_TOPICS = [
    ("sql-fundamentals", "SQL Fundamentals"),
    ("aggregations", "Aggregations"),
    ("joins", "Joins"),
    ("subqueries", "Subqueries"),
    ("cte", "CTE"),
    ("window-functions", "Window Functions"),
    ("conditional-logic", "Conditional Logic"),
    ("date-functions", "Date Functions"),
    ("string-functions", "String Functions"),
    ("advanced-sql", "Advanced SQL"),
]

SQL_PROBLEM_BANK: list[dict] = [
    # -------------------------------------------------------------------------
    # EASY (12)
    # -------------------------------------------------------------------------
    {
        "slug": "active-catalog-items",
        "title": "Active Catalog Items",
        "description": (
            "NovaMart keeps a lightweight product catalog for its online storefront. "
            "Merchandising wants a quick list of items currently shown to shoppers.\n\n"
            "Use the products table to return only active listings, sorted so the most "
            "expensive active items appear first."
        ),
        "difficulty": "easy",
        "topic_slug": "sql-fundamentals",
        "tags": ["select", "where", "order-by"],
        "role_tags": ["Data Analyst", "Backend Developer", "Business Analyst"],
        "scenario": "Ecommerce catalog hygiene for the storefront.",
        "task_description": (
            "Return product_name and price for rows where is_active is true, "
            "ordered by price descending."
        ),
        "expected_columns": ["product_name", "price"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT product_name, price\n"
            "FROM products\n"
            "WHERE is_active = TRUE\n"
            "ORDER BY price DESC"
        ),
        "solution_explanation": (
            "Filter with WHERE on the boolean flag, project the two requested columns, "
            "and sort with ORDER BY price DESC."
        ),
        "alternate_solution": None,
        "key_concepts": ["SELECT", "WHERE", "ORDER BY"],
        "hints": [
            "Boolean columns can be compared with TRUE/FALSE.",
            "ORDER BY comes after WHERE.",
        ],
        "sample_expected_rows": [["Ultrawide Monitor", 249], ["Standing Desk", 199]],
        "estimated_time_seconds": 240,
        "tables": [
            {
                "table_name": "products",
                "display_name": "Products",
                "description": "Storefront catalog rows",
                "sort_order": 0,
                "columns": [
                    {"column_name": "product_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "product_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "price", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                    {"column_name": "is_active", "data_type": "BOOLEAN", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"product_id": 1, "product_name": "Desk Lamp", "price": 30, "is_active": True},
                    {"product_id": 2, "product_name": "Standing Desk", "price": 199, "is_active": True},
                    {"product_id": 3, "product_name": "Office Chair", "price": 89, "is_active": False},
                    {"product_id": 4, "product_name": "Ultrawide Monitor", "price": 249, "is_active": True},
                    {"product_id": 5, "product_name": "USB Hub", "price": 25, "is_active": False},
                ],
            }
        ],
        "expected_rows": [
            ["Ultrawide Monitor", 249],
            ["Standing Desk", 199],
            ["Desk Lamp", 30],
        ],
    },
    {
        "slug": "high-priority-open-tickets",
        "title": "High Priority Open Tickets",
        "description": (
            "HelpDesk Pro tracks customer support tickets for a SaaS billing product. "
            "Ops needs a short queue of issues that must be worked first.\n\n"
            "Pull open tickets marked high priority, oldest first by ticket_id."
        ),
        "difficulty": "easy",
        "topic_slug": "sql-fundamentals",
        "tags": ["filtering", "support"],
        "role_tags": ["Business Analyst", "Data Analyst", "Backend Developer"],
        "scenario": "Support queue triage for a SaaS helpdesk.",
        "task_description": (
            "Return ticket_id, subject, and priority for tickets with status 'open' "
            "and priority 'high', ordered by ticket_id ascending."
        ),
        "expected_columns": ["ticket_id", "subject", "priority"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT ticket_id, subject, priority\n"
            "FROM tickets\n"
            "WHERE status = 'open' AND priority = 'high'\n"
            "ORDER BY ticket_id"
        ),
        "solution_explanation": "Combine two equality filters with AND and sort by ticket_id.",
        "alternate_solution": None,
        "key_concepts": ["WHERE", "AND", "ORDER BY"],
        "hints": [
            "Both status and priority must match.",
            "Ascending order is the default for ORDER BY.",
        ],
        "sample_expected_rows": [[101, "Payment failed twice", "high"]],
        "estimated_time_seconds": 240,
        "tables": [
            {
                "table_name": "tickets",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "ticket_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "subject", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "priority", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                    {"column_name": "status", "data_type": "TEXT", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"ticket_id": 101, "subject": "Payment failed twice", "priority": "high", "status": "open"},
                    {"ticket_id": 102, "subject": "Change email", "priority": "low", "status": "open"},
                    {"ticket_id": 103, "subject": "API timeout", "priority": "high", "status": "resolved"},
                    {"ticket_id": 104, "subject": "Invoice PDF missing", "priority": "high", "status": "open"},
                    {"ticket_id": 105, "subject": "Feature request", "priority": "medium", "status": "open"},
                ],
            }
        ],
        "expected_rows": [
            [101, "Payment failed twice", "high"],
            [104, "Invoice PDF missing", "high"],
        ],
    },
    {
        "slug": "engineering-headcount-roster",
        "title": "Engineering Headcount Roster",
        "description": (
            "BrightHire HR maintains an employee roster across departments. Finance is "
            "preparing a headcount snapshot for Engineering only.\n\n"
            "List currently employed engineers ordered by last name."
        ),
        "difficulty": "easy",
        "topic_slug": "sql-fundamentals",
        "tags": ["hr", "filter"],
        "role_tags": ["Business Analyst", "Data Analyst", "BI Developer"],
        "scenario": "HR roster filter for Engineering staff.",
        "task_description": (
            "Return employee_id, first_name, and last_name for employees in department "
            "'Engineering' with is_active true, ordered by last_name ascending."
        ),
        "expected_columns": ["employee_id", "first_name", "last_name"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT employee_id, first_name, last_name\n"
            "FROM employees\n"
            "WHERE department = 'Engineering' AND is_active = TRUE\n"
            "ORDER BY last_name"
        ),
        "solution_explanation": "Filter department and active flag, then sort alphabetically by last_name.",
        "alternate_solution": None,
        "key_concepts": ["SELECT", "WHERE", "ORDER BY"],
        "hints": ["Department values are case-sensitive strings.", "Sort on last_name only."],
        "sample_expected_rows": [[3, "Maya", "Iyer"]],
        "estimated_time_seconds": 240,
        "tables": [
            {
                "table_name": "employees",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "employee_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "first_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "last_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                    {"column_name": "department", "data_type": "TEXT", "is_nullable": False, "sort_order": 3},
                    {"column_name": "is_active", "data_type": "BOOLEAN", "is_nullable": False, "sort_order": 4},
                ],
                "rows": [
                    {"employee_id": 1, "first_name": "Arjun", "last_name": "Mehta", "department": "Sales", "is_active": True},
                    {"employee_id": 2, "first_name": "Priya", "last_name": "Shah", "department": "Engineering", "is_active": False},
                    {"employee_id": 3, "first_name": "Maya", "last_name": "Iyer", "department": "Engineering", "is_active": True},
                    {"employee_id": 4, "first_name": "Dev", "last_name": "Nair", "department": "Engineering", "is_active": True},
                    {"employee_id": 5, "first_name": "Leah", "last_name": "Chen", "department": "Marketing", "is_active": True},
                ],
            }
        ],
        "expected_rows": [
            [3, "Maya", "Iyer"],
            [4, "Dev", "Nair"],
        ],
    },
    {
        "slug": "category-sku-counts",
        "title": "Category SKU Counts",
        "description": (
            "ShelfWise inventory analysts want a quick rollup of how many SKUs sit in "
            "each product category before a replenishment meeting.\n\n"
            "Count products per category and sort by the highest counts first."
        ),
        "difficulty": "easy",
        "topic_slug": "aggregations",
        "tags": ["group-by", "count"],
        "role_tags": ["Data Analyst", "BI Developer", "Business Analyst"],
        "scenario": "Inventory category rollup for replenishment planning.",
        "task_description": (
            "Return category and sku_count (COUNT of product_id) grouped by category, "
            "ordered by sku_count descending, then category ascending."
        ),
        "expected_columns": ["category", "sku_count"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT category, COUNT(product_id) AS sku_count\n"
            "FROM inventory\n"
            "GROUP BY category\n"
            "ORDER BY sku_count DESC, category"
        ),
        "solution_explanation": "GROUP BY category with COUNT, then ORDER BY the aggregate.",
        "alternate_solution": None,
        "key_concepts": ["GROUP BY", "COUNT", "ORDER BY"],
        "hints": ["Alias the count as sku_count.", "Break ties alphabetically by category."],
        "sample_expected_rows": [["Apparel", 3]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "inventory",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "product_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "sku", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "category", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"product_id": 1, "sku": "APP-01", "category": "Apparel"},
                    {"product_id": 2, "sku": "APP-02", "category": "Apparel"},
                    {"product_id": 3, "sku": "APP-03", "category": "Apparel"},
                    {"product_id": 4, "sku": "HOM-01", "category": "Home"},
                    {"product_id": 5, "sku": "HOM-02", "category": "Home"},
                    {"product_id": 6, "sku": "ELE-01", "category": "Electronics"},
                ],
            }
        ],
        "expected_rows": [
            ["Apparel", 3],
            ["Home", 2],
            ["Electronics", 1],
        ],
    },
    {
        "slug": "branch-deposit-totals",
        "title": "Branch Deposit Totals",
        "description": (
            "RiverBank operations reviews daily cash deposits by branch. Leadership "
            "wants the total deposited amount for each branch code.\n\n"
            "Sum deposit amounts per branch and sort by total descending."
        ),
        "difficulty": "easy",
        "topic_slug": "aggregations",
        "tags": ["sum", "banking"],
        "role_tags": ["Data Analyst", "BI Developer", "Business Analyst"],
        "scenario": "Banking branch deposit rollup.",
        "task_description": (
            "Return branch_code and total_deposits (SUM of amount) ordered by "
            "total_deposits descending."
        ),
        "expected_columns": ["branch_code", "total_deposits"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT branch_code, SUM(amount) AS total_deposits\n"
            "FROM deposits\n"
            "GROUP BY branch_code\n"
            "ORDER BY total_deposits DESC"
        ),
        "solution_explanation": "Aggregate with SUM and GROUP BY branch_code.",
        "alternate_solution": None,
        "key_concepts": ["SUM", "GROUP BY"],
        "hints": ["One row per branch_code.", "Use SUM(amount) aliased as total_deposits."],
        "sample_expected_rows": [["BLR-01", 15000]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "deposits",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "deposit_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "branch_code", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"deposit_id": 1, "branch_code": "BLR-01", "amount": 5000},
                    {"deposit_id": 2, "branch_code": "BLR-01", "amount": 10000},
                    {"deposit_id": 3, "branch_code": "HYD-02", "amount": 8000},
                    {"deposit_id": 4, "branch_code": "MUM-03", "amount": 12000},
                    {"deposit_id": 5, "branch_code": "HYD-02", "amount": 2000},
                ],
            }
        ],
        "expected_rows": [
            ["BLR-01", 15000],
            ["MUM-03", 12000],
            ["HYD-02", 10000],
        ],
    },
    {
        "slug": "customer-order-pairs",
        "title": "Customer Order Pairs",
        "description": (
            "Cartly ecommerce analysts need a simple joined list of customers and the "
            "orders they placed for a stakeholder walkthrough.\n\n"
            "Join customers to orders and return one row per order."
        ),
        "difficulty": "easy",
        "topic_slug": "joins",
        "tags": ["inner-join", "ecommerce"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Backend Developer"],
        "scenario": "Ecommerce customer-to-order join for reporting.",
        "task_description": (
            "Return customer_name, order_id, and order_total for every order by joining "
            "customers and orders on customer_id. Order by order_id ascending."
        ),
        "expected_columns": ["customer_name", "order_id", "order_total"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT c.customer_name, o.order_id, o.order_total\n"
            "FROM customers c\n"
            "INNER JOIN orders o ON c.customer_id = o.customer_id\n"
            "ORDER BY o.order_id"
        ),
        "solution_explanation": "INNER JOIN customers to orders on customer_id.",
        "alternate_solution": None,
        "key_concepts": ["INNER JOIN", "table aliases"],
        "hints": ["Match on customer_id.", "Customers without orders should not appear."],
        "sample_expected_rows": [["Neha Kapoor", 501, 120]],
        "estimated_time_seconds": 360,
        "tables": [
            {
                "table_name": "customers",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"customer_id": 1, "customer_name": "Neha Kapoor"},
                    {"customer_id": 2, "customer_name": "Rohan Das"},
                    {"customer_id": 3, "customer_name": "Aisha Khan"},
                ],
            },
            {
                "table_name": "orders",
                "display_name": None,
                "description": None,
                "sort_order": 1,
                "columns": [
                    {"column_name": "order_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "order_total", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"order_id": 501, "customer_id": 1, "order_total": 120},
                    {"order_id": 502, "customer_id": 2, "order_total": 80},
                    {"order_id": 503, "customer_id": 1, "order_total": 45},
                    {"order_id": 504, "customer_id": 3, "order_total": 200},
                ],
            },
        ],
        "expected_rows": [
            ["Neha Kapoor", 501, 120],
            ["Rohan Das", 502, 80],
            ["Neha Kapoor", 503, 45],
            ["Aisha Khan", 504, 200],
        ],
    },
    {
        "slug": "signup-email-domains",
        "title": "Signup Email Domains",
        "description": (
            "EduPath marketing wants to understand which email domains dominate new "
            "student signups for campus outreach targeting.\n\n"
            "Extract the domain portion of each email and list distinct domains sorted alphabetically."
        ),
        "difficulty": "easy",
        "topic_slug": "string-functions",
        "tags": ["split_part", "distinct"],
        "role_tags": ["Data Analyst", "Business Analyst", "Analytics Engineer"],
        "scenario": "Education marketing domain extraction from signup emails.",
        "task_description": (
            "Return distinct email_domain values extracted with SPLIT_PART(email, '@', 2), "
            "ordered alphabetically."
        ),
        "expected_columns": ["email_domain"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT DISTINCT SPLIT_PART(email, '@', 2) AS email_domain\n"
            "FROM signups\n"
            "ORDER BY email_domain"
        ),
        "solution_explanation": "SPLIT_PART splits on '@' and returns the domain; DISTINCT removes duplicates.",
        "alternate_solution": None,
        "key_concepts": ["SPLIT_PART", "DISTINCT"],
        "hints": ["The domain is the second part after '@'.", "Alias the expression as email_domain."],
        "sample_expected_rows": [["campus.edu"]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "signups",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "signup_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "student_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "email", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"signup_id": 1, "student_name": "Anika", "email": "anika@campus.edu"},
                    {"signup_id": 2, "student_name": "Omar", "email": "omar@gmail.com"},
                    {"signup_id": 3, "student_name": "Sara", "email": "sara@campus.edu"},
                    {"signup_id": 4, "student_name": "Leo", "email": "leo@outlook.com"},
                    {"signup_id": 5, "student_name": "Mia", "email": "mia@gmail.com"},
                ],
            }
        ],
        "expected_rows": [
            ["campus.edu"],
            ["gmail.com"],
            ["outlook.com"],
        ],
    },
    {
        "slug": "order-size-bands",
        "title": "Order Size Bands",
        "description": (
            "PulseShop finance classifies each order into size bands for dashboard "
            "filters. Small is under 50, medium is 50–149, and large is 150 or more.\n\n"
            "Assign a band label to every order using conditional logic."
        ),
        "difficulty": "easy",
        "topic_slug": "conditional-logic",
        "tags": ["case", "classification"],
        "role_tags": ["Data Analyst", "BI Developer", "Analytics Engineer"],
        "scenario": "Sales order banding for finance dashboards.",
        "task_description": (
            "Return order_id, amount, and size_band where size_band is 'small' if amount < 50, "
            "'medium' if amount < 150, else 'large'. Order by order_id."
        ),
        "expected_columns": ["order_id", "amount", "size_band"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT order_id, amount,\n"
            "  CASE\n"
            "    WHEN amount < 50 THEN 'small'\n"
            "    WHEN amount < 150 THEN 'medium'\n"
            "    ELSE 'large'\n"
            "  END AS size_band\n"
            "FROM shop_orders\n"
            "ORDER BY order_id"
        ),
        "solution_explanation": "CASE evaluates thresholds in order and labels each order.",
        "alternate_solution": None,
        "key_concepts": ["CASE", "WHEN", "ELSE"],
        "hints": ["Check the lower thresholds first.", "Alias the CASE expression as size_band."],
        "sample_expected_rows": [[1, 40, "small"]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "shop_orders",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "order_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"order_id": 1, "amount": 40},
                    {"order_id": 2, "amount": 90},
                    {"order_id": 3, "amount": 150},
                    {"order_id": 4, "amount": 25},
                    {"order_id": 5, "amount": 200},
                ],
            }
        ],
        "expected_rows": [
            [1, 40, "small"],
            [2, 90, "medium"],
            [3, 150, "large"],
            [4, 25, "small"],
            [5, 200, "large"],
        ],
    },
    {
        "slug": "march-course-enrollments",
        "title": "March Course Enrollments",
        "description": (
            "LearnLoop education ops tracks course enrollments by date. For a spring "
            "campaign review they only want enrollments that happened in March 2024.\n\n"
            "Filter by calendar month and year using date functions."
        ),
        "difficulty": "easy",
        "topic_slug": "date-functions",
        "tags": ["extract", "filter-dates"],
        "role_tags": ["Data Analyst", "Business Analyst", "Analytics Engineer"],
        "scenario": "Education enrollment filter for March 2024.",
        "task_description": (
            "Return enrollment_id, student_name, and enroll_date for rows where the year "
            "is 2024 and the month is 3. Order by enrollment_id."
        ),
        "expected_columns": ["enrollment_id", "student_name", "enroll_date"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT enrollment_id, student_name, enroll_date\n"
            "FROM enrollments\n"
            "WHERE EXTRACT(YEAR FROM enroll_date) = 2024\n"
            "  AND EXTRACT(MONTH FROM enroll_date) = 3\n"
            "ORDER BY enrollment_id"
        ),
        "solution_explanation": "EXTRACT pulls year and month components for filtering.",
        "alternate_solution": (
            "SELECT enrollment_id, student_name, enroll_date\n"
            "FROM enrollments\n"
            "WHERE enroll_date >= DATE '2024-03-01'\n"
            "  AND enroll_date < DATE '2024-04-01'\n"
            "ORDER BY enrollment_id"
        ),
        "key_concepts": ["EXTRACT", "DATE filtering"],
        "hints": ["EXTRACT(MONTH FROM ...) returns 3 for March.", "Also constrain the year to 2024."],
        "sample_expected_rows": [[2, "Kabir", "2024-03-05"]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "enrollments",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "enrollment_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "student_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "enroll_date", "data_type": "DATE", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"enrollment_id": 1, "student_name": "Riya", "enroll_date": "2024-02-28"},
                    {"enrollment_id": 2, "student_name": "Kabir", "enroll_date": "2024-03-05"},
                    {"enrollment_id": 3, "student_name": "Nina", "enroll_date": "2024-03-18"},
                    {"enrollment_id": 4, "student_name": "Omar", "enroll_date": "2024-04-01"},
                    {"enrollment_id": 5, "student_name": "Tara", "enroll_date": "2023-03-12"},
                ],
            }
        ],
        "expected_rows": [
            [2, "Kabir", "2024-03-05"],
            [3, "Nina", "2024-03-18"],
        ],
    },
    {
        "slug": "settled-invoice-payments",
        "title": "Settled Invoice Payments",
        "description": (
            "PayStack Internal finance reconciles invoices against payment events. "
            "Controllers want only payments that settled invoices marked paid.\n\n"
            "Join payments to invoices and keep paid settlements."
        ),
        "difficulty": "easy",
        "topic_slug": "joins",
        "tags": ["join", "finance"],
        "role_tags": ["Data Analyst", "Backend Developer", "BI Developer"],
        "scenario": "Fintech invoice-payment reconciliation.",
        "task_description": (
            "Return payment_id, invoice_id, and amount for payments joined to invoices "
            "where invoice status is 'paid'. Order by payment_id."
        ),
        "expected_columns": ["payment_id", "invoice_id", "amount"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT p.payment_id, p.invoice_id, p.amount\n"
            "FROM payments p\n"
            "INNER JOIN invoices i ON p.invoice_id = i.invoice_id\n"
            "WHERE i.status = 'paid'\n"
            "ORDER BY p.payment_id"
        ),
        "solution_explanation": "Join on invoice_id and filter invoices to paid status.",
        "alternate_solution": None,
        "key_concepts": ["INNER JOIN", "WHERE"],
        "hints": ["Filter on invoices.status after joining.", "Order by payment_id."],
        "sample_expected_rows": [[11, 201, 500]],
        "estimated_time_seconds": 360,
        "tables": [
            {
                "table_name": "invoices",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "invoice_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "status", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"invoice_id": 201, "status": "paid"},
                    {"invoice_id": 202, "status": "open"},
                    {"invoice_id": 203, "status": "paid"},
                    {"invoice_id": 204, "status": "void"},
                ],
            },
            {
                "table_name": "payments",
                "display_name": None,
                "description": None,
                "sort_order": 1,
                "columns": [
                    {"column_name": "payment_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "invoice_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"payment_id": 11, "invoice_id": 201, "amount": 500},
                    {"payment_id": 12, "invoice_id": 202, "amount": 300},
                    {"payment_id": 13, "invoice_id": 203, "amount": 750},
                    {"payment_id": 14, "invoice_id": 204, "amount": 100},
                ],
            },
        ],
        "expected_rows": [
            [11, 201, 500],
            [13, 203, 750],
        ],
    },
    {
        "slug": "store-average-basket",
        "title": "Store Average Basket",
        "description": (
            "GreenBasket grocery ops compares average basket size across neighborhood "
            "stores to spot underperforming locations.\n\n"
            "Compute the average order amount per store rounded to the nearest integer."
        ),
        "difficulty": "easy",
        "topic_slug": "aggregations",
        "tags": ["avg", "round"],
        "role_tags": ["Data Analyst", "BI Developer", "Business Analyst"],
        "scenario": "Retail average basket comparison by store.",
        "task_description": (
            "Return store_name and avg_basket as ROUND(AVG(amount))::INTEGER grouped by "
            "store_name, ordered by avg_basket descending."
        ),
        "expected_columns": ["store_name", "avg_basket"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT store_name, ROUND(AVG(amount))::INTEGER AS avg_basket\n"
            "FROM store_orders\n"
            "GROUP BY store_name\n"
            "ORDER BY avg_basket DESC"
        ),
        "solution_explanation": "AVG per store, ROUND to nearest integer, cast to INTEGER.",
        "alternate_solution": None,
        "key_concepts": ["AVG", "ROUND", "GROUP BY"],
        "hints": ["Cast the rounded average to INTEGER.", "One row per store_name."],
        "sample_expected_rows": [["Indiranagar", 110]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "store_orders",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "order_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "store_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"order_id": 1, "store_name": "Indiranagar", "amount": 100},
                    {"order_id": 2, "store_name": "Indiranagar", "amount": 120},
                    {"order_id": 3, "store_name": "Koramangala", "amount": 80},
                    {"order_id": 4, "store_name": "Koramangala", "amount": 90},
                    {"order_id": 5, "store_name": "Whitefield", "amount": 150},
                    {"order_id": 6, "store_name": "Whitefield", "amount": 50},
                ],
            }
        ],
        "expected_rows": [
            ["Indiranagar", 110],
            ["Whitefield", 100],
            ["Koramangala", 85],
        ],
    },
    {
        "slug": "duplicate-member-emails",
        "title": "Duplicate Member Emails",
        "description": (
            "FitClub membership ops discovered messy CRM imports. They need emails that "
            "appear more than once so duplicates can be merged.\n\n"
            "Find emails with a count greater than one."
        ),
        "difficulty": "easy",
        "topic_slug": "aggregations",
        "tags": ["having", "duplicates"],
        "role_tags": ["Data Analyst", "Data Engineer", "Database Developer"],
        "scenario": "Gym CRM duplicate email cleanup.",
        "task_description": (
            "Return email and occurrence_count for emails appearing more than once, "
            "ordered by occurrence_count descending, then email ascending."
        ),
        "expected_columns": ["email", "occurrence_count"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT email, COUNT(*) AS occurrence_count\n"
            "FROM members\n"
            "GROUP BY email\n"
            "HAVING COUNT(*) > 1\n"
            "ORDER BY occurrence_count DESC, email"
        ),
        "solution_explanation": "GROUP BY email and filter groups with HAVING COUNT(*) > 1.",
        "alternate_solution": None,
        "key_concepts": ["GROUP BY", "HAVING", "COUNT"],
        "hints": ["HAVING filters after aggregation.", "Unique emails should not appear."],
        "sample_expected_rows": [["alex@fitclub.io", 3]],
        "estimated_time_seconds": 300,
        "tables": [
            {
                "table_name": "members",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "member_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "full_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "email", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"member_id": 1, "full_name": "Alex One", "email": "alex@fitclub.io"},
                    {"member_id": 2, "full_name": "Alex Two", "email": "alex@fitclub.io"},
                    {"member_id": 3, "full_name": "Alex Three", "email": "alex@fitclub.io"},
                    {"member_id": 4, "full_name": "Blake", "email": "blake@fitclub.io"},
                    {"member_id": 5, "full_name": "Casey A", "email": "casey@fitclub.io"},
                    {"member_id": 6, "full_name": "Casey B", "email": "casey@fitclub.io"},
                ],
            }
        ],
        "expected_rows": [
            ["alex@fitclub.io", 3],
            ["casey@fitclub.io", 2],
        ],
    },
    # -------------------------------------------------------------------------
    # MEDIUM (12)
    # -------------------------------------------------------------------------
    {
        "slug": "top-customers-by-revenue",
        "title": "Top Customers by Revenue",
        "description": (
            "MarketLane sales leadership wants VIP outreach based on lifetime spend. "
            "Combine customer profiles with completed order amounts.\n\n"
            "Rank customers by total revenue from completed orders only."
        ),
        "difficulty": "medium",
        "topic_slug": "joins",
        "tags": ["revenue", "group-by", "join"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Business Analyst"],
        "scenario": "Ecommerce VIP customer ranking by completed-order revenue.",
        "task_description": (
            "Return customer_name and total_revenue (SUM of amount for status 'completed') "
            "for each customer who has at least one completed order. Order by total_revenue "
            "descending, then customer_name ascending."
        ),
        "expected_columns": ["customer_name", "total_revenue"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT c.customer_name, SUM(o.amount) AS total_revenue\n"
            "FROM customers c\n"
            "INNER JOIN orders o ON c.customer_id = o.customer_id\n"
            "WHERE o.status = 'completed'\n"
            "GROUP BY c.customer_id, c.customer_name\n"
            "ORDER BY total_revenue DESC, c.customer_name"
        ),
        "solution_explanation": (
            "Join customers to orders, keep completed rows, aggregate with SUM, and sort."
        ),
        "alternate_solution": None,
        "key_concepts": ["JOIN", "SUM", "GROUP BY", "WHERE"],
        "hints": ["Filter status before aggregating.", "Customers with only cancelled orders drop out."],
        "sample_expected_rows": [["Isha Verma", 450]],
        "estimated_time_seconds": 480,
        "tables": [
            {
                "table_name": "customers",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"customer_id": 1, "customer_name": "Isha Verma"},
                    {"customer_id": 2, "customer_name": "Jon Hale"},
                    {"customer_id": 3, "customer_name": "Zara Ali"},
                    {"customer_id": 4, "customer_name": "Ben Ortiz"},
                ],
            },
            {
                "table_name": "orders",
                "display_name": None,
                "description": None,
                "sort_order": 1,
                "columns": [
                    {"column_name": "order_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                    {"column_name": "status", "data_type": "TEXT", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"order_id": 1, "customer_id": 1, "amount": 200, "status": "completed"},
                    {"order_id": 2, "customer_id": 1, "amount": 250, "status": "completed"},
                    {"order_id": 3, "customer_id": 2, "amount": 300, "status": "completed"},
                    {"order_id": 4, "customer_id": 2, "amount": 100, "status": "cancelled"},
                    {"order_id": 5, "customer_id": 3, "amount": 150, "status": "completed"},
                    {"order_id": 6, "customer_id": 4, "amount": 90, "status": "cancelled"},
                ],
            },
        ],
        "expected_rows": [
            ["Isha Verma", 450],
            ["Jon Hale", 300],
            ["Zara Ali", 150],
        ],
    },
    {
        "slug": "monthly-subscription-sales",
        "title": "Monthly Subscription Sales",
        "description": (
            "StreamNest finance reviews paid subscription charges by calendar month. "
            "Build a monthly GMV series for 2024 charges only.\n\n"
            "Truncate charge dates to month and sum amounts."
        ),
        "difficulty": "medium",
        "topic_slug": "date-functions",
        "tags": ["date_trunc", "subscriptions"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "BI Developer"],
        "scenario": "Subscription billing monthly GMV series.",
        "task_description": (
            "Return sales_month as DATE_TRUNC('month', charge_date)::DATE and monthly_sales "
            "as SUM(amount) for 2024 charges. Order by sales_month ascending."
        ),
        "expected_columns": ["sales_month", "monthly_sales"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT DATE_TRUNC('month', charge_date)::DATE AS sales_month,\n"
            "       SUM(amount) AS monthly_sales\n"
            "FROM charges\n"
            "WHERE EXTRACT(YEAR FROM charge_date) = 2024\n"
            "GROUP BY DATE_TRUNC('month', charge_date)\n"
            "ORDER BY sales_month"
        ),
        "solution_explanation": "DATE_TRUNC buckets dates into months; SUM aggregates revenue.",
        "alternate_solution": None,
        "key_concepts": ["DATE_TRUNC", "GROUP BY", "SUM"],
        "hints": ["Cast the truncated timestamp to DATE.", "Exclude non-2024 rows."],
        "sample_expected_rows": [["2024-01-01", 120]],
        "estimated_time_seconds": 480,
        "tables": [
            {
                "table_name": "charges",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "charge_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "charge_date", "data_type": "DATE", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"charge_id": 1, "charge_date": "2024-01-05", "amount": 50},
                    {"charge_id": 2, "charge_date": "2024-01-20", "amount": 70},
                    {"charge_id": 3, "charge_date": "2024-02-02", "amount": 80},
                    {"charge_id": 4, "charge_date": "2024-02-18", "amount": 40},
                    {"charge_id": 5, "charge_date": "2024-03-01", "amount": 100},
                    {"charge_id": 6, "charge_date": "2023-12-30", "amount": 999},
                ],
            }
        ],
        "expected_rows": [
            ["2024-01-01", 120],
            ["2024-02-01", 120],
            ["2024-03-01", 100],
        ],
    },
    {
        "slug": "department-salary-rankings",
        "title": "Department Salary Rankings",
        "description": (
            "PeopleOps at Northwind Labs wants salary rankings within each department "
            "for compensation calibration.\n\n"
            "Use a window function to rank employees by salary inside their department."
        ),
        "difficulty": "medium",
        "topic_slug": "window-functions",
        "tags": ["rank", "partition"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Data Scientist"],
        "scenario": "HR compensation ranking within departments.",
        "task_description": (
            "Return employee_name, department, salary, and dept_rank as RANK() over "
            "salary descending partitioned by department. Order by department, dept_rank, "
            "employee_name."
        ),
        "expected_columns": ["employee_name", "department", "salary", "dept_rank"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT employee_name, department, salary,\n"
            "       RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank\n"
            "FROM staff\n"
            "ORDER BY department, dept_rank, employee_name"
        ),
        "solution_explanation": "RANK with PARTITION BY department orders salaries high to low within each dept.",
        "alternate_solution": None,
        "key_concepts": ["RANK", "PARTITION BY", "ORDER BY"],
        "hints": ["Partition by department.", "Highest salary should get rank 1."],
        "sample_expected_rows": [["Asha", "Engineering", 140000, 1]],
        "estimated_time_seconds": 540,
        "tables": [
            {
                "table_name": "staff",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "employee_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "employee_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "department", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                    {"column_name": "salary", "data_type": "INTEGER", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"employee_id": 1, "employee_name": "Asha", "department": "Engineering", "salary": 140000},
                    {"employee_id": 2, "employee_name": "Ben", "department": "Engineering", "salary": 120000},
                    {"employee_id": 3, "employee_name": "Cara", "department": "Engineering", "salary": 120000},
                    {"employee_id": 4, "employee_name": "Dee", "department": "Sales", "salary": 110000},
                    {"employee_id": 5, "employee_name": "Eli", "department": "Sales", "salary": 95000},
                    {"employee_id": 6, "employee_name": "Fay", "department": "Sales", "salary": 100000},
                ],
            }
        ],
        "expected_rows": [
            ["Asha", "Engineering", 140000, 1],
            ["Ben", "Engineering", 120000, 2],
            ["Cara", "Engineering", 120000, 2],
            ["Dee", "Sales", 110000, 1],
            ["Fay", "Sales", 100000, 2],
            ["Eli", "Sales", 95000, 3],
        ],
    },
    {
        "slug": "ticket-sla-breaches",
        "title": "Ticket SLA Breaches",
        "description": (
            "CloudCare support promises first response within 24 hours. Compliance wants "
            "tickets where the response landed after the SLA deadline.\n\n"
            "Compare responded_at against created_at + 24 hours."
        ),
        "difficulty": "medium",
        "topic_slug": "date-functions",
        "tags": ["interval", "sla"],
        "role_tags": ["Data Analyst", "Business Analyst", "Backend Developer"],
        "scenario": "Support SLA breach detection for first response.",
        "task_description": (
            "Return ticket_id, created_at, responded_at, and hours_to_respond as "
            "EXTRACT(EPOCH FROM (responded_at - created_at))/3600 rounded to 1 decimal "
            "for tickets where responded_at > created_at + INTERVAL '24 hours'. "
            "Order by ticket_id."
        ),
        "expected_columns": ["ticket_id", "created_at", "responded_at", "hours_to_respond"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT ticket_id, created_at, responded_at,\n"
            "       ROUND((EXTRACT(EPOCH FROM (responded_at - created_at)) / 3600)::NUMERIC, 1)\n"
            "         AS hours_to_respond\n"
            "FROM support_tickets\n"
            "WHERE responded_at > created_at + INTERVAL '24 hours'\n"
            "ORDER BY ticket_id"
        ),
        "solution_explanation": "Interval comparison finds breaches; epoch extract converts duration to hours.",
        "alternate_solution": None,
        "key_concepts": ["INTERVAL", "EXTRACT", "EPOCH"],
        "hints": ["Add an interval of 24 hours to created_at.", "Round hours to one decimal place."],
        "sample_expected_rows": [[2, "2024-05-01T09:00:00", "2024-05-02T12:00:00", 27.0]],
        "estimated_time_seconds": 540,
        "tables": [
            {
                "table_name": "support_tickets",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "ticket_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "created_at", "data_type": "TIMESTAMP", "is_nullable": False, "sort_order": 1},
                    {"column_name": "responded_at", "data_type": "TIMESTAMP", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"ticket_id": 1, "created_at": "2024-05-01T09:00:00", "responded_at": "2024-05-01T15:00:00"},
                    {"ticket_id": 2, "created_at": "2024-05-01T09:00:00", "responded_at": "2024-05-02T12:00:00"},
                    {"ticket_id": 3, "created_at": "2024-05-02T10:00:00", "responded_at": "2024-05-03T11:00:00"},
                    {"ticket_id": 4, "created_at": "2024-05-03T08:00:00", "responded_at": "2024-05-04T09:30:00"},
                    {"ticket_id": 5, "created_at": "2024-05-04T14:00:00", "responded_at": "2024-05-04T20:00:00"},
                ],
            }
        ],
        "expected_rows": [
            [2, "2024-05-01T09:00:00", "2024-05-02T12:00:00", 27.0],
            [3, "2024-05-02T10:00:00", "2024-05-03T11:00:00", 25.0],
            [4, "2024-05-03T08:00:00", "2024-05-04T09:30:00", 25.5],
        ],
    },
    {
        "slug": "channel-conversion-rates",
        "title": "Channel Conversion Rates",
        "description": (
            "AdPulse marketing tracks landing visits and purchases by acquisition "
            "channel. Leadership wants conversion rate per channel.\n\n"
            "Compute purchases / visits as a percentage rounded to one decimal."
        ),
        "difficulty": "medium",
        "topic_slug": "advanced-sql",
        "tags": ["conversion", "marketing"],
        "role_tags": ["Data Analyst", "Business Analyst", "Analytics Engineer"],
        "scenario": "Marketing channel conversion rate calculation.",
        "task_description": (
            "Return channel, visits, purchases, and conversion_pct as "
            "ROUND(100.0 * purchases / visits, 1) ordered by conversion_pct descending."
        ),
        "expected_columns": ["channel", "visits", "purchases", "conversion_pct"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT channel, visits, purchases,\n"
            "       ROUND(100.0 * purchases / visits, 1) AS conversion_pct\n"
            "FROM channel_stats\n"
            "ORDER BY conversion_pct DESC"
        ),
        "solution_explanation": "Multiply by 100.0 to force floating division, then ROUND to 1 decimal.",
        "alternate_solution": None,
        "key_concepts": ["arithmetic", "ROUND"],
        "hints": ["Use 100.0 not 100 to avoid integer division.", "Order by conversion_pct DESC."],
        "sample_expected_rows": [["Email", 200, 40, 20.0]],
        "estimated_time_seconds": 420,
        "tables": [
            {
                "table_name": "channel_stats",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "channel", "data_type": "TEXT", "is_nullable": False, "sort_order": 0},
                    {"column_name": "visits", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "purchases", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"channel": "Email", "visits": 200, "purchases": 40},
                    {"channel": "Paid Search", "visits": 500, "purchases": 50},
                    {"channel": "Social", "visits": 400, "purchases": 32},
                    {"channel": "Referral", "visits": 100, "purchases": 25},
                ],
            }
        ],
        "expected_rows": [
            ["Referral", 100, 25, 25.0],
            ["Email", 200, 40, 20.0],
            ["Paid Search", 500, 50, 10.0],
            ["Social", 400, 32, 8.0],
        ],
    },
    {
        "slug": "second-highest-deal",
        "title": "Second Highest Closed Deal",
        "description": (
            "SummitCRM sales ops wants the second-highest closed deal amount for a "
            "quota celebration runner-up. Ties should share the same dense rank.\n\n"
            "Use a window function to isolate rank 2 among closed deals."
        ),
        "difficulty": "medium",
        "topic_slug": "window-functions",
        "tags": ["dense-rank", "nth"],
        "role_tags": ["Data Analyst", "Business Analyst", "Data Scientist"],
        "scenario": "Sales CRM second-highest closed deal lookup.",
        "task_description": (
            "Return deal_id, rep_name, and amount for closed deals whose DENSE_RANK by "
            "amount descending equals 2. Order by deal_id."
        ),
        "expected_columns": ["deal_id", "rep_name", "amount"],
        "order_sensitive": True,
        "solution_query": (
            "WITH ranked AS (\n"
            "  SELECT deal_id, rep_name, amount,\n"
            "         DENSE_RANK() OVER (ORDER BY amount DESC) AS rnk\n"
            "  FROM deals\n"
            "  WHERE stage = 'closed'\n"
            ")\n"
            "SELECT deal_id, rep_name, amount\n"
            "FROM ranked\n"
            "WHERE rnk = 2\n"
            "ORDER BY deal_id"
        ),
        "solution_explanation": "DENSE_RANK assigns contiguous ranks; filter to rank 2 for the second-highest amount.",
        "alternate_solution": (
            "SELECT deal_id, rep_name, amount\n"
            "FROM deals\n"
            "WHERE stage = 'closed'\n"
            "  AND amount = (\n"
            "    SELECT MAX(amount) FROM deals d2\n"
            "    WHERE stage = 'closed'\n"
            "      AND amount < (SELECT MAX(amount) FROM deals WHERE stage = 'closed')\n"
            "  )\n"
            "ORDER BY deal_id"
        ),
        "key_concepts": ["DENSE_RANK", "CTE", "filtering ranks"],
        "hints": ["Filter to stage = 'closed' first.", "DENSE_RANK avoids gaps when amounts tie at the top."],
        "sample_expected_rows": [[3, "Sam", 80000]],
        "estimated_time_seconds": 540,
        "tables": [
            {
                "table_name": "deals",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "deal_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "rep_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                    {"column_name": "stage", "data_type": "TEXT", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"deal_id": 1, "rep_name": "Ana", "amount": 100000, "stage": "closed"},
                    {"deal_id": 2, "rep_name": "Bo", "amount": 100000, "stage": "closed"},
                    {"deal_id": 3, "rep_name": "Sam", "amount": 80000, "stage": "closed"},
                    {"deal_id": 4, "rep_name": "Kim", "amount": 75000, "stage": "closed"},
                    {"deal_id": 5, "rep_name": "Lee", "amount": 90000, "stage": "pipeline"},
                ],
            }
        ],
        "expected_rows": [
            [3, "Sam", 80000],
        ],
    },
    {
        "slug": "daily-running-revenue",
        "title": "Daily Running Revenue",
        "description": (
            "ByteCart finance wants a cumulative revenue curve across consecutive sales "
            "days for a weekly ops review.\n\n"
            "Compute a running total of daily_revenue ordered by sale_date."
        ),
        "difficulty": "medium",
        "topic_slug": "window-functions",
        "tags": ["running-total", "sum-over"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "BI Developer"],
        "scenario": "Ecommerce cumulative daily revenue series.",
        "task_description": (
            "Return sale_date, daily_revenue, and running_revenue as SUM(daily_revenue) "
            "OVER (ORDER BY sale_date). Order by sale_date."
        ),
        "expected_columns": ["sale_date", "daily_revenue", "running_revenue"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT sale_date, daily_revenue,\n"
            "       SUM(daily_revenue) OVER (ORDER BY sale_date) AS running_revenue\n"
            "FROM daily_sales\n"
            "ORDER BY sale_date"
        ),
        "solution_explanation": "A window SUM without PARTITION accumulates in sale_date order.",
        "alternate_solution": None,
        "key_concepts": ["SUM OVER", "running total"],
        "hints": ["Order the window by sale_date.", "No PARTITION BY is needed for a single series."],
        "sample_expected_rows": [["2024-06-01", 100, 100]],
        "estimated_time_seconds": 480,
        "tables": [
            {
                "table_name": "daily_sales",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "sale_date", "data_type": "DATE", "is_nullable": False, "sort_order": 0},
                    {"column_name": "daily_revenue", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"sale_date": "2024-06-01", "daily_revenue": 100},
                    {"sale_date": "2024-06-02", "daily_revenue": 150},
                    {"sale_date": "2024-06-03", "daily_revenue": 80},
                    {"sale_date": "2024-06-04", "daily_revenue": 200},
                    {"sale_date": "2024-06-05", "daily_revenue": 50},
                ],
            }
        ],
        "expected_rows": [
            ["2024-06-01", 100, 100],
            ["2024-06-02", 150, 250],
            ["2024-06-03", 80, 330],
            ["2024-06-04", 200, 530],
            ["2024-06-05", 50, 580],
        ],
    },
    {
        "slug": "cte-repeat-high-spenders",
        "title": "Repeat High Spenders",
        "description": (
            "GlowMart loyalty wants customers who placed at least two orders and whose "
            "average order value is at least 100.\n\n"
            "Use a CTE to aggregate first, then filter the result."
        ),
        "difficulty": "medium",
        "topic_slug": "cte",
        "tags": ["cte", "loyalty"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Data Engineer"],
        "scenario": "Retail loyalty filter for repeat high-AOV customers.",
        "task_description": (
            "Using a CTE, return customer_id, order_count, and avg_order_value (rounded "
            "to integer) for customers with order_count >= 2 and avg_order_value >= 100. "
            "Order by avg_order_value descending."
        ),
        "expected_columns": ["customer_id", "order_count", "avg_order_value"],
        "order_sensitive": True,
        "solution_query": (
            "WITH customer_stats AS (\n"
            "  SELECT customer_id,\n"
            "         COUNT(*) AS order_count,\n"
            "         ROUND(AVG(amount))::INTEGER AS avg_order_value\n"
            "  FROM purchases\n"
            "  GROUP BY customer_id\n"
            ")\n"
            "SELECT customer_id, order_count, avg_order_value\n"
            "FROM customer_stats\n"
            "WHERE order_count >= 2 AND avg_order_value >= 100\n"
            "ORDER BY avg_order_value DESC"
        ),
        "solution_explanation": "CTE aggregates per customer; outer query applies both thresholds.",
        "alternate_solution": None,
        "key_concepts": ["WITH", "AVG", "HAVING-style filter"],
        "hints": ["Aggregate inside the CTE.", "Apply both filters in the outer WHERE."],
        "sample_expected_rows": [[2, 2, 150]],
        "estimated_time_seconds": 540,
        "tables": [
            {
                "table_name": "purchases",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "purchase_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"purchase_id": 1, "customer_id": 1, "amount": 80},
                    {"purchase_id": 2, "customer_id": 1, "amount": 90},
                    {"purchase_id": 3, "customer_id": 2, "amount": 120},
                    {"purchase_id": 4, "customer_id": 2, "amount": 180},
                    {"purchase_id": 5, "customer_id": 3, "amount": 200},
                    {"purchase_id": 6, "customer_id": 4, "amount": 110},
                    {"purchase_id": 7, "customer_id": 4, "amount": 130},
                ],
            }
        ],
        "expected_rows": [
            [2, 2, 150],
            [4, 2, 120],
        ],
    },
    {
        "slug": "above-average-spenders",
        "title": "Above Average Spenders",
        "description": (
            "CityBank card analytics wants cardholders whose monthly spend exceeds the "
            "overall average spend across all cardholders.\n\n"
            "Use a subquery to compute the global average as the threshold."
        ),
        "difficulty": "medium",
        "topic_slug": "subqueries",
        "tags": ["subquery", "comparison"],
        "role_tags": ["Data Analyst", "Data Scientist", "Analytics Engineer"],
        "scenario": "Banking cardholder spend vs global average.",
        "task_description": (
            "Return cardholder_name and monthly_spend for rows where monthly_spend is "
            "greater than the average monthly_spend of all cardholders. Order by "
            "monthly_spend descending."
        ),
        "expected_columns": ["cardholder_name", "monthly_spend"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT cardholder_name, monthly_spend\n"
            "FROM card_spend\n"
            "WHERE monthly_spend > (SELECT AVG(monthly_spend) FROM card_spend)\n"
            "ORDER BY monthly_spend DESC"
        ),
        "solution_explanation": "Scalar subquery computes AVG; outer query keeps above-average rows.",
        "alternate_solution": None,
        "key_concepts": ["scalar subquery", "AVG"],
        "hints": ["Average is across all rows in card_spend.", "Compare each row to that scalar."],
        "sample_expected_rows": [["Nora", 900]],
        "estimated_time_seconds": 420,
        "tables": [
            {
                "table_name": "card_spend",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "cardholder_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "cardholder_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "monthly_spend", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"cardholder_id": 1, "cardholder_name": "Nora", "monthly_spend": 900},
                    {"cardholder_id": 2, "cardholder_name": "Omar", "monthly_spend": 400},
                    {"cardholder_id": 3, "cardholder_name": "Pia", "monthly_spend": 700},
                    {"cardholder_id": 4, "cardholder_name": "Quin", "monthly_spend": 300},
                    {"cardholder_id": 5, "cardholder_name": "Raj", "monthly_spend": 500},
                ],
            }
        ],
        # avg = (900+400+700+300+500)/5 = 560
        "expected_rows": [
            ["Nora", 900],
            ["Pia", 700],
        ],
    },
    {
        "slug": "loyalty-tier-assignment",
        "title": "Loyalty Tier Assignment",
        "description": (
            "SkyMiles+ assigns tiers from points: Bronze below 1000, Silver below 5000, "
            "Gold otherwise. Marketing needs a labeled member list.\n\n"
            "Map points to tier labels with CASE."
        ),
        "difficulty": "medium",
        "topic_slug": "conditional-logic",
        "tags": ["case", "loyalty"],
        "role_tags": ["Data Analyst", "BI Developer", "Business Analyst"],
        "scenario": "Airline loyalty tier labeling from points balances.",
        "task_description": (
            "Return member_name, points, and tier ('Bronze', 'Silver', or 'Gold') using "
            "the thresholds above. Order by points descending."
        ),
        "expected_columns": ["member_name", "points", "tier"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT member_name, points,\n"
            "  CASE\n"
            "    WHEN points < 1000 THEN 'Bronze'\n"
            "    WHEN points < 5000 THEN 'Silver'\n"
            "    ELSE 'Gold'\n"
            "  END AS tier\n"
            "FROM loyalty_members\n"
            "ORDER BY points DESC"
        ),
        "solution_explanation": "Ordered CASE thresholds assign Bronze/Silver/Gold.",
        "alternate_solution": None,
        "key_concepts": ["CASE", "classification"],
        "hints": ["Check Bronze before Silver.", "Gold is the ELSE branch."],
        "sample_expected_rows": [["Vik", 8000, "Gold"]],
        "estimated_time_seconds": 360,
        "tables": [
            {
                "table_name": "loyalty_members",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "member_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "member_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "points", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"member_id": 1, "member_name": "Vik", "points": 8000},
                    {"member_id": 2, "member_name": "Una", "points": 4500},
                    {"member_id": 3, "member_name": "Ted", "points": 900},
                    {"member_id": 4, "member_name": "Sue", "points": 1000},
                    {"member_id": 5, "member_name": "Rio", "points": 5000},
                ],
            }
        ],
        "expected_rows": [
            ["Vik", 8000, "Gold"],
            ["Rio", 5000, "Gold"],
            ["Una", 4500, "Silver"],
            ["Sue", 1000, "Silver"],
            ["Ted", 900, "Bronze"],
        ],
    },
    {
        "slug": "formatted-customer-labels",
        "title": "Formatted Customer Labels",
        "description": (
            "ParcelGo warehouse printers need shipping labels combining uppercase city "
            "codes with trimmed customer names.\n\n"
            "Build a display label using string functions."
        ),
        "difficulty": "medium",
        "topic_slug": "string-functions",
        "tags": ["upper", "trim", "concat"],
        "role_tags": ["Data Engineer", "Backend Developer", "Analytics Engineer"],
        "scenario": "Logistics shipping label string formatting.",
        "task_description": (
            "Return customer_id and label as UPPER(TRIM(city_code)) || '-' || TRIM(customer_name) "
            "ordered by customer_id."
        ),
        "expected_columns": ["customer_id", "label"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT customer_id,\n"
            "       UPPER(TRIM(city_code)) || '-' || TRIM(customer_name) AS label\n"
            "FROM ship_customers\n"
            "ORDER BY customer_id"
        ),
        "solution_explanation": "TRIM cleans whitespace; UPPER normalizes city codes; || concatenates.",
        "alternate_solution": (
            "SELECT customer_id,\n"
            "       CONCAT(UPPER(TRIM(city_code)), '-', TRIM(customer_name)) AS label\n"
            "FROM ship_customers\n"
            "ORDER BY customer_id"
        ),
        "key_concepts": ["UPPER", "TRIM", "concatenation"],
        "hints": ["Trim both city_code and customer_name.", "Separate parts with a hyphen."],
        "sample_expected_rows": [[1, "BLR-Asha Rao"]],
        "estimated_time_seconds": 360,
        "tables": [
            {
                "table_name": "ship_customers",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "city_code", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"customer_id": 1, "customer_name": " Asha Rao ", "city_code": "blr"},
                    {"customer_id": 2, "customer_name": "Ben Cole", "city_code": " mum "},
                    {"customer_id": 3, "customer_name": "Cora Lee", "city_code": "del"},
                    {"customer_id": 4, "customer_name": " Dan Wu", "city_code": "HYD"},
                ],
            }
        ],
        "expected_rows": [
            [1, "BLR-Asha Rao"],
            [2, "MUM-Ben Cole"],
            [3, "DEL-Cora Lee"],
            [4, "HYD-Dan Wu"],
        ],
    },
    {
        "slug": "products-never-ordered",
        "title": "Products Never Ordered",
        "description": (
            "Warehouse planners at NestKart want SKUs that exist in the catalog but have "
            "never appeared on an order line.\n\n"
            "Find catalog products missing from order_items."
        ),
        "difficulty": "medium",
        "topic_slug": "subqueries",
        "tags": ["not-in", "anti-join"],
        "role_tags": ["Data Analyst", "Data Engineer", "Backend Developer"],
        "scenario": "Ecommerce catalog items with zero order history.",
        "task_description": (
            "Return product_id and product_name for products that do not appear in "
            "order_items. Order by product_id."
        ),
        "expected_columns": ["product_id", "product_name"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT p.product_id, p.product_name\n"
            "FROM catalog p\n"
            "WHERE p.product_id NOT IN (SELECT product_id FROM order_items)\n"
            "ORDER BY p.product_id"
        ),
        "solution_explanation": "NOT IN (or anti-join) keeps products absent from order_items.",
        "alternate_solution": (
            "SELECT p.product_id, p.product_name\n"
            "FROM catalog p\n"
            "LEFT JOIN order_items oi ON p.product_id = oi.product_id\n"
            "WHERE oi.product_id IS NULL\n"
            "ORDER BY p.product_id"
        ),
        "key_concepts": ["NOT IN", "anti-join", "subquery"],
        "hints": ["Compare product_id against order_items.", "Ordered products should be excluded."],
        "sample_expected_rows": [[3, "Yoga Mat"]],
        "estimated_time_seconds": 480,
        "tables": [
            {
                "table_name": "catalog",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "product_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "product_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"product_id": 1, "product_name": "Water Bottle"},
                    {"product_id": 2, "product_name": "Resistance Band"},
                    {"product_id": 3, "product_name": "Yoga Mat"},
                    {"product_id": 4, "product_name": "Foam Roller"},
                    {"product_id": 5, "product_name": "Jump Rope"},
                ],
            },
            {
                "table_name": "order_items",
                "display_name": None,
                "description": None,
                "sort_order": 1,
                "columns": [
                    {"column_name": "item_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "product_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"item_id": 1, "product_id": 1},
                    {"item_id": 2, "product_id": 2},
                    {"item_id": 3, "product_id": 1},
                    {"item_id": 4, "product_id": 5},
                ],
            },
        ],
        "expected_rows": [
            [3, "Yoga Mat"],
            [4, "Foam Roller"],
        ],
    },
    # -------------------------------------------------------------------------
    # HARD (6)
    # -------------------------------------------------------------------------
    {
        "slug": "weekly-active-retention",
        "title": "Weekly Active Retention",
        "description": (
            "HabitApp product analytics defines week-1 retention as users who were "
            "active in week 0 and also active in week 1.\n\n"
            "Compute retained users and retention rate for the week-0 cohort."
        ),
        "difficulty": "hard",
        "topic_slug": "advanced-sql",
        "tags": ["retention", "cohort"],
        "role_tags": ["Data Scientist", "Analytics Engineer", "Data Analyst"],
        "scenario": "Product analytics week-1 retention for an app cohort.",
        "task_description": (
            "Using activity weeks 0 and 1, return cohort_users (distinct users in week 0), "
            "retained_users (distinct users active in both weeks), and retention_pct as "
            "ROUND(100.0 * retained_users / cohort_users, 1)."
        ),
        "expected_columns": ["cohort_users", "retained_users", "retention_pct"],
        "order_sensitive": False,
        "solution_query": (
            "WITH week0 AS (\n"
            "  SELECT DISTINCT user_id FROM activity WHERE activity_week = 0\n"
            "), week1 AS (\n"
            "  SELECT DISTINCT user_id FROM activity WHERE activity_week = 1\n"
            ")\n"
            "SELECT\n"
            "  (SELECT COUNT(*) FROM week0) AS cohort_users,\n"
            "  (SELECT COUNT(*) FROM week0 w0 INNER JOIN week1 w1 ON w0.user_id = w1.user_id)\n"
            "    AS retained_users,\n"
            "  ROUND(\n"
            "    100.0 * (SELECT COUNT(*) FROM week0 w0 INNER JOIN week1 w1 ON w0.user_id = w1.user_id)\n"
            "    / (SELECT COUNT(*) FROM week0),\n"
            "    1\n"
            "  ) AS retention_pct"
        ),
        "solution_explanation": "CTEs isolate weekly cohorts; intersection counts retained users.",
        "alternate_solution": None,
        "key_concepts": ["CTE", "retention", "DISTINCT"],
        "hints": ["Week 0 defines the cohort.", "Retention requires presence in both weeks."],
        "sample_expected_rows": [[4, 2, 50.0]],
        "estimated_time_seconds": 720,
        "tables": [
            {
                "table_name": "activity",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "user_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "activity_week", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"user_id": 1, "activity_week": 0},
                    {"user_id": 2, "activity_week": 0},
                    {"user_id": 3, "activity_week": 0},
                    {"user_id": 4, "activity_week": 0},
                    {"user_id": 1, "activity_week": 1},
                    {"user_id": 3, "activity_week": 1},
                    {"user_id": 5, "activity_week": 1},
                    {"user_id": 2, "activity_week": 0},
                ],
            }
        ],
        # week0 users 1,2,3,4; retained 1,3 => 2/4 = 50.0
        "expected_rows": [
            [4, 2, 50.0],
        ],
    },
    {
        "slug": "checkout-funnel-rates",
        "title": "Checkout Funnel Rates",
        "description": (
            "ShopFlow growth measures a three-step funnel: view → cart → purchase. "
            "They need step counts and conversion from the prior step.\n\n"
            "Build funnel metrics ordered by step sequence."
        ),
        "difficulty": "hard",
        "topic_slug": "advanced-sql",
        "tags": ["funnel", "lag"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Data Scientist"],
        "scenario": "Ecommerce checkout funnel step conversion analysis.",
        "task_description": (
            "Return step_name, step_order, users, and pct_of_previous as "
            "ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_order), 1) "
            "(NULL for the first step). Order by step_order."
        ),
        "expected_columns": ["step_name", "step_order", "users", "pct_of_previous"],
        "order_sensitive": True,
        "solution_query": (
            "SELECT step_name, step_order, users,\n"
            "       ROUND(100.0 * users / LAG(users) OVER (ORDER BY step_order), 1)\n"
            "         AS pct_of_previous\n"
            "FROM funnel_steps\n"
            "ORDER BY step_order"
        ),
        "solution_explanation": "LAG looks at the previous funnel step's users to compute step conversion.",
        "alternate_solution": None,
        "key_concepts": ["LAG", "funnel", "window functions"],
        "hints": ["First step pct_of_previous should be NULL.", "Order windows and output by step_order."],
        "sample_expected_rows": [["view", 1, 1000, None]],
        "estimated_time_seconds": 720,
        "tables": [
            {
                "table_name": "funnel_steps",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "step_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 0},
                    {"column_name": "step_order", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "users", "data_type": "INTEGER", "is_nullable": False, "sort_order": 2},
                ],
                "rows": [
                    {"step_name": "view", "step_order": 1, "users": 1000},
                    {"step_name": "cart", "step_order": 2, "users": 400},
                    {"step_name": "purchase", "step_order": 3, "users": 120},
                ],
            }
        ],
        "expected_rows": [
            ["view", 1, 1000, None],
            ["cart", 2, 400, 40.0],
            ["purchase", 3, 120, 30.0],
        ],
    },
    {
        "slug": "top-earner-per-department",
        "title": "Top Earner per Department",
        "description": (
            "CompBand HR wants exactly one top earner per department for a leadership "
            "briefing. If salaries tie, pick the lowest employee_id.\n\n"
            "Use ROW_NUMBER to select the winner in each partition."
        ),
        "difficulty": "hard",
        "topic_slug": "window-functions",
        "tags": ["row-number", "top-n"],
        "role_tags": ["Data Analyst", "Analytics Engineer", "Data Engineer"],
        "scenario": "HR top earner selection with deterministic tie-break.",
        "task_description": (
            "Return department, employee_name, and salary for the employee with "
            "ROW_NUMBER() = 1 when partitioned by department ordered by salary DESC, "
            "employee_id ASC. Order by department."
        ),
        "expected_columns": ["department", "employee_name", "salary"],
        "order_sensitive": True,
        "solution_query": (
            "WITH ranked AS (\n"
            "  SELECT department, employee_name, salary,\n"
            "         ROW_NUMBER() OVER (\n"
            "           PARTITION BY department\n"
            "           ORDER BY salary DESC, employee_id ASC\n"
            "         ) AS rn\n"
            "  FROM comp_staff\n"
            ")\n"
            "SELECT department, employee_name, salary\n"
            "FROM ranked\n"
            "WHERE rn = 1\n"
            "ORDER BY department"
        ),
        "solution_explanation": "ROW_NUMBER with a tie-break on employee_id yields one row per department.",
        "alternate_solution": None,
        "key_concepts": ["ROW_NUMBER", "PARTITION BY", "tie-break"],
        "hints": ["Order by salary DESC then employee_id ASC.", "Filter rn = 1."],
        "sample_expected_rows": [["Engineering", "Asha", 150000]],
        "estimated_time_seconds": 600,
        "tables": [
            {
                "table_name": "comp_staff",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "employee_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "employee_name", "data_type": "TEXT", "is_nullable": False, "sort_order": 1},
                    {"column_name": "department", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                    {"column_name": "salary", "data_type": "INTEGER", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"employee_id": 1, "employee_name": "Asha", "department": "Engineering", "salary": 150000},
                    {"employee_id": 2, "employee_name": "Ben", "department": "Engineering", "salary": 150000},
                    {"employee_id": 3, "employee_name": "Cara", "department": "Engineering", "salary": 130000},
                    {"employee_id": 4, "employee_name": "Dee", "department": "Sales", "salary": 120000},
                    {"employee_id": 5, "employee_name": "Eli", "department": "Sales", "salary": 110000},
                    {"employee_id": 6, "employee_name": "Fay", "department": "Marketing", "salary": 100000},
                ],
            }
        ],
        "expected_rows": [
            ["Engineering", "Asha", 150000],
            ["Marketing", "Fay", 100000],
            ["Sales", "Dee", 120000],
        ],
    },
    {
        "slug": "month-over-month-growth",
        "title": "Month-over-Month Growth",
        "description": (
            "Ledgerly SaaS finance tracks monthly recurring revenue and wants MoM "
            "growth percentage versus the prior month.\n\n"
            "Use a CTE plus LAG to compare consecutive months."
        ),
        "difficulty": "hard",
        "topic_slug": "cte",
        "tags": ["mom", "lag", "growth"],
        "role_tags": ["Analytics Engineer", "Data Analyst", "BI Developer"],
        "scenario": "SaaS MRR month-over-month growth calculation.",
        "task_description": (
            "Return sales_month, mrr, prev_mrr, and mom_growth_pct as "
            "ROUND(100.0 * (mrr - prev_mrr) / prev_mrr, 1) where prev_mrr comes from "
            "LAG(mrr). Exclude the first month (NULL prev). Order by sales_month."
        ),
        "expected_columns": ["sales_month", "mrr", "prev_mrr", "mom_growth_pct"],
        "order_sensitive": True,
        "solution_query": (
            "WITH ordered AS (\n"
            "  SELECT sales_month, mrr,\n"
            "         LAG(mrr) OVER (ORDER BY sales_month) AS prev_mrr\n"
            "  FROM monthly_mrr\n"
            ")\n"
            "SELECT sales_month, mrr, prev_mrr,\n"
            "       ROUND(100.0 * (mrr - prev_mrr) / prev_mrr, 1) AS mom_growth_pct\n"
            "FROM ordered\n"
            "WHERE prev_mrr IS NOT NULL\n"
            "ORDER BY sales_month"
        ),
        "solution_explanation": "LAG fetches prior-month MRR; growth formula uses percent change.",
        "alternate_solution": None,
        "key_concepts": ["CTE", "LAG", "percent change"],
        "hints": ["Filter out the first month where LAG is NULL.", "Round to one decimal."],
        "sample_expected_rows": [["2024-02-01", 12000, 10000, 20.0]],
        "estimated_time_seconds": 720,
        "tables": [
            {
                "table_name": "monthly_mrr",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "sales_month", "data_type": "DATE", "is_nullable": False, "sort_order": 0},
                    {"column_name": "mrr", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                ],
                "rows": [
                    {"sales_month": "2024-01-01", "mrr": 10000},
                    {"sales_month": "2024-02-01", "mrr": 12000},
                    {"sales_month": "2024-03-01", "mrr": 15000},
                    {"sales_month": "2024-04-01", "mrr": 13500},
                    {"sales_month": "2024-05-01", "mrr": 16200},
                ],
            }
        ],
        "expected_rows": [
            ["2024-02-01", 12000, 10000, 20.0],
            ["2024-03-01", 15000, 12000, 25.0],
            ["2024-04-01", 13500, 15000, -10.0],
            ["2024-05-01", 16200, 13500, 20.0],
        ],
    },
    {
        "slug": "session-to-purchase-gaps",
        "title": "Session to Purchase Gaps",
        "description": (
            "ClickTrail analytics stores chronological events per user. Growth wants "
            "the days between each user's first session and their first purchase.\n\n"
            "Use window functions and conditional aggregation."
        ),
        "difficulty": "hard",
        "topic_slug": "window-functions",
        "tags": ["min", "filter", "dates"],
        "role_tags": ["Data Scientist", "Analytics Engineer", "Data Analyst"],
        "scenario": "Product analytics time-to-first-purchase from session events.",
        "task_description": (
            "For users who have both a 'session' and a 'purchase' event, return user_id, "
            "first_session, first_purchase, and days_to_purchase as "
            "(first_purchase - first_session). Order by user_id."
        ),
        "expected_columns": ["user_id", "first_session", "first_purchase", "days_to_purchase"],
        "order_sensitive": True,
        "solution_query": (
            "WITH bounds AS (\n"
            "  SELECT user_id,\n"
            "         MIN(event_date) FILTER (WHERE event_type = 'session') AS first_session,\n"
            "         MIN(event_date) FILTER (WHERE event_type = 'purchase') AS first_purchase\n"
            "  FROM events\n"
            "  GROUP BY user_id\n"
            ")\n"
            "SELECT user_id, first_session, first_purchase,\n"
            "       (first_purchase - first_session) AS days_to_purchase\n"
            "FROM bounds\n"
            "WHERE first_session IS NOT NULL AND first_purchase IS NOT NULL\n"
            "ORDER BY user_id"
        ),
        "solution_explanation": "FILTER clauses compute typed minima; subtract dates for day gaps.",
        "alternate_solution": None,
        "key_concepts": ["FILTER", "MIN", "date subtraction"],
        "hints": ["Users missing either event type should be dropped.", "Date subtraction yields integer days."],
        "sample_expected_rows": [[1, "2024-07-01", "2024-07-04", 3]],
        "estimated_time_seconds": 720,
        "tables": [
            {
                "table_name": "events",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "event_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "user_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "event_type", "data_type": "TEXT", "is_nullable": False, "sort_order": 2},
                    {"column_name": "event_date", "data_type": "DATE", "is_nullable": False, "sort_order": 3},
                ],
                "rows": [
                    {"event_id": 1, "user_id": 1, "event_type": "session", "event_date": "2024-07-01"},
                    {"event_id": 2, "user_id": 1, "event_type": "session", "event_date": "2024-07-02"},
                    {"event_id": 3, "user_id": 1, "event_type": "purchase", "event_date": "2024-07-04"},
                    {"event_id": 4, "user_id": 2, "event_type": "session", "event_date": "2024-07-03"},
                    {"event_id": 5, "user_id": 2, "event_type": "purchase", "event_date": "2024-07-10"},
                    {"event_id": 6, "user_id": 3, "event_type": "session", "event_date": "2024-07-05"},
                    {"event_id": 7, "user_id": 4, "event_type": "purchase", "event_date": "2024-07-08"},
                ],
            }
        ],
        "expected_rows": [
            [1, "2024-07-01", "2024-07-04", 3],
            [2, "2024-07-03", "2024-07-10", 7],
        ],
    },
    {
        "slug": "first-purchase-cohort-revenue",
        "title": "First Purchase Cohort Revenue",
        "description": (
            "NorthCart analytics engineers define cohorts by each customer's first "
            "purchase month, then sum all subsequent completed revenue for that cohort.\n\n"
            "Combine a first-purchase CTE with joined order totals."
        ),
        "difficulty": "hard",
        "topic_slug": "advanced-sql",
        "tags": ["cohort", "cte", "revenue"],
        "role_tags": ["Analytics Engineer", "Data Engineer", "Data Scientist"],
        "scenario": "Ecommerce cohort revenue by first-purchase month.",
        "task_description": (
            "Return cohort_month as DATE_TRUNC('month', first_purchase_date)::DATE, "
            "customers (count of customers), and cohort_revenue (SUM of all completed "
            "order amounts for those customers). Order by cohort_month."
        ),
        "expected_columns": ["cohort_month", "customers", "cohort_revenue"],
        "order_sensitive": True,
        "solution_query": (
            "WITH first_purchase AS (\n"
            "  SELECT customer_id, MIN(order_date) AS first_purchase_date\n"
            "  FROM cohort_orders\n"
            "  WHERE status = 'completed'\n"
            "  GROUP BY customer_id\n"
            ")\n"
            "SELECT DATE_TRUNC('month', fp.first_purchase_date)::DATE AS cohort_month,\n"
            "       COUNT(DISTINCT fp.customer_id) AS customers,\n"
            "       SUM(o.amount) AS cohort_revenue\n"
            "FROM first_purchase fp\n"
            "INNER JOIN cohort_orders o\n"
            "  ON o.customer_id = fp.customer_id\n"
            " AND o.status = 'completed'\n"
            "GROUP BY DATE_TRUNC('month', fp.first_purchase_date)\n"
            "ORDER BY cohort_month"
        ),
        "solution_explanation": (
            "First CTE finds each customer's earliest completed purchase; join brings all "
            "completed orders and aggregates by cohort month."
        ),
        "alternate_solution": None,
        "key_concepts": ["cohort analysis", "CTE", "DATE_TRUNC"],
        "hints": ["Define cohort from MIN(order_date) of completed orders.", "Sum all completed revenue for cohort members."],
        "sample_expected_rows": [["2024-01-01", 2, 350]],
        "estimated_time_seconds": 780,
        "tables": [
            {
                "table_name": "cohort_orders",
                "display_name": None,
                "description": None,
                "sort_order": 0,
                "columns": [
                    {"column_name": "order_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 0},
                    {"column_name": "customer_id", "data_type": "INTEGER", "is_nullable": False, "sort_order": 1},
                    {"column_name": "order_date", "data_type": "DATE", "is_nullable": False, "sort_order": 2},
                    {"column_name": "amount", "data_type": "INTEGER", "is_nullable": False, "sort_order": 3},
                    {"column_name": "status", "data_type": "TEXT", "is_nullable": False, "sort_order": 4},
                ],
                "rows": [
                    {"order_id": 1, "customer_id": 1, "order_date": "2024-01-10", "amount": 100, "status": "completed"},
                    {"order_id": 2, "customer_id": 1, "order_date": "2024-02-05", "amount": 50, "status": "completed"},
                    {"order_id": 3, "customer_id": 2, "order_date": "2024-01-20", "amount": 200, "status": "completed"},
                    {"order_id": 4, "customer_id": 3, "order_date": "2024-02-02", "amount": 80, "status": "completed"},
                    {"order_id": 5, "customer_id": 3, "order_date": "2024-03-01", "amount": 120, "status": "completed"},
                    {"order_id": 6, "customer_id": 4, "order_date": "2024-02-15", "amount": 90, "status": "cancelled"},
                    {"order_id": 7, "customer_id": 4, "order_date": "2024-02-18", "amount": 70, "status": "completed"},
                ],
            }
        ],
        # customer 1 first Jan -> 100+50=150; customer 2 first Jan -> 200; Jan cohort: 2 cust, 350
        # customer 3 first Feb -> 80+120=200; customer 4 first Feb (completed) -> 70; Feb: 2 cust, 270
        "expected_rows": [
            ["2024-01-01", 2, 350],
            ["2024-02-01", 2, 270],
        ],
    },
]
