DROP TABLE IF EXISTS cities;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT,
    country TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    FOREIGN KEY (country) REFERENCES countries(code)
);

CREATE INDEX idx_cities_name ON cities(name);
CREATE INDEX idx_cities_country ON cities(country);
