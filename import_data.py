import json
import psycopg2
from psycopg2.extras import execute_values
import os
from pathlib import Path

def get_db_connection():
    return psycopg2.connect(
        dbname="medicine_search",
        user="postgres",
        password="syed",  # Your password from .env
        host="localhost",
        port="5433"
    )

def load_json_files():
    """Load all JSON data files from DB_Dataset/DB_Dataset/data/ into database"""
    data_dir = Path("DB_Dataset/DB_Dataset/data")
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing data
    print("Clearing existing data...")
    cursor.execute("TRUNCATE TABLE medicines RESTART IDENTITY;")
    
    all_medicines = []
    files_processed = 0
    
    # Process all JSON files (a.json to z.json)
    for json_file in sorted(data_dir.glob("*.json")):
        print(f"Processing {json_file.name}...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # Skip empty files
                    print(f"  Skipping empty file: {json_file.name}")
                    continue
                    
                data = json.loads(content)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    medicines = data
                elif isinstance(data, dict) and 'medicines' in data:
                    medicines = data['medicines']
                elif isinstance(data, dict) and 'data' in data:
                    medicines = data['data']
                else:
                    medicines = [data]  # Single medicine object
                
                for medicine in medicines:
                    # Extract medicine data with default values
                    medicine_data = {
                        'sku_id': medicine.get('sku_id', medicine.get('id', '')),
                        'name': medicine.get('name', ''),
                        'manufacturer_name': medicine.get('manufacturer_name', medicine.get('manufacturer', '')),
                        'marketer_name': medicine.get('marketer_name', medicine.get('marketer', '')),
                        'type': medicine.get('type', medicine.get('category', 'unknown')),
                        'price': float(medicine.get('price', 0.0)) if medicine.get('price') else 0.0,
                        'pack_size_label': medicine.get('pack_size_label', medicine.get('pack_size', '')),
                        'short_composition': medicine.get('short_composition', medicine.get('composition', ''))
                    }
                    
                    if medicine_data['name']:  # Only add if name exists
                        all_medicines.append(medicine_data)
                
                files_processed += 1
                
        except json.JSONDecodeError as e:
            print(f"  Error parsing {json_file.name}: {e}")
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
    
    print(f"\nProcessed {files_processed} files, found {len(all_medicines)} medicines")
    
    if all_medicines:
        # Remove duplicates by sku_id
        print("Removing duplicates...")
        seen_sku_ids = set()
        unique_medicines = []
        for med in all_medicines:
            sku_id = med['sku_id'] or f"auto_{len(unique_medicines)}"  # Generate ID if empty
            if sku_id not in seen_sku_ids:
                seen_sku_ids.add(sku_id)
                med['sku_id'] = sku_id
                unique_medicines.append(med)
        
        print(f"Unique medicines after deduplication: {len(unique_medicines)}")
        
        # Insert all medicines into database
        print("Inserting medicines into database...")
        
        insert_query = """
        INSERT INTO medicines (sku_id, name, manufacturer_name, marketer_name, type, price, pack_size_label, short_composition)
        VALUES %s
        """
        
        medicine_values = [
            (med['sku_id'], med['name'], med['manufacturer_name'], med['marketer_name'], med['type'], 
             med['price'], med['pack_size_label'], med['short_composition'])
            for med in unique_medicines
        ]
        
        execute_values(cursor, insert_query, medicine_values, page_size=1000)
        conn.commit()
        
        print(f"Successfully imported {len(unique_medicines)} medicine records!")
        
        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM medicines;")
        count = cursor.fetchone()[0]
        print(f"Total medicines in database: {count}")
        
        # Show a few examples
        cursor.execute("SELECT name, manufacturer_name, type FROM medicines LIMIT 5;")
        examples = cursor.fetchall()
        print("\nFirst 5 medicines:")
        for i, (name, manufacturer, med_type) in enumerate(examples, 1):
            print(f"  {i}. {name} by {manufacturer} ({med_type})")
    else:
        print("No medicine data found to import!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_json_files()