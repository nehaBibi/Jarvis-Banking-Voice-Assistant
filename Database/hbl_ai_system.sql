-- =========================
-- DATABASE CREATION
-- =========================
CREATE DATABASE IF NOT EXISTS ai_banking_system;
USE ai_banking_system;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- FINANCING PRODUCTS TABLE
-- =========================
CREATE TABLE financing_products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(120),
    category VARCHAR(60),
    min_income INT,
    max_tenure_months INT,
    description TEXT,
    markup_type VARCHAR(50)
);

-- =========================
-- USER QUERIES TABLE (CHAT LOGS)
-- =========================
CREATE TABLE user_queries (
    query_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    message TEXT,
    intent VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- =========================
-- RESPONSES TABLE
-- =========================
CREATE TABLE responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    query_id INT,
    product_id INT NULL,
    response_text TEXT,
    confidence FLOAT,
    FOREIGN KEY (query_id) REFERENCES user_queries(query_id),
    FOREIGN KEY (product_id) REFERENCES financing_products(product_id)
);

-- =========================
-- SAMPLE USERS
-- =========================
INSERT INTO users (full_name, email, phone) VALUES
('Ali Raza', 'ali@gmail.com', '03001234567'),
('Sara Khan', 'sara@gmail.com', '03019876543'),
('Usman Tariq', NULL, '03121234567'),
('Hina Ahmed', 'hina@gmail.com', NULL),
('Ahmed Ali', 'ahmed@test.com', '03211234567');

-- =========================
-- FINANCING PRODUCTS
-- =========================
INSERT INTO financing_products
(product_name, category, min_income, max_tenure_months, description, markup_type)
VALUES

('Car Loan', 'Auto Financing', 50000, 84,
'Financing for new and used vehicles with flexible repayment options', 'Variable'),

('Home Loan', 'Housing Finance', 80000, 240,
'Loan for buying, constructing, or renovating houses', 'Fixed/Variable'),

('Personal Loan', 'Consumer Finance', 30000, 60,
'Quick cash loan for personal needs like medical or education', 'Fixed'),

('Business Loan', 'SME Financing', 100000, 120,
'Working capital and business expansion financing', 'Negotiable'),

('Education Loan', 'Student Finance', 20000, 72,
'Tuition fee and education-related expenses financing', 'Low Markup'),

('Islamic Financing', 'Shariah Finance', 40000, 180,
'Shariah-compliant financing for personal and business needs', 'Profit Based'),

('Auto Lease', 'Vehicle Leasing', 50000, 84,
'Car leasing with option of ownership at end of term', 'Lease-Based'),

('Emergency Loan', 'Instant Finance', 30000, 24,
'Fast approval emergency cash support', 'High Markup');

-- =========================
-- USER QUERIES
-- =========================
INSERT INTO user_queries (user_id, message, intent) VALUES
(1, 'I need a car loan', 'loan_request'),
(2, 'Tell me about home financing', 'loan_info'),
(3, 'Can I get a personal loan?', 'loan_request'),
(4, 'business funding options', 'loan_info'),
(5, 'emergency cash needed', 'loan_request');

-- =========================
-- RESPONSES
-- =========================
INSERT INTO responses (query_id, product_id, response_text, confidence) VALUES

(1, 1, 'Car Loan offers flexible repayment for new and used vehicles', 0.92),
(2, 2, 'Home Loan supports long-term housing finance up to 20 years', 0.95),
(3, 3, 'Personal Loan provides quick cash with fixed installment plans', 0.89),
(4, 4, 'Business Loan supports SMEs with flexible repayment options', 0.93),
(5, 8, 'Emergency Loan provides fast cash support with quick approval', 0.90);