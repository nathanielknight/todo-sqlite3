-- TAGS
-- Tags are stored in their own table with a many-to-many relationship to items.

CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    -- Tags can be any UTF8 encoded string.
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE item_tags (
    item_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (item_id, tag_id),
    -- Tag links are deleted when tags or items are deleted.
    FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);
