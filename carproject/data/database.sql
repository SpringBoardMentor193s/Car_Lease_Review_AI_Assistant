-- Car Project database schema (MySQL)
-- NOTE: SQL only; no execution performed here.

CREATE DATABASE IF NOT EXISTS car_project
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE car_project;

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(32),
    full_name VARCHAR(255),
    auth_provider VARCHAR(64),
    created_at DATETIME,
    updated_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dealers (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(128),
    state VARCHAR(64),
    postal_code VARCHAR(20),
    country VARCHAR(64),
    phone VARCHAR(32),
    website VARCHAR(255),
    created_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lenders (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    nmls_id VARCHAR(64),
    website VARCHAR(255),
    phone VARCHAR(32),
    address VARCHAR(255),
    created_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicles (
    id VARCHAR(64) PRIMARY KEY,
    vin VARCHAR(17) NOT NULL,
    year INT,
    make VARCHAR(64),
    model VARCHAR(64),
    trim VARCHAR(64),
    body_class VARCHAR(64),
    engine VARCHAR(128),
    drivetrain VARCHAR(64),
    fuel_type VARCHAR(64),
    odometer_miles DECIMAL(12,2),
    color_ext VARCHAR(64),
    color_int VARCHAR(64),
    created_at DATETIME,
    updated_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS providers (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(64) NOT NULL,
    is_free TINYINT(1) NOT NULL,
    base_url VARCHAR(255),
    notes TEXT,
    created_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicle_reports (
    id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64) NOT NULL,
    provider_id VARCHAR(64),
    title VARCHAR(255),
    report_type VARCHAR(128),
    availability VARCHAR(64),
    url VARCHAR(500),
    raw LONGTEXT,
    created_at DATETIME,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(provider_id) REFERENCES providers(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicle_recalls (
    id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64) NOT NULL,
    recall_number VARCHAR(64),
    issue_date DATE,
    component VARCHAR(255),
    summary TEXT,
    remedy TEXT,
    source VARCHAR(128),
    raw LONGTEXT,
    created_at DATETIME,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64),
    vehicle_id VARCHAR(64),
    dealer_id VARCHAR(64),
    lender_id VARCHAR(64),
    contract_type VARCHAR(64),
    doc_status VARCHAR(64),
    dealer_offer_name VARCHAR(255),
    contract_date DATE,
    locale VARCHAR(16),
    currency VARCHAR(8),
    fairness_score DOUBLE,
    red_flag_level VARCHAR(32),
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(dealer_id) REFERENCES dealers(id),
    FOREIGN KEY(lender_id) REFERENCES lenders(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contract_files (
    id VARCHAR(64) PRIMARY KEY,
    contract_id VARCHAR(64) NOT NULL,
    storage_uri VARCHAR(500),
    file_name VARCHAR(255),
    mime_type VARCHAR(128),
    page_count INT,
    uploaded_at DATETIME,
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contract_pages (
    id VARCHAR(64) PRIMARY KEY,
    contract_file_id VARCHAR(64) NOT NULL,
    page_number INT NOT NULL,
    ocr_text LONGTEXT,
    ocr_confidence DECIMAL(5,2),
    thumbnail_uri VARCHAR(500),
    created_at DATETIME,
    FOREIGN KEY(contract_file_id) REFERENCES contract_files(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS extractions (
    id VARCHAR(64) PRIMARY KEY,
    contract_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(128),
    prompt_version VARCHAR(64),
    status VARCHAR(32),
    started_at DATETIME,
    completed_at DATETIME,
    raw_output LONGTEXT,
    error_message TEXT,
    FOREIGN KEY(contract_id) REFERENCES contracts(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS extracted_clauses (
    id VARCHAR(64) PRIMARY KEY,
    extraction_id VARCHAR(64) NOT NULL,
    clause_type VARCHAR(64),
    page_number INT,
    text_snippet LONGTEXT,
    normalized_value LONGTEXT,
    red_flag_level VARCHAR(32),
    comment TEXT,
    FOREIGN KEY(extraction_id) REFERENCES extractions(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS negotiation_threads (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64),
    contract_id VARCHAR(64),
    dealer_id VARCHAR(64),
    lender_id VARCHAR(64),
    channel VARCHAR(32),
    subject VARCHAR(255),
    created_at DATETIME,
    closed_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS negotiation_messages (
    id VARCHAR(64) PRIMARY KEY,
    thread_id VARCHAR(64) NOT NULL,
    sender_role VARCHAR(32),
    body LONGTEXT,
    suggested_text LONGTEXT,
    attachments LONGTEXT,
    sent_at DATETIME,
    FOREIGN KEY(thread_id) REFERENCES negotiation_threads(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS price_recommendations (
    id VARCHAR(64) PRIMARY KEY,
    vehicle_id VARCHAR(64) NOT NULL,
    geo_postal VARCHAR(32),
    msrp DECIMAL(12,2),
    fair_price_low DECIMAL(12,2),
    fair_price_high DECIMAL(12,2),
    basis VARCHAR(128),
    methodology VARCHAR(128),
    generated_at DATETIME,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS offer_comparisons (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    primary_contract_id VARCHAR(64) NOT NULL,
    compared_contract_id VARCHAR(64) NOT NULL,
    comparison_json LONGTEXT,
    created_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS integration_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    provider_id VARCHAR(64),
    request_path VARCHAR(255),
    request_params TEXT,
    response_status INT,
    response_ms INT,
    occurred_at DATETIME,
    error_message TEXT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(64),
    entity_table VARCHAR(64),
    entity_id VARCHAR(64),
    action VARCHAR(64),
    details TEXT,
    occurred_at DATETIME
) ENGINE=InnoDB;
