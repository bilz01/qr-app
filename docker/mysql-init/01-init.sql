CREATE DATABASE IF NOT EXISTS qr_verification;
USE qr_verification;

CREATE TABLE IF NOT EXISTS qr_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qr_id VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qr_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(100),
    http_method VARCHAR(10),
    status_code INT,
    country VARCHAR(100),
    city VARCHAR(100),
    browser VARCHAR(100),
    platform VARCHAR(100),
    device_type VARCHAR(50),
    FOREIGN KEY (qr_id) REFERENCES qr_codes(qr_id) ON DELETE SET NULL
);
