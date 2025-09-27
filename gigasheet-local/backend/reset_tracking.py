#!/usr/bin/env python3
"""
🔄 Reset processed files tracking
Use this if you want to reprocess all files from scratch
"""

import duckdb
import os

def reset_processing_history():
    print("🔄 Resetting processed files tracking...")
    
    try:
        # Connect to database
        conn = duckdb.connect('gigasheet_data.db')
        
        # Clear processed files table
        conn.execute("DELETE FROM processed_files")
        print("✅ Cleared processed files tracking")
        
        # Optionally drop and recreate the merged_excel_data table
        response = input("🗑️  Do you want to also clear all merged data? (y/N): ")
        if response.lower() == 'y':
            conn.execute("DROP TABLE IF EXISTS merged_excel_data")
            print("✅ Cleared merged data table")
            print("🎯 Next merge will process all files fresh")
        else:
            print("💾 Merged data kept - only tracking reset")
        
        conn.close()
        print("\n🎉 Reset complete!")
        print("ℹ️  Next smart merge will analyze all files as 'new'")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 RESET PROCESSING TRACKING")
    print("=" * 50)
    reset_processing_history()