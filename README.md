# TODO Sqlite3

This is a schema for a [SQLite database](https://sqlite.org/) for holding todo/task/project data.

It's inspired by [todo.txt](http://todotxt.org/) and [Getting Things Done](https://en.wikipedia.org/wiki/Getting_Things_Done).

todo-sqlite3 is shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

# Design Goals and Rationale

- As simple as possible but no simpler
- Designed for longevity, flexibility, and human scale
- Leverage SQLite to enable features
- Open for extension

# Extensions

- Can make their own tables, but shouldn't modify `items`
- Can rely on foreign keys
- Should delete-cascade when items are deleted
- Can specify tables, triggers, views, etc. but can't specify application semantics.
