-- INSIGHT IQ — MySQL schema (Phases 1-8)
-- Run this once against an empty database if you prefer to create tables
-- manually instead of letting SQLAlchemy's db.create_all() do it for you.
--
-- Usage:
--   mysql -u root -p -e "CREATE DATABASE insightiq CHARACTER SET utf8mb4;"
--   mysql -u root -p insightiq < schema.sql
--
-- Note: db.create_all() (used automatically on every app startup) will
-- always match models.py exactly. This file is a convenience for people
-- who want to provision the schema by hand instead, and is kept in sync
-- with models.py as of Phase 8.

CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120) NOT NULL,
    company_name    VARCHAR(150) NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS datasets (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    user_id                 INT NOT NULL,

    original_filename       VARCHAR(255) NOT NULL,
    stored_filename         VARCHAR(255) NOT NULL UNIQUE,
    file_extension          VARCHAR(10) NOT NULL,
    file_size_bytes         INT NOT NULL,
    row_count               INT NULL,
    column_count            INT NULL,
    columns_preview         JSON NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'uploaded',

    -- Phase 2: validation
    validation_report       JSON NULL,
    validated_at            DATETIME NULL,

    -- Phase 2: cleaning
    cleaning_summary        JSON NULL,
    cleaned_filename        VARCHAR(255) NULL,
    cleaned_row_count       INT NULL,
    cleaned_column_count    INT NULL,
    cleaned_at              DATETIME NULL,

    -- Phase 3: exploratory data analysis
    eda_report               JSON NULL,
    eda_at                   DATETIME NULL,

    -- Phase 5: predictive analytics
    predictive_report        JSON NULL,
    predictive_at            DATETIME NULL,

    -- Phase 6: business insights
    insights_report          JSON NULL,
    insights_at              DATETIME NULL,

    uploaded_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_datasets_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_datasets_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Phase 8: Ask INSIGHT IQ conversation history
CREATE TABLE IF NOT EXISTS chat_messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id      INT NOT NULL,
    role            VARCHAR(10) NOT NULL,   -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_messages_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
        ON DELETE CASCADE,
    INDEX idx_chat_messages_dataset (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
