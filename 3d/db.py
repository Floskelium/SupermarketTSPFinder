import sqlite3
import random
from collections import Counter


class GroceryDBInterface:
    def __init__(self, db_path='grocery_store.db'):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_all_groceries(self):
        """Retrieve all groceries with their category and shelf information"""
        query = '''
            SELECT groceries.id, groceries.name, groceries.shelf_id, categories.name AS category_name
            FROM groceries
            JOIN categories ON groceries.category_id = categories.id
            ORDER BY groceries.shelf_id
        '''
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        groceries = [
            {"id": row[0], "name": row[1], "shelf_id": row[2], "category": row[3]}
            for row in rows
        ]
        return groceries

    def get_groceries_by_category(self, category_name):
        """Retrieve groceries by a specific category name"""
        query = '''
            SELECT groceries.id, groceries.name, groceries.shelf_id
            FROM groceries
            JOIN categories ON groceries.category_id = categories.id
            WHERE categories.name = ?
            ORDER BY groceries.shelf_id
        '''
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (category_name,))
            rows = cursor.fetchall()

        groceries = [
            {"id": row[0], "name": row[1], "shelf_id": row[2]}
            for row in rows
        ]
        return groceries

    def get_grocery_by_id(self, grocery_id):
        """Retrieve a single grocery item by its ID"""
        query = '''
            SELECT groceries.id, groceries.name, groceries.shelf_id, categories.name AS category_name
            FROM groceries
            JOIN categories ON groceries.category_id = categories.id
            WHERE groceries.id = ?
        '''
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (grocery_id,))
            row = cursor.fetchone()

        if row:
            return {"id": row[0], "name": row[1], "shelf_id": row[2], "category": row[3]}
        return None

    def get_groceries_by_shelf(self, shelf_id):
        """Retrieve all groceries on a specific shelf."""
        query = '''
            SELECT groceries.id, groceries.name, categories.name AS category_name
            FROM groceries
            JOIN categories ON groceries.category_id = categories.id
            WHERE groceries.shelf_id = ?
        '''
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (shelf_id,))
            rows = cursor.fetchall()

        groceries = [
            {"id": row[0], "name": row[1], "category": row[2]}
            for row in rows
        ]
        return groceries

    def search_groceries(self, search_term):
        """Search groceries by category name or grocery name with a case-insensitive substring match.
        Returns results where most items share the same shelf_id.
        """
        query = '''
            SELECT groceries.id, groceries.name, groceries.shelf_id, categories.name AS category_name
            FROM groceries
            JOIN categories ON groceries.category_id = categories.id
            WHERE groceries.name LIKE ? OR categories.name LIKE ?
        '''
        search_pattern = f'%{search_term}%'

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (search_pattern, search_pattern))
            rows = cursor.fetchall()

        # Structure the data and identify the most common shelf ID
        groceries = [
            {"id": row[0], "name": row[1], "shelf_id": row[2], "category": row[3]}
            for row in rows
        ]

        # Count shelf IDs to find the most common one
        shelf_counts = Counter(grocery["shelf_id"] for grocery in groceries)
        if not shelf_counts:
            return []  # No results found

        # Get the shelf_id with the highest count
        most_common_shelf_id = shelf_counts.most_common(1)[0][0]

        # Filter groceries to only include items on the most common shelf
        filtered_groceries = [
            grocery for grocery in groceries if grocery["shelf_id"] == most_common_shelf_id
        ]

        return filtered_groceries


if __name__ == '__main__':
    # Connect to (or create) the database
    conn = sqlite3.connect('grocery_store.db')
    cursor = conn.cursor()

    # Create tables for categories and groceries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groceries (
            id INTEGER PRIMARY KEY,
            shelf_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # List of German category names
    categories = [
        "Mehl", "Apfel", "Müsli", "Milch", "Käse", "Brot", "Fleisch", "Gemüse", "Obst",
        "Getränke", "Eier", "Fisch", "Nudeln", "Reis", "Suppe", "Snacks", "Süßigkeiten", "Kaffee",
        "Tee", "Honig", "Marmelade", "Gewürze", "Soßen", "Konserven", "Öl", "Essig"
    ]

    # Insert categories into the categories table
    for category in categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name) VALUES (?)
        ''', (category,))

    # Commit the category insertions
    conn.commit()

    # Dictionary to store specific products (grocery items) for each category
    grocery_items = {
        "Mehl": ["Weizenmehl", "Roggenmehl", "Dinkelmehl"],
        "Apfel": ["Gala Apfel", "Granny Smith", "Braeburn"],
        "Müsli": ["Früchte-Müsli", "Schoko-Müsli", "Korn-Müsli"],
        "Milch": ["Vollmilch", "Fettarme Milch", "Laktosefreie Milch"],
        "Käse": ["Gouda", "Emmentaler", "Camembert"],
        "Brot": ["Roggenbrot", "Vollkornbrot", "Toastbrot"],
        "Fleisch": ["Rindfleisch", "Schweinefleisch", "Hühnerfleisch"],
        "Gemüse": ["Karotten", "Tomaten", "Salat"],
        "Obst": ["Bananen", "Birnen", "Kiwis"],
        "Getränke": ["Mineralwasser", "Orangensaft", "Apfelsaft"],
        "Eier": ["Freilandeier", "Bio-Eier", "Bodenhaltung-Eier"],
        "Fisch": ["Lachs", "Forelle", "Thunfisch"],
        "Nudeln": ["Spaghetti", "Penne", "Fusilli"],
        "Reis": ["Langkornreis", "Basmati-Reis", "Jasmin-Reis"],
        "Suppe": ["Tomatensuppe", "Hühnersuppe", "Gemüsesuppe"],
        "Snacks": ["Chips", "Popcorn", "Erdnüsse"],
        "Süßigkeiten": ["Schokolade", "Bonbons", "Kekse"],
        "Kaffee": ["Espresso", "Kaffeebohnen", "Instant-Kaffee"],
        "Tee": ["Schwarztee", "Grüntee", "Früchtetee"],
        "Honig": ["Blütenhonig", "Waldhonig", "Akazienhonig"],
        "Marmelade": ["Erdbeermarmelade", "Aprikosenmarmelade", "Himbeermarmelade"],
        "Gewürze": ["Pfeffer", "Salz", "Paprika"],
        "Soßen": ["Tomatensoße", "Käsesoße", "BBQ-Soße"],
        "Konserven": ["Erbsen in Dose", "Mais in Dose", "Bohnen in Dose"],
        "Öl": ["Olivenöl", "Sonnenblumenöl", "Kokosöl"],
        "Essig": ["Apfelessig", "Balsamico-Essig", "Weißweinessig"]
    }

    # Insert grocery items into the groceries table
    shelf_id_counter = 1
    for category_name, items in grocery_items.items():
        # Get the category_id from the categories table
        cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
        category_id = cursor.fetchone()[0]

        for item_name in items:
            # Insert grocery item with an incrementing shelf_id
            cursor.execute('''
                INSERT INTO groceries (shelf_id, name, category_id) 
                VALUES (?, ?, ?)
            ''', (shelf_id_counter, item_name, category_id))
        shelf_id_counter += random.randint(0, 1)

    # Commit the grocery items insertions
    conn.commit()

    # Verify the data by printing the contents of each table
    print("Categories:")
    for row in cursor.execute('SELECT * FROM categories'):
        print(row)

    print("\nGroceries:")
    for row in cursor.execute('SELECT * FROM groceries'):
        print(row)

    conn.close()
