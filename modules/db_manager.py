# -*- coding: utf-8 -*-
__author__     = "Mia Sophie Behrendt"
__copyright__  = "Copyright 2023, Maker-Hub.de"
__license__    = "GPL"
__version__    = "1.0.0"
__maintainer__ = "Maker-Hub-De"
__email__      = "github@maker-hub.de"
__status__     = "Development"
__date__       = "12.10.2023"

import os
import sqlite3
import logging

class DBManager:
    def __init__(self, db_filename, logger=None):
        # Use an absolute path to the SQLite database file
        self.db_filename = os.path.abspath(db_filename)
        self.logger = logger if logger else logging.getLogger("DBManager")

        # Check if the database file already exists; if not, create it
        if not os.path.exists(self.db_filename):
            self.create_db_file()
        else:
            self.logging.info(f"Database file '{self.db_filename}' found")

    def __del__(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except sqlite3.Error as e:
            self.logging.error(f"Error closing the database connection: {str(e)}")

    def create_db_file(self):
        try:
            with sqlite3.connect(self.db_filename) as conn:
                self.logging.info(f"Database file '{self.db_filename}' created")
        except sqlite3.Error as e:
            self.logging.error(f"Error creating database file: {str(e)}")
            exit()  # Exit the program

    def create_table(self):
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                # Check if the table already exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_info'")
                table_exists = cursor.fetchone()

                if not table_exists:
                    # Create table
                    cursor.execute('''
                        CREATE TABLE file_info (
                            filename TEXT PRIMARY KEY,
                            last_modified INTEGER,
                            last_checked INTEGER
                        )
                    ''')
                    conn.commit()
                    self.logging.info("Table file_info created")
                else:
                    self.logging.info("Table file_info exists")
        except sqlite3.Error as e:
            self.logging.error(f"Error creating table: {str(e)}")

    def insert_file_info(self, filename, last_modified, last_checked):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO file_info (filename, last_modified, last_checked) VALUES (?, ?, ?)", (filename, last_modified, last_checked))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error inserting file info: {str(e)}")
            return False

    def update_file_info(self, filename, last_modified, last_checked):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("UPDATE file_info SET last_modified = ?, last_checked = ? WHERE filename = ?", (last_modified, last_checked, filename))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error updating file info: {str(e)}")
            return False

    def delete_file_info(self, filename):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_info WHERE filename = ?", (filename,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error deleting file info: {str(e)}")
            return False

    def get_file_info(self, filename):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT last_modified, last_checked FROM file_info WHERE filename = ?", (filename,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0], result[1] 
            else:
                return None, None
        except sqlite3.Error as e:
            self.logging.error(f"Error getting file info: {str(e)}")
            return None, None

    def get_files_not_checked_since(self, since_datetime):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT filename, last_checked FROM file_info WHERE last_checked <= ?", (since_datetime,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error as e:
            self.logging.error(f"Error getting files not checked since: {str(e)}")
            return []
