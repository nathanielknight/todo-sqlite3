-- todo-sqlite3
-- https://github.com/nathanielknight/todo-sqlite3

-- Foreign Key constraints are required.
PRAGMA foreign_keys = ON;


-- Core Items table
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    -- Every item has a title (not necessarily unique)
    title TEXT NOT NULL,
    -- Body can be markdown, plaintext, asciidoc, etc.
    body TEXT,
    -- Items can be archived to support soft-deletion
    is_archived BOOLEAN NOT NULL DEFAULT 0,
    archive_status_changed_at TIMESTAMP,
    -- Items have automatically updating created_at and changed_at timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- The changed_at and archive_status_changed_at fields are automatically updated.
CREATE TRIGGER update_items_changed_at 
AFTER UPDATE ON items
BEGIN
    UPDATE items SET changed_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER update_archive_status_timestamp
AFTER UPDATE OF is_archived ON items
WHEN NEW.is_archived != OLD.is_archived
BEGIN
    UPDATE items 
    SET archive_status_changed_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
