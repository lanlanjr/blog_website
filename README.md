# Flask Web Application with CRUD and User Management

A Flask web application with user authentication, role-based access control, and CRUD operations.

## Features

- User authentication (login, registration, logout)
- Role-based access control (admin vs. regular users)
- CRUD operations for posts
- Admin features (managing users, viewing all posts)
- User features (creating, updating, deleting own posts)

## Setup and Installation

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```
   python init_db.py
   ```
4. Run the application:
   ```
   python run.py
   ```

5. Access the application at `http://localhost:5000`

## Default Admin Account

- Email: admin@example.com
- Password: admin123

## License

This project is licensed under the MIT License - see the LICENSE file for details. 