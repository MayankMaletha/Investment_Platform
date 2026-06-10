-- Initial DB setup script run by PostgreSQL on first start
-- The actual schema is managed by SQLAlchemy/Alembic
-- This script creates extensions and sets locale defaults

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fast text search

-- Set timezone for all connections
ALTER DATABASE investment_agent SET timezone TO 'UTC';
