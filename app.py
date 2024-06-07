import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

DB_HOST = "localhost"
DB_NAME = "Good Reading Book Store"
DB_USER = "postgres"
DB_PASS = "xxxxxx"

# load_dotenv()
conn = psycopg2.connect(database=DB_NAME, host=DB_HOST, user=DB_USER, password=DB_PASS, port="5432")

app = Flask(__name__)

@app.get('/')
def home():
    return 'Hello, I am testing REST API for Good Reading Bookstore!'

@app.route('/search_books_by_author', methods=['GET'])
def search_books_by_author():
    author_name = request.args.get('authorname')
    
    if not author_name:
        return jsonify({'error': 'authorname parameter is required'}), 400
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = """
        SELECT 
            b.title,
            a.authorname,
            i.quantity,
            i.priceperbook_rupiah,
            s.storename
        FROM 
            books b
        JOIN 
            inventory i ON b.bookid = i.bookid
        JOIN 
            authors a ON b.authorid = a.authorid
        JOIN 
            store s ON i.storeid = s.storeid
        WHERE 
            a.authorname = %s
    """
    cur.execute(query, (author_name,))
    books = cur.fetchall()

    # Format the output with notes
    formatted_books = []
    for book in books:
        formatted_books.append({
            'book title': book['title'],
            'author': book['authorname'],
            'quantity': book['quantity'],
            'price (Rp.)': book['priceperbook_rupiah'],
            'store': book['storename']
        })

    return jsonify(formatted_books), 200

@app.route('/add_book_to_wishlist', methods=['POST'])
def add_book_to_wishlist():
    # Get the book title, username, and store name from the request query parameters
    book_title = request.args.get('title')
    username = request.args.get('username')
    store_name = request.args.get('storename')

    if not book_title or not username or not store_name:
        return jsonify({'error': 'All parameters book title, storename, and username are required parameters'}), 400

    cur = conn.cursor()

    try:
        # Retrieve the book's bookid from the books table
        cur.execute("SELECT bookid FROM books WHERE title = %s", (book_title,))
        book = cur.fetchone()
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        book_id = book[0]

        # Retrieve the storeid for the given store name
        cur.execute("SELECT storeid FROM store WHERE storename = %s", (store_name,))
        store = cur.fetchone()
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        store_id = store[0]

        # Retrieve the accountid for the given username
        cur.execute("SELECT accountid FROM account WHERE username = %s", (username,))
        account = cur.fetchone()
        if not account:
            return jsonify({'error': 'User not found'}), 404
        account_id = account[0]

        # Retrieve the wishlistid for the user from accountid
        cur.execute("SELECT wishlistid FROM wishlist WHERE accountid = %s", (account_id,))
        wishlist = cur.fetchone()
        if not wishlist:
            return jsonify({'error': 'Wishlist not found'}), 404
        wishlist_id = wishlist[0]

        # Retrieve the inventoryid for the book and store
        cur.execute("SELECT inventoryid FROM inventory WHERE bookid = %s AND storeid = %s", (book_id, store_id))
        inventory_item = cur.fetchone()
        if not inventory_item:
            return jsonify({'error': 'Inventory item not found'}), 404
        inventory_id = inventory_item[0]

        # Insert the inventory item into the wishlist
        cur.execute("INSERT INTO inventory_wishlist (inventoryid, wishlistid) VALUES (%s, %s)", (inventory_id, wishlist_id))
        conn.commit()
        return jsonify({'message': 'Book added to wishlist successfully'}), 201

    except Exception as e:
        # Roll back the transaction in case of an error
        conn.rollback()
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()

@app.route('/stores_information', methods=['GET'])
def get_stores():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Query to retrieve storename, city, and branchnumber
    cur.execute("SELECT storename, city, branchnumber FROM store")
    stores = cur.fetchall()

    # Convert the result to a list of dictionaries
    store_list = []
    for store in stores:
        store_dict = {
            'storename': store['storename'],
            'city': store['city'],
            'branchnumber': store['branchnumber']
        }
        store_list.append(store_dict)
    
    return jsonify(store_list), 200

@app.route('/update_password', methods=['POST'])
def update_password():
    # Get the current username, current password, and new password from the request query parameters
    username = request.args.get('username')
    current_password = request.args.get('current_password')
    new_password = request.args.get('new_password')

    # Check if all required parameters are provided
    if not username or not current_password or not new_password:
        return jsonify({'error': 'Username, current password, and new password are required parameters'}), 400

    # Retrieve the current password associated with the provided username
    cur = conn.cursor()
    cur.execute("SELECT passwordaccount FROM account WHERE username = %s", (username,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'Username not found'}), 404
    current_db_password = row[0]

    # Verify if the provided current password matches the password associated with the username
    if current_password != current_db_password:
        return jsonify({'error': 'Incorrect current password'}), 401

    # Update the password for the user
    cur.execute("UPDATE account SET passwordaccount = %s WHERE username = %s", (new_password, username))
    conn.commit()

    return jsonify({'message': 'Password updated successfully'}), 200

@app.route('/accounts_information', methods=['GET'])
def get_accounts():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Query to retrieve username and passwordaccount
    cur.execute("SELECT username, passwordaccount FROM account")
    accounts = cur.fetchall()

    # Convert the result to a list of dictionaries
    account_list = []
    for account in accounts:
        account_dict = {
            'passwordaccount': account['passwordaccount'],
            'username': account['username']
        }
        account_list.append(account_dict)
    
    return jsonify(account_list), 200

@app.route('/create_account', methods=['POST'])
def create_account():
    # Get the first name, last name, username, and password from the request query parameters
    firstname = request.args.get('firstname')
    lastname = request.args.get('lastname')
    username = request.args.get('username')
    passwordaccount = request.args.get('password')

    if not firstname or not lastname or not username or not passwordaccount:
        return jsonify({'error': 'All parameters firstname, lastname, username, and password are required'}), 400

    cur = conn.cursor()
    
    try:
        # Insert the new customer into the customer table
        cur.execute("INSERT INTO customer (firstname, lastname) VALUES (%s, %s) RETURNING customerid", (firstname, lastname))
        customer_id = cur.fetchone()[0]
        
        # Insert the new account into the account table with the new customerid
        cur.execute("INSERT INTO account (username, passwordaccount, customerid) VALUES (%s, %s, %s) RETURNING accountid", (username, passwordaccount, customer_id))
        account_id = cur.fetchone()[0]

        # Insert a new wishlist entry for the new account
        cur.execute("INSERT INTO wishlist (accountid) VALUES (%s) RETURNING wishlistid", (account_id,))
        wishlist_id = cur.fetchone()[0]
        
        # Commit the transaction
        conn.commit()
        
        return jsonify({'message': 'Account created successfully', 'accountid': account_id, 'customerid': customer_id, 'wishlistid': wishlist_id}), 201
    
    except Exception as e:
        # Roll back the transaction in case of an error
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    # Get the username and password from the request query parameters
    username = request.args.get('username')
    passwordaccount = request.args.get('password')

    if not username or not passwordaccount:
        return jsonify({'error': 'Both username and password are required parameters'}), 400

    cur = conn.cursor()
    
    try:
        # Retrieve the accountid for the given username and password
        cur.execute("SELECT accountid FROM account WHERE username = %s AND passwordaccount = %s", (username, passwordaccount))
        account = cur.fetchone()
        if not account:
            return jsonify({'error': 'User not found or incorrect password'}), 404
        account_id = account[0]

        # Retrieve the wishlistid for the account
        cur.execute("SELECT wishlistid FROM wishlist WHERE accountid = %s", (account_id,))
        wishlist = cur.fetchone()
        if not wishlist:
            return jsonify({'error': 'Wishlist not found'}), 404
        wishlist_id = wishlist[0]

        # Delete the entries in inventory_wishlist associated with the wishlistid
        cur.execute("DELETE FROM inventory_wishlist WHERE wishlistid = %s", (wishlist_id,))

        # Delete the wishlist entry
        cur.execute("DELETE FROM wishlist WHERE wishlistid = %s", (wishlist_id,))

        # Delete the account entry
        cur.execute("DELETE FROM account WHERE accountid = %s", (account_id,))

        # Commit the transaction
        conn.commit()
        
        return jsonify({'message': 'Account deleted successfully'}), 200

    except Exception as e:
        # Roll back the transaction in case of an error
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
