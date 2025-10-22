from flask import Flask, request, jsonify, render_template
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, ADMIN_CREDENTIALS
import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime
import requests
import json
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# Basic HTTP Authentication Configuration
# Provide ADMIN_CREDENTIALS as a comma-separated list: "user1:pass1,user2:pass2"
def load_admin_users_from_env(creds_string: str):
    users = {}
    for pair in creds_string.split(','):
        if not pair.strip():
            continue
        if ':' not in pair:
            continue
        username, pwd = pair.split(':', 1)
        users[username.strip()] = generate_password_hash(pwd.strip())
    return users

ADMIN_USERS = load_admin_users_from_env(ADMIN_CREDENTIALS)

def check_auth(username, password):
    """Check if a username/password combination is valid."""
    if username in ADMIN_USERS:
        return check_password_hash(ADMIN_USERS[username], password)
    return False

def authenticate():
    """Send a 401 response that enables basic auth"""
    return jsonify({
        'status': 'error',
        'message': 'Authentication required'
    }), 401, {'WWW-Authenticate': 'Basic realm="Admin Access Required"'}

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Database configuration
db_config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_client_info():
    """Extract client information from request"""
    # Get real IP address (handling proxies)
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    user_agent = request.headers.get('User-Agent', '')
    
    # Simple device/browser detection
    user_agent_lower = user_agent.lower()
    
    # Browser detection
    if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
        browser = 'Chrome'
    elif 'firefox' in user_agent_lower:
        browser = 'Firefox'
    elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
        browser = 'Safari'
    elif 'edg' in user_agent_lower:
        browser = 'Edge'
    else:
        browser = 'Other'
    
    # Platform detection
    if 'windows' in user_agent_lower:
        platform = 'Windows'
    elif 'mac' in user_agent_lower:
        platform = 'Mac'
    elif 'linux' in user_agent_lower:
        platform = 'Linux'
    elif 'android' in user_agent_lower:
        platform = 'Android'
    elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
        platform = 'iOS'
    else:
        platform = 'Unknown'
    
    # Device type
    if 'mobile' in user_agent_lower:
        device_type = 'Mobile'
    elif 'tablet' in user_agent_lower:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    return {
        'ip_address': ip,
        'user_agent': user_agent,
        'browser': browser,
        'platform': platform,
        'device_type': device_type
    }

def get_geo_location(ip_address):
    """Get geographical location from IP address (optional)"""
    try:
        if ip_address not in ['127.0.0.1', 'localhost']:
            response = requests.get(f'http://ipapi.co/{ip_address}/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', 'Unknown'),
                    'city': data.get('city', 'Unknown')
                }
    except:
        pass
    
    return {'country': 'Unknown', 'city': 'Unknown'}

def log_access(qr_id, endpoint, http_method, status_code):
    """Log API access to database"""
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        client_info = get_client_info()
        geo_info = get_geo_location(client_info['ip_address'])
        
        cursor = connection.cursor()
        query = """
        INSERT INTO api_access_logs 
        (qr_id, ip_address, user_agent, endpoint, http_method, status_code, country, city, browser, platform, device_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            qr_id,
            client_info['ip_address'],
            client_info['user_agent'],
            endpoint,
            http_method,
            status_code,
            geo_info['country'],
            geo_info['city'],
            client_info['browser'],
            client_info['platform'],
            client_info['device_type']
        ))
        connection.commit()
        
    except Error as e:
        print(f"Error logging access: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# PUBLIC ROUTES (No authentication required)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/verify/<qr_id>')
def verify_qr(qr_id):
    connection = get_db_connection()
    if connection is None:
        log_access(qr_id, '/verify/' + qr_id, 'GET', 500)
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM qr_codes WHERE qr_id = %s"
        cursor.execute(query, (qr_id,))
        result = cursor.fetchone()
        
        if result:
            log_access(qr_id, '/verify/' + qr_id, 'GET', 200)
            return render_template('verification.html', 
                                 qr_id=qr_id,
                                 description=result['description'],
                                 status='VALID',
                                 created_at=result['created_at'])
        else:
            log_access(qr_id, '/verify/' + qr_id, 'GET', 404)
            return render_template('verification.html', 
                                 qr_id=qr_id,
                                 status='INVALID',
                                 description='QR code not found')
    
    except Error as e:
        log_access(qr_id, '/verify/' + qr_id, 'GET', 500)
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/verify/<qr_id>')
def api_verify_qr(qr_id):
    """API endpoint for JSON response"""
    connection = get_db_connection()
    if connection is None:
        log_access(qr_id, '/api/verify/' + qr_id, 'GET', 500)
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM qr_codes WHERE qr_id = %s"
        cursor.execute(query, (qr_id,))
        result = cursor.fetchone()
        
        if result:
            log_access(qr_id, '/api/verify/' + qr_id, 'GET', 200)
            return jsonify({
                'status': 'success',
                'qr_id': qr_id,
                'description': result['description'],
                'created_at': str(result['created_at']),
                'valid': True
            })
        else:
            log_access(qr_id, '/api/verify/' + qr_id, 'GET', 404)
            return jsonify({
                'status': 'error',
                'message': 'QR code not found',
                'valid': False
            }), 404
    
    except Error as e:
        log_access(qr_id, '/api/verify/' + qr_id, 'GET', 500)
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Add a simple test route
@app.route('/api/test')
def test_api():
    return jsonify({'status': 'success', 'message': 'API is working!'})

# PROTECTED ADMIN ROUTES (Authentication required)
@app.route('/api/access_logs', methods=['GET'])
@requires_auth
def get_access_logs():
    """Get API access logs (for admin purposes)"""
    connection = get_db_connection()
    if connection is None:
        return render_template('admin_error.html', message='Database connection failed'), 500
    
    try:
        # Get query parameters for filtering
        qr_id_filter = request.args.get('qr_id')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        # Sanity limits
        if per_page <= 0:
            per_page = 100
        if per_page > 1000:
            per_page = 1000
        if page <= 0:
            page = 1

        offset = (page - 1) * per_page

        cursor = connection.cursor(dictionary=True)

        # Get total count for pagination
        if qr_id_filter:
            count_query = "SELECT COUNT(*) as cnt FROM api_access_logs WHERE qr_id = %s"
            cursor.execute(count_query, (qr_id_filter,))
            total = cursor.fetchone()['cnt']
            select_query = """
            SELECT * FROM api_access_logs
            WHERE qr_id = %s
            ORDER BY access_time DESC
            LIMIT %s OFFSET %s
            """
            cursor.execute(select_query, (qr_id_filter, per_page, offset))
        else:
            count_query = "SELECT COUNT(*) as cnt FROM api_access_logs"
            cursor.execute(count_query)
            total = cursor.fetchone()['cnt']
            select_query = "SELECT * FROM api_access_logs ORDER BY access_time DESC LIMIT %s OFFSET %s"
            cursor.execute(select_query, (per_page, offset))

        logs = cursor.fetchall()
        
        # Convert datetime objects to strings for template display
        for log in logs:
            if log.get('access_time'):
                log['access_time'] = log['access_time'].isoformat()

        # Pagination metadata
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }

        return render_template('access_logs.html', logs=logs, count=len(logs), qr_id_filter=qr_id_filter, pagination=pagination)
    
    except Error as e:
        return render_template('admin_error.html', message=str(e)), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/access_stats', methods=['GET'])
@requires_auth
def get_access_stats():
    """Get access statistics"""
    connection = get_db_connection()
    if connection is None:
        return render_template('admin_error.html', message='Database connection failed'), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Total scans
        cursor.execute("SELECT COUNT(*) as total_scans FROM api_access_logs")
        total_scans = cursor.fetchone()['total_scans']
        
        # Scans today
        cursor.execute("""
            SELECT COUNT(*) as scans_today 
            FROM api_access_logs 
            WHERE DATE(access_time) = CURDATE()
        """)
        scans_today = cursor.fetchone()['scans_today']
        
        # Unique QR codes scanned
        cursor.execute("SELECT COUNT(DISTINCT qr_id) as unique_qr_codes FROM api_access_logs")
        unique_qr_codes = cursor.fetchone()['unique_qr_codes']
        
        # Most scanned QR codes
        cursor.execute("""
            SELECT qr_id, COUNT(*) as scan_count 
            FROM api_access_logs 
            GROUP BY qr_id 
            ORDER BY scan_count DESC 
            LIMIT 10
        """)
        most_scanned = cursor.fetchall()
        
        # Scans by device type
        cursor.execute("""
            SELECT device_type, COUNT(*) as count 
            FROM api_access_logs 
            GROUP BY device_type
        """)
        device_stats = cursor.fetchall()
        
        # Scans by browser
        cursor.execute("""
            SELECT browser, COUNT(*) as count 
            FROM api_access_logs 
            GROUP BY browser
        """)
        browser_stats = cursor.fetchall()
        
        # Prepare data for template
        return render_template('access_stats.html',
                               total_scans=total_scans,
                               scans_today=scans_today,
                               unique_qr_codes=unique_qr_codes,
                               most_scanned=most_scanned,
                               device_stats=device_stats,
                               browser_stats=browser_stats)
    
    except Error as e:
        return render_template('admin_error.html', message=str(e)), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/qr_codes', methods=['GET'])
@requires_auth
def get_all_qr_codes():
    """Get all QR codes with scan counts"""
    connection = get_db_connection()
    if connection is None:
        return render_template('admin_error.html', message='Database connection failed'), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT qc.*, COUNT(al.id) as scan_count 
        FROM qr_codes qc 
        LEFT JOIN api_access_logs al ON qc.qr_id = al.qr_id 
        GROUP BY qc.id 
        ORDER BY qc.created_at DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Normalize datetimes for display
        for r in results:
            if r.get('created_at'):
                try:
                    r['created_at'] = r['created_at'].isoformat()
                except Exception:
                    pass

        return render_template('qr_codes.html', qr_codes=results, count=len(results))
    
    except Error as e:
        return render_template('admin_error.html', message=str(e)), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Admin test endpoint
@app.route('/api/admin/test')
@requires_auth
def admin_test():
    return jsonify({'status': 'success', 'message': 'Admin access granted!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5040)