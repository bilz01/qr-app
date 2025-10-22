import qrcode
from PIL import Image
import mysql.connector
from mysql.connector import Error
import uuid
import os
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, BASE_URL

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

def generate_qr_code(qr_id, description, base_url=None):
    """
    Generate a QR code that points to the verification URL
    """
    # Create the verification URL - IMPORTANT: Use the full path with /qr-app/
    if base_url is None:
        base_url = BASE_URL
    verification_url = f"{base_url}/verify/{qr_id}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Create output directory if it doesn't exist
    os.makedirs('qr_codes', exist_ok=True)
    
    # Save the QR code
    filename = f"qr_codes/{qr_id}.png"
    img.save(filename)
    
    print(f"QR code generated: {filename}")
    print(f"Verification URL: {verification_url}")
    
    return filename

def save_to_database(qr_id, description):
    """
    Save QR code information to database
    """
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "INSERT INTO qr_codes (qr_id, description) VALUES (%s, %s)"
        cursor.execute(query, (qr_id, description))
        connection.commit()
        
        print(f"QR code saved to database with ID: {qr_id}")
        return True
    
    except Error as e:
        print(f"Error saving to database: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def main():
    """
    Main function to generate QR codes based on user input
    """
    print("=== QR Code Generator ===")
    print(f"Base URL: {BASE_URL}")
    
    while True:
        print("\n1. Generate new QR code")
        print("2. Exit")
        choice = input("Choose an option (1-2): ").strip()
        
        if choice == '2':
            break
        elif choice == '1':
            # Get user input
            description = input("Enter description for the QR code: ").strip()
            
            if not description:
                print("Description cannot be empty!")
                continue
            
            # Generate unique ID
            qr_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
            
            # Save to database
            if save_to_database(qr_id, description):
                # Generate QR code
                generate_qr_code(qr_id, description)
                
                print(f"\n✅ QR Code generated successfully!")
                print(f"📝 Description: {description}")
                print(f"🆔 Unique ID: {qr_id}")
                print(f"🌐 Verification URL: https://www.nid-library.com/qr-app/verify/{qr_id}")
            else:
                print("❌ Failed to save QR code to database!")
        
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()