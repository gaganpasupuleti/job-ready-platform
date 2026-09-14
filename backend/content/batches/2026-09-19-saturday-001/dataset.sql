-- Original synthetic shop. PostgreSQL. Amounts are rupees. No employer source.
CREATE TABLE customers (id int primary key, name text not null, city text not null);
CREATE TABLE orders (
  id int primary key,
  customer_id int not null references customers(id),
  status text not null,
  amount numeric,
  ordered_on date not null
);
CREATE TABLE payments (
  id int primary key,
  order_id int not null references orders(id),
  amount numeric not null,
  paid_on date not null
);
INSERT INTO customers (id, name, city) VALUES
  (1, 'Ada', 'Hyderabad'),
  (2, 'Ben', 'Bengaluru'),
  (3, 'Cho', 'Pune');
INSERT INTO orders (id, customer_id, status, amount, ordered_on) VALUES
  (1, 1, 'paid', 1000, DATE '2026-01-02'),
  (2, 1, 'pending', 500, DATE '2026-01-05'),
  (3, 2, 'paid', 800, DATE '2026-01-03'),
  (4, 2, 'cancelled', 200, DATE '2026-01-04'),
  (5, 3, 'shipped', 1500, DATE '2026-01-06');
INSERT INTO payments (id, order_id, amount, paid_on) VALUES
  (1, 1, 1000, DATE '2026-01-02'),
  (2, 3, 800, DATE '2026-01-04');
