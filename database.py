import os
import sqlite3
from typing import List, Dict, Any, Optional

# Operational Database configuration
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "postgres")

# Check if we should use AlloyDB (PostgreSQL) or SQLite
USE_POSTGRES = DB_HOST is not None

def get_connection():
    """
    Returns a database connection. Automatically switches between 
    AlloyDB (PostgreSQL) and local SQLite based on environment variables.
    """
    if USE_POSTGRES:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=3
            )
            return conn
        except ImportError:
            print("WARNING: psycopg2 not installed. Falling back to SQLite.")
        except Exception as e:
            print(f"WARNING: Failed to connect to AlloyDB ({e}). Falling back to SQLite.")
            
    # SQLite fallback
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zoneguardian.db")
    conn = sqlite3.connect(db_path)
    # Enable row factory for dictionary-like results
    conn.row_factory = sqlite3.Row
    return conn

import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def seed_super_admin():
    """
    Seeds the default super admin credentials (yudhae@gmail.com / Password!123) if they do not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    admin_email = "yudhae@gmail.com"
    admin_password_hash = hash_password("Password!123")
    
    if USE_POSTGRES:
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (admin_email,))
    else:
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (admin_email,))
        
    if not cursor.fetchone():
        print(f"Seeding super admin user '{admin_email}'...")
        if USE_POSTGRES:
            cursor.execute(
                "INSERT INTO users (user_id, name, email, password_hash, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                ("admin_1", "Yudhae", admin_email, admin_password_hash, "super_admin")
            )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, name, email, password_hash, role) "
                "VALUES (?, ?, ?, ?, ?)",
                ("admin_1", "Yudhae", admin_email, admin_password_hash, "super_admin")
            )
        conn.commit()
    conn.close()

def init_db():
    """
    Runs schema DDL to create tables if they do not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        # PostgreSQL syntax for AlloyDB
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'parent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteer_roster (
                roster_id SERIAL PRIMARY KEY,
                school_id VARCHAR(50) NOT NULL,
                volunteer_name VARCHAR(100) NOT NULL,
                assigned_zone VARCHAR(100) NOT NULL,
                time_window VARCHAR(50) NOT NULL,
                shift_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        # SQLite syntax for local development
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'parent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteer_roster (
                roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT NOT NULL,
                volunteer_name TEXT NOT NULL,
                assigned_zone TEXT NOT NULL,
                time_window TEXT NOT NULL,
                shift_date TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_hazards (
                hazard_id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_id TEXT NOT NULL,
                description TEXT NOT NULL,
                severity_multiplier REAL DEFAULT 1.0,
                hazard_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_briefings (
                school_id TEXT PRIMARY KEY,
                briefing_html TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_hazards (
                hazard_id SERIAL PRIMARY KEY,
                school_id VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                severity_multiplier FLOAT DEFAULT 1.0,
                hazard_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS school_briefings (
                school_id VARCHAR(50) PRIMARY KEY,
                briefing_html TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
    conn.commit()
    conn.close()
    print(f"Operational database initialized (Mode: {'AlloyDB/PostgreSQL' if USE_POSTGRES else 'Local SQLite'}).")
    
    # Seed the super admin credentials
    try:
        seed_super_admin()
    except Exception as e:
        print(f"Failed to seed super admin: {e}")

# Roster CRUD Operations
def add_volunteer_shift(school_id: str, name: str, zone: str, time_window: str, shift_date: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "INSERT INTO volunteer_roster (school_id, volunteer_name, assigned_zone, time_window, shift_date) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING roster_id",
            (school_id, name, zone, time_window, shift_date)
        )
        roster_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            "INSERT INTO volunteer_roster (school_id, volunteer_name, assigned_zone, time_window, shift_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (school_id, name, zone, time_window, shift_date)
        )
        roster_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return roster_id

def get_volunteer_shifts(school_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT roster_id, school_id, volunteer_name, assigned_zone, time_window, shift_date, status "
            "FROM volunteer_roster WHERE school_id = %s ORDER BY created_at DESC",
            (school_id,)
        )
        # Convert tuples to dicts for PostgreSQL
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        cursor.execute(
            "SELECT roster_id, school_id, volunteer_name, assigned_zone, time_window, shift_date, status "
            "FROM volunteer_roster WHERE school_id = ? ORDER BY created_at DESC",
            (school_id,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        
    conn.close()
    return results

# Hazards CRUD Operations
def add_hazard(school_id: str, description: str, severity_multiplier: float, hazard_type: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "INSERT INTO school_hazards (school_id, description, severity_multiplier, hazard_type) "
            "VALUES (%s, %s, %s, %s) RETURNING hazard_id",
            (school_id, description, severity_multiplier, hazard_type)
        )
        hazard_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            "INSERT INTO school_hazards (school_id, description, severity_multiplier, hazard_type) "
            "VALUES (?, ?, ?, ?)",
            (school_id, description, severity_multiplier, hazard_type)
        )
        hazard_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return hazard_id

def get_hazards(school_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT hazard_id, school_id, description, severity_multiplier, hazard_type, created_at "
            "FROM school_hazards WHERE school_id = %s ORDER BY created_at DESC",
            (school_id,)
        )
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        cursor.execute(
            "SELECT hazard_id, school_id, description, severity_multiplier, hazard_type, created_at "
            "FROM school_hazards WHERE school_id = ? ORDER BY created_at DESC",
            (school_id,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        
    conn.close()
    return results

# Briefings CRUD Operations
def save_briefing(school_id: str, briefing_html: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "INSERT INTO school_briefings (school_id, briefing_html, updated_at) "
            "VALUES (%s, %s, CURRENT_TIMESTAMP) "
            "ON CONFLICT (school_id) DO UPDATE SET briefing_html = EXCLUDED.briefing_html, updated_at = CURRENT_TIMESTAMP",
            (school_id, briefing_html)
        )
    else:
        cursor.execute(
            "INSERT OR REPLACE INTO school_briefings (school_id, briefing_html, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (school_id, briefing_html)
        )
        
    conn.commit()
    conn.close()

def get_latest_briefing(school_id: str) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute(
            "SELECT briefing_html FROM school_briefings WHERE school_id = %s",
            (school_id,)
        )
    else:
        cursor.execute(
            "SELECT briefing_html FROM school_briefings WHERE school_id = ?",
            (school_id,)
        )
        
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return None
