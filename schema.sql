-- PostgreSQL schema for medicine search system

-- Create medicines table
CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    sku_id VARCHAR(255) UNIQUE,
    name VARCHAR(500) NOT NULL,
    manufacturer_name VARCHAR(500),
    marketer_name VARCHAR(500),
    type VARCHAR(100),
    price DECIMAL(10,2),
    pack_size_label VARCHAR(255),
    short_composition TEXT,
    is_discontinued BOOLEAN DEFAULT FALSE,
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for different search types

-- Prefix search index (using btree for LIKE queries)
CREATE INDEX idx_name_prefix ON medicines (name text_pattern_ops);
CREATE INDEX idx_manufacturer_prefix ON medicines (manufacturer_name text_pattern_ops);

-- Full-text search index
CREATE INDEX idx_name_fts ON medicines USING GIN (to_tsvector('english', name));
CREATE INDEX idx_composition_fts ON medicines USING GIN (to_tsvector('english', short_composition));

-- Trigram indexes for fuzzy search and substring search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_name_trgm ON medicines USING GIN (name gin_trgm_ops);
CREATE INDEX idx_composition_trgm ON medicines USING GIN (short_composition gin_trgm_ops);

-- Additional indexes for performance
CREATE INDEX idx_type ON medicines (type);
CREATE INDEX idx_available ON medicines (available);
CREATE INDEX idx_discontinued ON medicines (is_discontinued);
