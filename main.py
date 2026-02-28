import subprocess
import sys
import time

def run_script(script_path, run_as_streamlit=False):
    """Helper function to execute python scripts and handle errors."""
    print(f"\n{'='*50}")
    print(f"🚀 EXECUTING: {script_path}")
    print(f"{'='*50}")
    
    try:
        if run_as_streamlit:
            # Streamlit requires a different execution command
            subprocess.run([sys.executable, "-m", "streamlit", "run", script_path], check=True)
        else:
            # Standard python script execution
            subprocess.run([sys.executable, script_path], check=True)
            
        print(f"✅ SUCCESS: {script_path} completed.\n")
        time.sleep(1) # Brief pause for terminal readability
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to execute {script_path}.")
        print(f"Details: {e}")
        sys.exit(1) # Stop the pipeline if a step fails

if __name__ == "__main__":
    print("\n" + "#"*60)
    print(" ⚙️ SaaS REVENUE RETENTION ENGINE - PIPELINE ORCHESTRATOR ⚙️ ")
    print("#"*60 + "\n")

    # 1. Generate Raw Data
    run_script("src/data_generator.py")
    
    # 2. Run ETL (Load to DB & Execute SQL Marts)
    run_script("src/etl_loader.py")
    
    # 3. Analytics Layer: Generate Risk Segmentation
    run_script("src/risk_segmentation.py")
    
    # 4. Analytics Layer: Forecast Next 6 Months MRR
    run_script("src/forecast_model.py")
    
    # 5. Launch the Executive Dashboard
    print("\n🎉 PIPELINE COMPLETE! Launching the Executive Dashboard...")
    time.sleep(2)
    run_script("src/dashboard.py", run_as_streamlit=True)