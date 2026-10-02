-- MySQL schema for the Research Opportunity Portal.
-- Run once:  mysql -u root -p < schema.sql
-- On a cloud MySQL host, skip the CREATE DATABASE/USE lines if the database
-- already exists. (The app also creates the table automatically if missing.)
-- NOTE: no sample rows are inserted. All data is entered through the app.



CREATE DATABASE IF NOT EXISTS research_portal
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE research_portal;

CREATE TABLE IF NOT EXISTS opportunities (
    id               INT UNSIGNED  NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(200)  NOT NULL,
    description      TEXT          NOT NULL,
    research_area    VARCHAR(100)  NOT NULL,
    faculty_name     VARCHAR(100)  NOT NULL,
    department       VARCHAR(100)  NOT NULL,
    required_skills  VARCHAR(500)  NOT NULL,
    positions        INT UNSIGNED  NOT NULL,
    deadline         DATE          NOT NULL,
    status           ENUM('Open','Closed') NOT NULL DEFAULT 'Open',
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_deadline (deadline)
) ENGINE=InnoDB;
