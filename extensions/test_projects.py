import contextlib
import functools
import sqlite3
import unittest


@functools.lru_cache(maxsize=1)
def get_schema():
    with open("schema.sql") as schema_file:
        schema = schema_file.read()
        return schema


@functools.lru_cache(maxsize=1)
def get_extension():
    with open("extensions/projects.sql") as schema_file:
        schema = schema_file.read()
        return schema


@contextlib.contextmanager
def test_database():
    with sqlite3.connect(":memory:") as cxn:
        cxn.executescript(get_schema())
        cxn.executescript(get_extension())
        yield cxn


def query_project_items(cxn: sqlite3.Connection, project_name: str):
    "Retrieve all items belonging to a specific project."
    return cxn.execute(
        """
        SELECT 
            i.*,
            p.name AS project_name,
            p.id AS project_id
        FROM 
            items i
        JOIN 
            project_items pi ON i.id = pi.item_id
        JOIN 
            projects p ON pi.project_id = p.id
        WHERE 
            p.name = ?
        """,
        (project_name,),
    ).fetchall()


class TestProjectsExtension(unittest.TestCase):
    def test_creating_projects(self):
        with test_database() as cxn:
            # Create a project
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Test Project", "Project description"),
            )
            
            # Verify project was created
            project = cxn.execute("SELECT * FROM projects").fetchone()
            self.assertEqual(project[1], "Test Project")
            self.assertEqual(project[2], "Project description")
    
    def test_assigning_items_to_projects(self):
        with test_database() as cxn:
            # Create test items
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 1", "Body 1")
            )
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 2", "Body 2")
            )
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 3", "Body 3")
            )
            
            # Create a project
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Test Project", "Project description"),
            )
            project_id = cxn.execute("SELECT id FROM projects").fetchone()[0]
            
            # Assign items 1 and 2 to the project
            cxn.execute(
                "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                (project_id, 1),
            )
            cxn.execute(
                "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                (project_id, 2),
            )
            
            # Verify project items
            project_items = query_project_items(cxn, "Test Project")
            self.assertEqual(len(project_items), 2)
            
            # Check that the right items are in the project
            titles = [item[1] for item in project_items]
            self.assertIn("Item 1", titles)
            self.assertIn("Item 2", titles)
            self.assertNotIn("Item 3", titles)
    
    def test_unique_constraint_on_items(self):
        with test_database() as cxn:
            # Create a test item
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 1", "Body 1")
            )
            
            # Create two projects
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Project 1", "Description 1"),
            )
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Project 2", "Description 2"),
            )
            
            # Assign item to first project
            cxn.execute(
                "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                (1, 1),
            )
            
            # Try to assign the same item to second project, should fail due to UNIQUE constraint
            with self.assertRaises(sqlite3.IntegrityError):
                cxn.execute(
                    "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                    (2, 1),
                )
    
    def test_cascade_delete_project(self):
        with test_database() as cxn:
            # Create test item
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 1", "Body 1")
            )
            
            # Create a project and assign the item
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Test Project", "Project description"),
            )
            cxn.execute(
                "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                (1, 1),
            )
            
            # Delete the project
            cxn.execute("DELETE FROM projects WHERE id = ?", (1,))
            
            # Verify project_items relation is deleted but the item still exists
            project_items = cxn.execute("SELECT * FROM project_items").fetchall()
            self.assertEqual(len(project_items), 0)
            
            items = cxn.execute("SELECT * FROM items").fetchall()
            self.assertEqual(len(items), 1)
    
    def test_cascade_delete_item(self):
        with test_database() as cxn:
            # Create test item
            cxn.execute(
                "INSERT INTO items (title, body) VALUES (?, ?)", ("Item 1", "Body 1")
            )
            
            # Create a project and assign the item
            cxn.execute(
                "INSERT INTO projects (name, body) VALUES (?, ?)",
                ("Test Project", "Project description"),
            )
            cxn.execute(
                "INSERT INTO project_items (project_id, item_id) VALUES (?, ?)",
                (1, 1),
            )
            
            # Delete the item
            cxn.execute("DELETE FROM items WHERE id = ?", (1,))
            
            # Verify project_items relation is deleted but the project still exists
            project_items = cxn.execute("SELECT * FROM project_items").fetchall()
            self.assertEqual(len(project_items), 0)
            
            projects = cxn.execute("SELECT * FROM projects").fetchall()
            self.assertEqual(len(projects), 1)
