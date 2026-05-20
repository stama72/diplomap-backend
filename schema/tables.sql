-- Schema copy for deployment (tracked)
-- This is a copy of memo/database/tables.sql so the schema is available when memo/ is gitignored.

-- ========================================
-- System Tables
-- ========================================

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) UNIQUE NOT NULL,
    display_name  VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20) NOT NULL DEFAULT 'editor',
    email         VARCHAR(255) UNIQUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW(),
    CONSTRAINT role_check CHECK (role IN ('admin', 'reviewer', 'editor', 'viewer'))
);


-- ========================================
-- Geographic & Political Entities
-- ========================================

CREATE TABLE points (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    name_ja    VARCHAR(255) NOT NULL,
    lat        NUMERIC(10, 6) NOT NULL,
    lng        NUMERIC(10, 6) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_points_name ON points(name);


CREATE TABLE countries (
    iso_id     VARCHAR(16) PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    name_ja    VARCHAR(255) NOT NULL,
    capital_point_id INTEGER REFERENCES points(id),
    exist_from DATE,
    exist_until DATE,
    summary    TEXT,
    summary_jp TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_countries_name ON countries(name);

-- 以下未実装
CREATE TABLE international_orgs (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL,
    name_ja              VARCHAR(255) NOT NULL,
    headquarters_point_id INTEGER NOT NULL REFERENCES points(id),
    exist_from           DATE,
    exist_until          DATE,
    summary              TEXT,
    summary_jp           TEXT,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_international_orgs_name ON international_orgs(name);


CREATE TABLE member_countries (
    id                SERIAL PRIMARY KEY,
    org_id            INTEGER NOT NULL REFERENCES international_orgs(id),
    country_id        VARCHAR(255) NOT NULL REFERENCES countries(iso_id),
    joined_at         DATE,
    belonged_to_until DATE,
    status            VARCHAR(50),
    status_jp         VARCHAR(50),
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE(org_id, country_id, joined_at)
);

CREATE INDEX idx_member_countries_org_id ON member_countries(org_id);
CREATE INDEX idx_member_countries_country_id ON member_countries(country_id);


CREATE TABLE member_orgs (
    id                SERIAL PRIMARY KEY,
    greater_org_id    INTEGER NOT NULL REFERENCES international_orgs(id),
    member_org_id     INTEGER NOT NULL REFERENCES international_orgs(id),
    joined_at         DATE,
    belonged_to_until DATE,
    status            VARCHAR(50),
    status_jp         VARCHAR(50),
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW(),
    CONSTRAINT no_self_membership CHECK (greater_org_id <> member_org_id)
);

CREATE INDEX idx_member_orgs_greater_org_id ON member_orgs(greater_org_id);
CREATE INDEX idx_member_orgs_member_org_id ON member_orgs(member_org_id);


CREATE TABLE local_forces (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL,
    name_ja              VARCHAR(255) NOT NULL,
    headquarters_point_id INTEGER REFERENCES points(id),
    exist_from           DATE,
    exist_until          DATE,
    summary              TEXT,
    summary_jp          TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_local_forces_name ON local_forces(name);


-- ========================================
-- Maps & Links (Visualizations)
-- ========================================

CREATE TABLE maps (
    id                   SERIAL PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL,
    name_ja              VARCHAR(255) NOT NULL,
    owner                INTEGER NOT NULL REFERENCES users(id),
    read_permission      VARCHAR(20) NOT NULL,
    edit_permission      VARCHAR(20) NOT NULL,
    exist_from           DATE NOT NULL,
    exist_until          DATE NOT NULL,
    time_scale           VARCHAR(20) NOT NULL,
    summary              TEXT,
    summary_jp           TEXT,
    regulations          TEXT,
    source_url           TEXT,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW(),
    CONSTRAINT permission_check CHECK (
        read_permission IN ('private', 'shared', 'public')
        AND edit_permission IN ('private', 'shared', 'public')
    ),
    CONSTRAINT time_scale_check CHECK (
        time_scale IN ('hundred_years', 'ten_years', 'five_years', 'one_year', 'one_month', 'one_week', 'one_day')
    )
);

CREATE INDEX idx_maps_owner ON maps(owner);

CREATE TABLE map_points (
    id       SERIAL PRIMARY KEY,
    map_id   INTEGER NOT NULL REFERENCES maps(id),
    point_id INTEGER NOT NULL REFERENCES points(id),
    color    VARCHAR(16),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(map_id, point_id)
);

CREATE TABLE link_types (
    id        SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_ja VARCHAR(255) NOT NULL,
    map_id    INTEGER NOT NULL REFERENCES maps(id),
    color     VARCHAR(16),
    animated  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_link_types_map_id ON link_types(map_id);


CREATE TABLE links (
    id            SERIAL PRIMARY KEY,
    map_id        INTEGER NOT NULL REFERENCES maps(id),
    link_type     INTEGER NOT NULL REFERENCES link_types(id),
    point_from    INTEGER NOT NULL REFERENCES points(id),
    point_to      INTEGER NOT NULL REFERENCES points(id),
    exist_from    DATE NOT NULL,
    exist_until   DATE NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(map_id, link_type, point_from, point_to, exist_from)
);

CREATE INDEX idx_links_map_id ON links(map_id);
CREATE INDEX idx_links_point_from ON links(point_from);
CREATE INDEX idx_links_point_to ON links(point_to);
CREATE INDEX idx_links_link_type ON links(link_type);


CREATE TABLE link_details (
    link_id    INTEGER PRIMARY KEY REFERENCES links(id) ON DELETE CASCADE,
    summary    TEXT NOT NULL,
    summary_ja TEXT NOT NULL,
    source_url TEXT,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);
