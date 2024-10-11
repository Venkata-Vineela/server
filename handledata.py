import sqlite3
import mysql.connector
import os

def get_db_connection():
    connection = mysql.connector.connect(
        user='root',  # Default MySQL user
        password='',  # No password
        host=os.environ.get('DB_HOST', '34.16.53.160'),  # Use the public IP address
        database=os.environ.get('DB_NAME', '')  # Leave blank if not created yet
    )
    return connection


def add_user(firstname, lastname, username, password, phone, organization, street_address, city, state, zipcode):
    """
    Add a user to the user data.
    """

    conn = get_db_connection()
    
    cursor = conn.cursor()
    cursor.execute('''
            INSERT INTO users (
                firstname, lastname, username, password, phone, organization, street_address, city, state, zipcode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (firstname, lastname, username, password, phone, organization, street_address, city, state, zipcode))
    conn.commit()
    conn.close()

def check_user(username):
    """
    Check if the provided username and password are valid.
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def authenticate(username, password):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the provided username and password match a user record in the database
    cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    conn.close()

    # If a user is found, return True (authenticated); otherwise, return False
    return result is not None


def getunames(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, firstname FROM users WHERE firstname LIKE ? LIMIT 4', ('%' + query + '%',))
    # suggested_usernames = [row[0] for row in cursor.fetchall()]


    searchres_usernames = [{'username': row[0], 'firstname': row[1]} for row in cursor.fetchall()]
    conn.close()


    return searchres_usernames

def get_user_data(username):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT firstname, lastname, organization FROM users WHERE username = ?', (username,))
    user_data = [{'firstname': row[0], 'lastname': row[1], 'organization': row[2]} for row in cursor.fetchall()]
    conn.close()

    return user_data;

def get_userprofile_data(username):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT firstname, lastname, organization, street_address, city, state, zipcode FROM users WHERE username = ?', (username,))
    user_data = [{'firstname': row[0], 'lastname': row[1], 'organization': row[2], 'street_address': row[3], 'city': row[4], 'state': row[5], 'zipcode': row[6]} for row in cursor.fetchall()]
    conn.close()

    return user_data;


def get_uname_suggestions(username):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT organization,zipcode FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()

    if row:
        organization, zipcode = row

        # Query for suggestions
        cursor.execute('''
                    SELECT username, firstname FROM users
                    WHERE (organization = ? AND username != ?) 
                     OR 
                     (zipcode = ? AND username != ?)
                    LIMIT 10
                  ''', (organization, username, zipcode, username))

        suggestions = [{'username': row[0], 'firstname': row[1]} for row in cursor.fetchall()]

    conn.close()
    return suggestions

def get_requests(username):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM friendrequests WHERE friendusername = ?', (username,))
    row = cursor.fetchone()

    if row:
        username = row[0]

        # Query for suggestions
        cursor.execute('''SELECT username, firstname FROM users WHERE username = ?''', (username,))


        requests = [{'username': row[0], 'firstname': row[1]} for row in cursor.fetchall()]

    conn.close()
    return requests



def add_friend_connection(username, friendusername):
    username = username.strip()
    friendusername = friendusername.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the friend connection into the 'friends' table
    result = cursor.execute("INSERT INTO friends (username, friendusername) VALUES (?, ?)", (username, friendusername))
    print(result.lastrowid)
    if result.lastrowid > 0:
        conn.commit()
        cursor.execute("DELETE FROM friendrequests WHERE username = ? AND friendusername = ?", (friendusername, username))
        conn.commit()

        conn.close()
        # Return True to indicate a successful insertion
        return True
    else:
        # Return False to indicate insertion failed
        conn.rollback()
        conn.close()
        return False

def add_friend_request(username, friendusername):
    username = username.strip()
    friendusername = friendusername.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the friend connection into the 'friends' table
    result = cursor.execute("INSERT INTO friendrequests (username, friendusername) VALUES (?, ?)", (username, friendusername))

    if result.rowcount > 0:
        conn.commit()
        conn.close()
        # Return True to indicate a successful insertion
        return True
    else:
        # Return False to indicate insertion failed
        conn.rollback()
        conn.close()
        return False

def remove_friend_connection(username, friendusername):
    username = username.strip()
    friendusername = friendusername.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the friend connection from the 'friends' table
    result = cursor.execute("DELETE FROM friends WHERE (username = ? AND friendusername = ?) OR (username = ? AND friendusername = ?)",
                            (username, friendusername, friendusername, username))

    if result.rowcount > 0:
        conn.commit()
        conn.close()
        # Return True to indicate a successful removal
        return True
    else:
        # Return False to indicate removal failed
        conn.rollback()
        conn.close()
        return False


def friendstatus(username, friendusername):
    username = username.strip()
    friendusername = friendusername.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if they are friends
    cursor.execute("""SELECT * FROM friends 
                      WHERE (username = ? AND friendusername = ?)""",
                   (username, friendusername))

    result1 = cursor.fetchone()
    isfriend = result1 is not None

    # Check if a friend request has been sent
    cursor.execute("SELECT * FROM friendrequests WHERE (username = ? AND friendusername = ?) ", (username, friendusername))
    result2 = cursor.fetchone()
    isrequested = result2 is not None

    status = {
        'isfriend': isfriend,
        'isrequested': isrequested
    }

    conn.close()

    return status

def getpostnumber(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Count the number of posts for the given username
    postcount = cursor.execute('SELECT COUNT(*) FROM posts WHERE username = ?', (username,))
    result = cursor.fetchone()[0]
    conn.close()
    postcount = result + 1
    return postcount

def addpost(username,postnumber, text, file_data, file_name, file_type, visibility):
    conn = get_db_connection()
    cursor = conn.cursor()
   
    try:
        cursor.execute('''
            INSERT INTO posts (username, postnumber, text, file_data, file_name, file_type, visibility) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, postnumber, text, file_data, file_name, file_type, visibility))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
        
def getposts(username):
    username = username.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT postnumber, text, file_data, file_name, file_type FROM posts WHERE username = ?', (username,))
    posts = []

    for row in cursor:
        post = {
            'postnumber': row[0],
            'text': row[1],
            'file_data': row[2],
            'file_name': row[3],
            'file_type': row[4]
        }
        posts.append(post)

    conn.close()

    return posts
