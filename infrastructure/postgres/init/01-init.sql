-- PostgreSQL initialization script for Ponder
-- This script sets up the database with required extensions

-- Create the vector extension if available (for pgvector support)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create pg_stat_statements extension for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create uuid extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set up basic configuration
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET pg_stat_statements.max = 10000;

-- Create indexes for better performance (will be created by Alembic migrations)
-- This is just a placeholder for any additional setup needed