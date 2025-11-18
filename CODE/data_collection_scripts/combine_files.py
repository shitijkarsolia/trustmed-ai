#!/usr/bin/env python3
"""
Combine multiple JSON and CSV files by disease area, removing duplicates.
"""

import json
import csv
import glob
import os
from datetime import datetime

# Get script directory and set output relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'data')


def combine_json_files(disease_name):
    """Combine all JSON files for a disease, removing duplicates."""
    json_files = [f for f in glob.glob(f"{OUTPUT_DIR}/{disease_name}_threads_*.json") 
                  if 'incremental' not in f and 'combined' not in f]
    
    if not json_files:
        print(f'  No JSON files found for {disease_name}')
        return None
    
    print(f'\n📊 Combining {len(json_files)} JSON files for {disease_name}:')
    for f in json_files:
        print(f'    - {os.path.basename(f)}')
    
    all_threads = []
    seen_ids = set()
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                threads = json.load(f)
                for thread in threads:
                    thread_id = thread.get('id')
                    if thread_id and thread_id not in seen_ids:
                        seen_ids.add(thread_id)
                        all_threads.append(thread)
                    elif thread_id:
                        print(f'    ⚠ Skipped duplicate: {thread_id}')
        except Exception as e:
            print(f'    ✗ Error reading {os.path.basename(json_file)}: {e}')
    
    print(f'  ✓ Combined: {len(all_threads)} unique threads')
    return all_threads


def combine_csv_files(disease_name):
    """Combine all CSV files for a disease, removing duplicates."""
    csv_files = [f for f in glob.glob(f"{OUTPUT_DIR}/{disease_name}_threads_*.csv") 
                 if 'incremental' not in f and 'combined' not in f]
    
    if not csv_files:
        print(f'  No CSV files found for {disease_name}')
        return None
    
    print(f'\n📊 Combining {len(csv_files)} CSV files for {disease_name}:')
    for f in csv_files:
        print(f'    - {os.path.basename(f)}')
    
    all_rows = []
    seen_ids = set()
    fieldnames = None
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                
                for row in reader:
                    thread_id = row.get('id')
                    if thread_id and thread_id not in seen_ids:
                        seen_ids.add(thread_id)
                        all_rows.append(row)
                    elif thread_id:
                        print(f'    ⚠ Skipped duplicate: {thread_id}')
        except Exception as e:
            print(f'    ✗ Error reading {os.path.basename(csv_file)}: {e}')
    
    if all_rows and fieldnames:
        print(f'  ✓ Combined: {len(all_rows)} unique threads')
        return all_rows, fieldnames
    return None, None


def main():
    print('=' * 70)
    print('COMBINING FILES BY DISEASE AREA')
    print('=' * 70)
    
    # Combine diabetes files
    print('\n' + '=' * 70)
    print('DIABETES')
    print('=' * 70)
    
    diabetes_threads = combine_json_files('diabetes')
    if diabetes_threads:
        # Save combined JSON
        output_json = os.path.join(OUTPUT_DIR, 'diabetes_threads_combined.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(diabetes_threads, f, indent=2, ensure_ascii=False)
        print(f'  💾 Saved: {os.path.basename(output_json)}')
    
    diabetes_rows, fieldnames = combine_csv_files('diabetes')
    if diabetes_rows and fieldnames:
        # Save combined CSV
        output_csv = os.path.join(OUTPUT_DIR, 'diabetes_threads_combined.csv')
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(diabetes_rows)
        print(f'  💾 Saved: {os.path.basename(output_csv)}')
    
    # Combine heart disease files
    print('\n' + '=' * 70)
    print('HEART DISEASE')
    print('=' * 70)
    
    heart_threads = combine_json_files('heart_disease')
    if heart_threads:
        # Save combined JSON
        output_json = os.path.join(OUTPUT_DIR, 'heart_disease_threads_combined.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(heart_threads, f, indent=2, ensure_ascii=False)
        print(f'  💾 Saved: {os.path.basename(output_json)}')
    
    heart_rows, fieldnames = combine_csv_files('heart_disease')
    if heart_rows and fieldnames:
        # Save combined CSV
        output_csv = os.path.join(OUTPUT_DIR, 'heart_disease_threads_combined.csv')
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(heart_rows)
        print(f'  💾 Saved: {os.path.basename(output_csv)}')
    
    # Summary
    print('\n' + '=' * 70)
    print('SUMMARY')
    print('=' * 70)
    if diabetes_threads:
        print(f'Diabetes: {len(diabetes_threads)} threads')
    if heart_threads:
        print(f'Heart Disease: {len(heart_threads)} threads')
    print('=' * 70)
    print('\n✓ Files combined successfully!')
    print(f'  Combined files saved to: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()

