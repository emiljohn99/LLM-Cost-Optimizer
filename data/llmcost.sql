-- Database: llm cost

-- DROP DATABASE IF EXISTS "llm cost";

CREATE DATABASE "llm cost"
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_India.1252'
    LC_CTYPE = 'English_India.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    category VARCHAR(30),

    cost_input_per_1m DECIMAL(10,4),
    cost_output_per_1m DECIMAL(10,4),

    avg_latency_ms INT,
    max_context_tokens INT,

    reasoning_score DECIMAL(3,2),
    coding_score DECIMAL(3,2),
    vision_score DECIMAL(3,2),

    supports_vision BOOLEAN,
    supports_function_calling BOOLEAN,
    supports_streaming BOOLEAN,
    supports_json BOOLEAN,

    health_score DECIMAL(4,2),
    success_rate DECIMAL(5,2),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


ALTER TABLE models
ALTER COLUMN reasoning_score TYPE DECIMAL(4,2);

ALTER TABLE models
ALTER COLUMN coding_score TYPE DECIMAL(4,2);

ALTER TABLE models
ALTER COLUMN vision_score TYPE DECIMAL(4,2);


ALTER TABLE models
ALTER COLUMN health_score TYPE DECIMAL(5,2);

ALTER TABLE models
ALTER COLUMN success_rate TYPE DECIMAL(5,2);

INSERT INTO models (
    provider,
    model_name,
    category,
    cost_input_per_1m,
    cost_output_per_1m,
    avg_latency_ms,
    max_context_tokens,
    reasoning_score,
    coding_score,
    vision_score,
    supports_vision,
    supports_function_calling,
    supports_streaming,
    supports_json,
    health_score,
    success_rate
)
VALUES

-- =========================
-- OpenAI
-- =========================
('OpenAI','gpt-5','Premium',15.00,60.00,2200,400000,9.9,9.8,9.7,TRUE,TRUE,TRUE,TRUE,99.8,99.9),

('OpenAI','gpt-5-mini','Balanced',2.50,10.00,900,400000,9.1,9.2,9.0,TRUE,TRUE,TRUE,TRUE,99.8,99.8),

('OpenAI','gpt-5-nano','Budget',0.50,2.00,450,128000,7.8,8.0,0.0,FALSE,TRUE,TRUE,TRUE,99.8,99.7),

-- =========================
-- Anthropic
-- =========================
('Anthropic','claude-opus-4','Premium',15.00,75.00,2400,200000,10.0,9.8,9.7,TRUE,TRUE,TRUE,TRUE,99.7,99.8),

('Anthropic','claude-sonnet-4','Balanced',3.00,15.00,1100,200000,9.7,9.8,9.6,TRUE,TRUE,TRUE,TRUE,99.8,99.9),

('Anthropic','claude-haiku-4','Budget',0.80,4.00,500,200000,8.3,8.5,8.2,TRUE,TRUE,TRUE,TRUE,99.8,99.9),

-- =========================
-- Google
-- =========================
('Google','gemini-2.5-pro','Premium',3.50,15.00,1800,1048576,9.8,9.5,9.8,TRUE,TRUE,TRUE,TRUE,99.8,99.8),

('Google','gemini-2.5-flash','Fast',0.35,1.50,500,1048576,8.8,8.5,9.1,TRUE,TRUE,TRUE,TRUE,99.9,99.8),

-- =========================
-- Meta
-- =========================
('Meta','llama-4-maverick','Open Weight',0.00,0.00,900,128000,8.9,9.0,9.1,TRUE,TRUE,TRUE,TRUE,99.6,99.5),

('Meta','llama-4-scout','Open Weight',0.00,0.00,500,1000000,8.2,8.3,8.5,TRUE,TRUE,TRUE,TRUE,99.6,99.5),

-- =========================
-- DeepSeek
-- =========================
('DeepSeek','deepseek-r1','Reasoning',0.55,2.20,1300,128000,9.8,9.7,0.0,FALSE,TRUE,TRUE,TRUE,99.7,99.7),

('DeepSeek','deepseek-v3','General',0.30,1.20,650,128000,9.2,9.2,0.0,FALSE,TRUE,TRUE,TRUE,99.8,99.7),

-- =========================
-- xAI
-- =========================
('xAI','grok-4','Premium',5.00,15.00,1700,256000,9.6,9.4,9.5,TRUE,TRUE,TRUE,TRUE,99.7,99.7),

-- =========================
-- Mistral
-- =========================
('Mistral','mistral-large','Premium',2.00,6.00,900,128000,9.0,9.2,8.7,TRUE,TRUE,TRUE,TRUE,99.7,99.7),

('Mistral','ministral-8b','Small',0.20,0.70,300,128000,7.8,7.9,0.0,FALSE,FALSE,TRUE,TRUE,99.8,99.6),

-- =========================
-- Alibaba
-- =========================
('Alibaba','qwen3-235b','Open Weight',0.00,0.00,1500,256000,9.6,9.3,9.2,TRUE,TRUE,TRUE,TRUE,99.6,99.5),

('Alibaba','qwen3-32b','Open Weight',0.00,0.00,600,256000,8.8,8.7,0.0,FALSE,TRUE,TRUE,TRUE,99.6,99.5),

-- =========================
-- Cohere
-- =========================
('Cohere','command-a','Enterprise',2.50,10.00,800,256000,8.8,8.8,0.0,FALSE,TRUE,TRUE,TRUE,99.7,99.8),

-- =========================
-- Microsoft
-- =========================
('Microsoft','phi-4','Small',0.00,0.00,300,128000,8.1,8.6,0.0,FALSE,FALSE,TRUE,TRUE,99.7,99.7),

-- =========================
-- Moonshot AI
-- =========================
('Moonshot','kimi-k2','Long Context',1.20,6.00,700,1000000,9.1,9.0,9.0,TRUE,TRUE,TRUE,TRUE,99.7,99.8),

-- =========================
-- NVIDIA
-- =========================
('NVIDIA','nemotron-ultra','Enterprise',2.00,8.00,1200,256000,9.0,9.1,0.0,FALSE,TRUE,TRUE,TRUE,99.6,99.6),

-- =========================
-- IBM
-- =========================
('IBM','granite-3.3','Enterprise',0.00,0.00,450,128000,8.2,8.1,0.0,FALSE,FALSE,TRUE,TRUE,99.5,99.5);