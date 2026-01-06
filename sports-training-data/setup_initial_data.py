#!/usr/bin/env python3
"""
Initial Data Setup Runner
Runs all setup scripts to populate foundational training data
"""

import asyncio
import subprocess
import sys
from pathlib import Path

def run_script(script_path):
    """Run a Python script and return success status"""
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print(f"✅ {script_path} completed successfully")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {script_path} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run {script_path}: {e}")
        return False

async def main():
    """Run all initial data setup scripts"""
    
    print("SportAI Training Data - Initial Setup")
    print("=" * 50)
    print("This will populate your MongoDB with foundational training data:")
    print("1. Fantasy Football Overview & Fundamentals")
    print("2. SportAI Product Context & User Personas")
    print("=" * 50)
    
    # Confirm before running
    response = input("Continue with setup? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Setup cancelled.")
        return
    
    setup_dir = Path(__file__).parent / "setup"
    scripts = [
        "add_fantasy_overview.py",
        "add_product_context.py"
    ]
    
    success_count = 0
    
    for script in scripts:
        script_path = setup_dir / script
        if script_path.exists():
            print(f"\n🔄 Running {script}...")
            if run_script(script_path):
                success_count += 1
        else:
            print(f"⚠️  Script not found: {script_path}")
    
    print(f"\n📊 Setup Summary:")
    print(f"Successfully completed: {success_count}/{len(scripts)} scripts")
    
    if success_count == len(scripts):
        print("🎉 Initial data setup complete!")
        print("\nNext steps:")
        print("1. Run data collection: python3 main.py")
        print("2. Start LLM server: cd ../sports-llm && python3 main.py")
    else:
        print("⚠️  Some scripts failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())