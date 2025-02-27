import contextlib
import functools
import sqlite3
import time
import unittest


@functools.lru_cache(maxsize=1)
def get_schema():
    with open("schema.sql") as schema_file:
        schema = schema_file.read()
        return schema


@contextlib.contextmanager
def test_database():
    with sqlite3.connect(":memory:") as cxn:
        schema = get_schema()
        cxn.executescript(schema)
        yield cxn


class TestSchemaProperties(unittest.TestCase):
    def test_insert_retrieve(self):
        "Check the very-most basic insert and retrieve."
        with test_database() as cxn:
            test_item = (
                "Test Item",
                "this is the test item body",
                False,
            )

            # Insert a record
            cxn.execute(
                "INSERT INTO items (title, body, is_archived) VALUES (?, ?, ?)",
                test_item,
            )

            # Retrieve the record
            cursor = cxn.execute("SELECT title, body, is_archived FROM items")
            retrieved = cursor.fetchone()

            # Verify the data matches what was inserted
            self.assertEqual(test_item, retrieved)

    def test_nullability(self):
        "Check that non-null fields can't be null."
        bad_cases = [
            (None, "body", None),
            ("title", "body", None),
            (None, "body", True),
            (None, "body", False),
        ]
        with test_database() as cxn:

            def attempt(c):
                cxn.execute(
                    "INSERT INTO items (title, body, is_archived) VALUES (?, ?, ?)",
                    c,
                )

            for case in bad_cases:
                self.assertRaises(sqlite3.IntegrityError, attempt, case)

    def test_created_at(self):
        "created_at is automatically populated."
        with test_database() as cxn:
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)",
                ("Test Item", "Test Body"),
            )
            cursor = cxn.execute(
                "SELECT created_at FROM items WHERE title = ?", ("Test Item",)
            )
            created_at = cursor.fetchone()[0]
            self.assertAlmostEqual(created_at, time.time(), delta=0.1)

    def test_changed_at(self):
        "changed_at is automatically updated."
        with test_database() as cxn:
            # Insert a record
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)",
                ("Test Item", "Test Body"),
            )

            # Retrieve the initial changed_at timestamp
            cursor = cxn.execute(
                "SELECT changed_at FROM items WHERE title = ?", ("Test Item",)
            )
            initial_changed_at = cursor.fetchone()[0]
            self.assertAlmostEqual(initial_changed_at, time.time(), delta=0.1)

            # Wait a moment to ensure a timestamp difference
            time.sleep(0.2)

            # Update the record
            cxn.execute(
                "UPDATE items SET body = ? WHERE title = ?",
                ("Updated Body", "Test Item"),
            )

            # Retrieve the new changed_at timestamp
            cursor = cxn.execute(
                "SELECT changed_at - created_at FROM items WHERE title = ?",
                ("Test Item",),
            )
            timediff = cursor.fetchone()[0]
            self.assertTrue(timediff > 0)

    def test_archive_status_changed_at(self):
        "archive_status_updated is changed if and only if the is_archived field changes"
        with test_database() as cxn:
            # Insert a record
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)",
                ("Test Item", "Test Body"),
            )

            # Verify archive_status_changed_at is initially NULL
            cursor = cxn.execute(
                "SELECT archive_status_changed_at FROM items WHERE title = ?",
                ("Test Item",),
            )
            initial_status = cursor.fetchone()[0]
            self.assertIsNone(initial_status)

            # Update the body without changing is_archived
            cxn.execute(
                "UPDATE items SET body = ? WHERE title = ?",
                ("Updated Body", "Test Item"),
            )

            # Verify archive_status_changed_at is still NULL
            cursor = cxn.execute(
                "SELECT archive_status_changed_at FROM items WHERE title = ?",
                ("Test Item",),
            )
            after_update_status = cursor.fetchone()[0]
            self.assertIsNone(after_update_status)

            # Change the is_archived status
            cxn.execute(
                "UPDATE items SET is_archived = 1 WHERE title = ?", ("Test Item",)
            )

            # Verify archive_status_changed_at is now set
            cursor = cxn.execute(
                "SELECT archive_status_changed_at FROM items WHERE title = ?",
                ("Test Item",),
            )
            after_archive_status = cursor.fetchone()[0]
            self.assertIsNotNone(after_archive_status)
            self.assertAlmostEqual(after_archive_status, time.time(), delta=0.1)

            # Another update without changing is_archived shouldn't change the timestamp
            time.sleep(0.2)
            cxn.execute(
                "UPDATE items SET title = ? WHERE title = ?",
                ("Renamed Item", "Test Item"),
            )

            cursor = cxn.execute(
                "SELECT archive_status_changed_at FROM items WHERE title = ?",
                ("Renamed Item",),
            )
            after_rename_status = cursor.fetchone()[0]
            self.assertEqual(after_archive_status, after_rename_status)

            # Changing is_archived again should update the timestamp
            time.sleep(0.2)
            cxn.execute(
                "UPDATE items SET is_archived = 0 WHERE title = ?", ("Renamed Item",)
            )

            cursor = cxn.execute(
                "SELECT archive_status_changed_at FROM items WHERE title = ?",
                ("Renamed Item",),
            )
            final_status = cursor.fetchone()[0]
            self.assertIsNotNone(final_status)
            self.assertNotEqual(after_archive_status, final_status)
            self.assertAlmostEqual(final_status, time.time(), delta=0.1)

    def test_retrieving_by_id(self):
        "Demonstrate insert returning id; retrieve by id"
        with test_database() as cxn:
            # Insert first record with title "Duplicate Title"
            cursor = cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?) RETURNING id",
                ("Duplicate Title", "First body"),
            )
            first_id = cursor.fetchone()[0]

            # Insert second record with the same title but different body
            cursor = cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?) RETURNING id",
                ("Duplicate Title", "Second body"),
            )
            second_id = cursor.fetchone()[0]

            # Verify the IDs are different
            self.assertNotEqual(first_id, second_id)

            # Update the first item
            cxn.execute(
                "UPDATE items SET body = 'New first body' WHERE id = ?", (first_id,)
            )

            # Retrieve the first record by ID and verify its content
            cursor = cxn.execute(
                "SELECT title, body FROM items WHERE id = ?", (first_id,)
            )
            first_record = cursor.fetchone()
            self.assertEqual(first_record, ("Duplicate Title", "New first body"))

            # Retrieve the second record by ID and verify its content
            cursor = cxn.execute(
                "SELECT title, body FROM items WHERE id = ?", (second_id,)
            )
            second_record = cursor.fetchone()
            self.assertEqual(second_record, ("Duplicate Title", "Second body"))

    def test_foreign_key_constraint(self):
        "Foreign keys are enforced"
        with test_database() as cxn:
            # Create a test table with foreign key reference
            cxn.execute(
                """
                CREATE TABLE test_references (
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            """
            )

            # Test inserting with non-existent reference
            with self.assertRaises(sqlite3.IntegrityError):
                cxn.execute(
                    "INSERT INTO test_references (item_id) VALUES (?)",
                    (999,),  # Non-existent ID
                )

            # Insert a valid item first
            cursor = cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?) RETURNING id",
                ("Test Item", "Test Body"),
            )
            item_id = cursor.fetchone()[0]

            # Test inserting with valid reference - should succeed
            cxn.execute("INSERT INTO test_references (item_id) VALUES (?)", (item_id,))

            # Test deleting referenced item - delete should cascade
            # Delete referenced item - should cascade
            cxn.execute("DELETE FROM items WHERE id = ?", (item_id,))

            # Verify the referenced record was also deleted
            cursor = cxn.execute(
                "SELECT COUNT(*) FROM test_references WHERE item_id = ?", (item_id,)
            )
            count = cursor.fetchone()[0]
            self.assertEqual(count, 0)
