# TODO Sqlite3

This is a schema for a [SQLite database](https://sqlite.org/) for holding todo/task/project data.

It's inspired by [todo.txt](http://todotxt.org/) and [Getting Things Done](https://en.wikipedia.org/wiki/Getting_Things_Done).

It defines a single table with the following columns:

- `id`: unique numeric id
- `title`: textual title for the item (e.g. "Learn SQLite")
- `body`: (possibly null) body for notes, links, comments, work-in-progress, etc.
- `is_archived`: support soft deletion
- `archived_status_changed_at`: the last time `is_archived` changed
- `created_at`: when the item was created
- `changed_at`: when the item was last updated

`id` is assigned automatically and shouldn't be changed.

Timestamp fields (`archived_status_changed_at`, `created_at`, and `changed_at`) are created and updated automatically.



# Design Goals and Rationale

- **Leverage SQLite** Formats like todo.txt already exist; this project aims to provide a more flexible, capable foundation without sacrificing stability or ubiquity. 

- **Human Scale** The format is designed for _personal_ use, and one person's to-do list shouldn't be terabytes long, so when choosing between simplicity and scalability, we strongly prefer simplicity.

- **Open for extension** The format isn't prescriptive about how you use it, and it doesn't cover every possible need. Extensions are expected and welcomed.


# The Core Schema

The core `items` table (as in [`.schema.sql`](./schema.sql)):

```sql
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
```

# Extensions

- Can make their own tables, but shouldn't modify `items`
- Can rely on foreign keys
- Should delete-cascade when items are deleted
- Can specify tables, triggers, views, etc. but can't specify application semantics.


# License

todo-sqlite3 is shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
