@app.route('/search_books_by_author', methods=['GET'])
def search_books_by_author():
    author_id = request.args.get('authorid')
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = """
        SELECT 
            b.title,
            i.*
        FROM 
            books b
        JOIN 
            inventory i ON b.bookid = i.bookid
        WHERE 
            b.authorid = %s

    """
    cur.execute(query, (author_id,))
    books = cur.fetchall()
    return jsonify(books)