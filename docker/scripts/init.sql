-- Initialize Ops Assistant Database

CREATE DATABASE IF NOT EXISTS ops_assistant;
USE ops_assistant;

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    department VARCHAR(100),
    service VARCHAR(100),
    level VARCHAR(20),
    tags JSON,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    INDEX idx_department (department),
    INDEX idx_service (service),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    chunk_index INT NOT NULL,
    page_number INT,
    start_char INT,
    end_char INT,
    vector_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document_id (document_id),
    INDEX idx_vector_id (vector_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(255),
    metadata_filter JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    sources JSON,
    query TEXT,
    rewritten_query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge base statistics view
CREATE OR REPLACE VIEW kb_stats AS
SELECT
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(dc.id) as total_chunks,
    SUM(d.file_size) as total_size_bytes,
    JSON_OBJECTAGG(d.department, dept_count.count) as departments,
    JSON_OBJECTAGG(d.service, svc_count.count) as services
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id
LEFT JOIN (
    SELECT department, COUNT(*) as count
    FROM documents
    GROUP BY department
) dept_count ON d.department = dept_count.department
LEFT JOIN (
    SELECT service, COUNT(*) as count
    FROM documents
    GROUP BY service
) svc_count ON d.service = svc_count.service;
