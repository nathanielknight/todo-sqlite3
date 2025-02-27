import contextlib
import functools
import json
import sqlite3
import unittest


@functools.lru_cache(maxsize=1)
def get_schema():
    with open("schema.sql") as schema_file:
        schema = schema_file.read()
        return schema


@functools.lru_cache(maxsize=1)
def get_extension():
    with open("extensions/tags.sql") as schema_file:
        schema = schema_file.read()
        return schema


@contextlib.contextmanager
def test_database():
    with sqlite3.connect(":memory:") as cxn:
        cxn.executescript(get_schema())
        cxn.executescript(get_extension())
        yield cxn


def query_tagged(cxn: sqlite3.Connection, tag: str):
    "Retrieve all items with a particular tag, as well as their list of tags."
    return cxn.execute(
        """
        SELECT 
            i.*,
            json_group_array(t2.name) FILTER (WHERE t2.name IS NOT NULL) AS tags
        FROM 
            items i
        JOIN 
            item_tags it1 ON i.id = it1.item_id
        JOIN 
            tags t1 ON it1.tag_id = t1.id
        LEFT JOIN 
            item_tags it2 ON i.id = it2.item_id
        LEFT JOIN 
            tags t2 ON it2.tag_id = t2.id
        WHERE 
            t1.name = ?
        GROUP BY 
            i.id
        """,
        (tag,),
    ).fetchall()


class TestTagsExtension(unittest.TestCase):
    def test_retrieving_tagged_items(self):
        # Create three items, tag two of them, and verify that the expected
        # items are tagged in the `tagged_item` view.
        with test_database() as cxn:
            # Create three test items
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 1", "Body 1")
            )
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 2", "Body 2")
            )
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 3", "Body 3")
            )

            # Tag items 1 and 2
            cxn.execute("INSERT INTO tags (name) VALUES (?)", ("test-tag",))
            tag_id = cxn.execute("SELECT id FROM tags").fetchone()[0]

            cxn.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)", (1, tag_id)
            )
            cxn.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)", (2, tag_id)
            )

            # Verify tagged items
            assert len(query_tagged(cxn, "nonexistent-tag")) == 0
    
            tagged_items = query_tagged(cxn, "test-tag")
            self.assertEqual(len(tagged_items), 2)
            item1 = next(ti for ti in tagged_items if ti[1] == "Item 1")
            self.assertEqual(json.loads(item1[-1]), ["test-tag"])
