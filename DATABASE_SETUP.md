# Database Setup Guide

## Overview

The Jarvis Banking AI system is designed to work with both **live MySQL databases** and **mock data fallback**. This allows the system to demonstrate functionality even if MySQL is not installed.

## Quick Start

### Option 1: Use Mock Data (Recommended for Quick Testing)

The system will automatically fall back to mock data if MySQL is not available. This allows you to test the full frontend/backend integration immediately.

**No additional setup required!** Just run:

```bash
python app.py
```

The system will:
- ✅ Use mock financing products
- ✅ Route queries intelligently (BFS/A*)
- ✅ Demonstrate full functionality
- ✅ Log to console (mock log entries)

### Option 2: Setup with Real MySQL Database

#### Prerequisites

- MySQL Server 5.7+ or 8.0+
- Python 3.8+
- MySQL connector installed: `pip install mysql-connector-python==8.0.33`

#### Step 1: Install MySQL

**Windows:**
1. Download from https://dev.mysql.com/downloads/mysql/
2. Run the installer and follow the installation wizard
3. Set root password during installation
4. Start MySQL service: `services.msc` → Start "MySQL80" (or your version)

**macOS:**
```bash
brew install mysql
brew services start mysql
mysql -u root
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install mysql-server
sudo mysql_secure_installation
sudo systemctl start mysql
```

#### Step 2: Import Database Schema

After MySQL is running and the server is accessible, run:

```bash
cd "path/to/AI Assistant"
python setup_database.py
```

This will:
- Create the `ai_banking_system` database
- Create all tables (users, financing_products, user_queries, responses)
- Insert 8 sample financing products
- Insert 5 sample users and queries

#### Step 3: Configure Database Connection

Edit `.env` file:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ai_banking_system
```

#### Step 4: Verify Connection

```bash
python -c "from utils.database import DatabaseConnection; conn = DatabaseConnection.get_connection(); print('✅ Connected!' if conn else '❌ Failed')"
```

#### Step 5: Start Backend

```bash
python app.py
```

You'll see:
```
✅ Connected to MySQL database
```

## Database Schema

### Tables

**users**
- `user_id`: int (PK)
- `username`: varchar(50)
- `password_hash`: varchar(255)
- `created_at`: timestamp

**financing_products**
- `product_id`: int (PK)
- `product_name`: varchar(100)
- `category`: varchar(50)
- `description`: text
- `min_income`: int
- `max_tenure_months`: int
- `markup_type`: varchar(50)

**user_queries**
- `query_id`: int (PK)
- `user_id`: int (FK)
- `message`: text
- `intent`: varchar(50)
- `created_at`: timestamp

**responses**
- `response_id`: int (PK)
- `query_id`: int (FK)
- `product_id`: int (FK)
- `response_text`: text
- `confidence`: float
- `created_at`: timestamp

## Sample Products (Included in Mock Data)

1. **Car Financing** - Auto Financing
2. **Home Financing** - Housing Finance  
3. **Personal Loan** - Personal Loan
4. **Business Financing** - SME Financing
5. **Education Financing** - Student Finance

(Plus 3 more: Islamic Financing, Auto Lease, Emergency Loan)

## Troubleshooting

### MySQL Connection Refused (10061)

**Solution:**
- Check if MySQL service is running: `services.msc` on Windows
- Verify credentials in `.env` file
- Default MySQL port is 3306

### "Can't connect to MySQL server"

**Solution:**
```bash
# Windows - Check service status
Get-Service -Name *mysql*

# Linux - Check service
sudo systemctl status mysql

# Restart service
sudo systemctl restart mysql
```

### "Access denied for user 'root'@'localhost'"

**Solution:**
- Check DB_PASSWORD in `.env` file
- Reset MySQL root password if needed

### Database Already Exists

**Solution:**
```bash
mysql -u root -p < Database/hbl_ai_system.sql
```

Or drop and recreate:
```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS ai_banking_system;"
python setup_database.py
```

## Features Working with Mock Data

✅ Query classification (Simple/Complex)
✅ Agent routing (BFS/A*)
✅ Product search and filtering
✅ Recommendation generation
✅ User authentication
✅ Message validation
✅ Response logging (to console)
✅ Full frontend integration

## Features Requiring Live Database

✅ Persistent query logging to database
✅ Response history tracking
✅ User history queries
✅ Analytics on product recommendations
✅ Audit trail storage

## Next Steps

Once MySQL is running:

1. **Import the schema:**
   ```bash
   python setup_database.py
   ```

2. **Start the backend:**
   ```bash
   python app.py
   ```

3. **Open the frontend:**
   - Open `index.html` in a web browser
   - Or serve via: `python -m http.server 8000`
   - Visit: `http://localhost:8000`

4. **Test the system:**
   - Login: `user` / `password`
   - Type: "Tell me about car loans"
   - Watch the system classify, route, and respond!

## Architecture Flow

```
User Query
    ↓
Query Classifier (Simple vs Complex)
    ↓
├─ Simple → BFS Agent (Uninformed Search)
│           ├─ Extract keywords
│           ├─ Query Database
│           └─ Format Response
│
└─ Complex → A* Agent (Informed Search)
            ├─ Analyze requirements
            ├─ Calculate costs & heuristics
            ├─ Find optimal product
            └─ Generate recommendation

    ↓
Database (Live MySQL or Mock)
    ├─ Product lookup
    ├─ Category search
    └─ Response logging

    ↓
Response to User
```

## Performance Notes

- **Mock Mode:** ~10-50ms query time
- **Live MySQL:** ~20-100ms query time (depends on indexing)
- **Recommendation Engine:** ~5-20ms (A* search)

## Security

- Credentials should not be hardcoded
- Use environment variables for sensitive data
- Mock data has no PII protection needed
- Live database should use:
  - Strong root password
  - Dedicated DB user with limited privileges
  - Encrypted connections in production

## Support

For issues or questions:
1. Check system logs: `cat debug-logs/*.log`
2. Test database: `python -c "from utils.database import query_financing_products; print(query_financing_products())"`
3. Verify imports: `python -c "from app import app; print('✅ OK')"`
