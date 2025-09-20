# FastAPI + html as web app framework. (lightweight, seamlessly interaction with the agent(in python))
# https://ai.pydantic.dev/examples/chat-app/

import fastapi
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import logfire
from pathlib import Path
import json
import io
import tempfile
import os
import sys
import glob
import csv

# Add parent directory to path to import project modules
sys.path.append(str(Path(__file__).parent.parent))


try:
  # from pd import process_discovery_pipeline
    from pnml import export_to_pnml
    from eval import evaluate_model
    # Import the main processing functions from the parent main.py
    from main import apply_inductive_miner, projection_based_on_organization, add_identifiers, post_processing
    
    # Try to import PM4Py for PNML reading
    try:
        from pm4py.objects.petri_net.importer import importer as pnml_importer
        from pm4py.objects.log.importer.xes import importer as xes_importer
        read_pnml = pnml_importer.apply
        
        def convert_petri_net_to_json(net, im, fm, org_name):
            """Convert Petri net to JSON format"""
            return {
                "places": [{"id": str(p), "name": str(p)} for p in net.places],
                "transitions": [{"id": str(t), "name": str(t)} for t in net.transitions],
                "arcs": [{"source": str(a.source), "target": str(a.target)} for a in net.arcs],
                "organization": org_name
            }
    except ImportError:
        # Fallback functions if PM4Py is not available
        def read_pnml(*args, **kwargs):
            raise ImportError("PM4Py not available")
        # def convert_petri_net_to_json(*args, **kwargs):
        #     return {"error": "PM4Py not available"}
        xes_importer = None
        
except ImportError:
    # Fallback if modules are not available
    print("Warning: Could not import project modules. Using mock functions.")
    def process_discovery_pipeline(*args, **kwargs):
        return {"places": [], "transitions": [], "arcs": []}
    def export_to_pnml(*args, **kwargs):
        return "<pnml></pnml>"
    def evaluate_model(*args, **kwargs):
        return {"fitness": 0.8, "precision": 0.75}
    def read_pnml(*args, **kwargs):
        raise ImportError("Modules not available")
    # def convert_petri_net_to_json(*args):
    #     return {"error": "Modules not available"}
    xes_importer = None

logfire.configure(send_to_logfire='if-token-present')

THIS_DIR = Path(__file__).parent

app = fastapi.FastAPI(title="Process Discovery TJN API")

# Mount visualizations directory to serve SVG files
if os.path.exists("../data/composed_pnml"):
    app.mount("/static/visualizations", StaticFiles(directory="../data/edited_processed_pnml"), name="visualizations")

# Mount webapp directory to serve JavaScript and other static files
app.mount("/static", StaticFiles(directory=str(THIS_DIR)), name="static")
logfire.instrument_fastapi(app)

@app.get('/')
async def index() -> FileResponse:
    return FileResponse((THIS_DIR / 'chat_app.html'), media_type='text/html')

@app.get('/pnml/{file_path:path}')
async def serve_pnml(file_path: str):
    """Serve PNML files for the visualizer"""
    try:
        # URL decode the file path to handle spaces and special characters
        from urllib.parse import unquote
        decoded_path = unquote(file_path)
        
        # Construct the full path
        full_path = THIS_DIR.parent / decoded_path
        
        # Check if file exists and is a PNML file
        if not full_path.exists():
            print(f"PNML file not found: {full_path}")
            raise HTTPException(status_code=404, detail=f"PNML file not found: {decoded_path}")
        
        if not str(full_path).endswith('.pnml'):
            raise HTTPException(status_code=400, detail="Not a PNML file")
        
        return FileResponse(full_path, media_type='application/xml')
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PNML file: {str(e)}")


@app.post('/export/pnml')
async def export_model_pnml(model_data: dict):
    """Export the discovered model to PNML format"""
    try:
        pnml_content = export_to_pnml(model_data)
        
        # Create a file-like object
        pnml_io = io.StringIO(pnml_content)
        
        return StreamingResponse(
            io.BytesIO(pnml_content.encode('utf-8')),
            media_type='application/xml',
            headers={"Content-Disposition": "attachment; filename=process_model.pnml"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# @app.on_event("startup")
# async def startup_event():
#     """Initialize the application with IP-1_initial_log.xes processing"""
#     try:
#         # Check if IP-1_initial_log.xes exists and process it if needed
#         pass
#     except Exception as e:
#         print(f"Error during startup processing: {e}")

@app.get('/available-xes-files')
async def get_available_xes_files():
    """Get all available XES files from the original_xes_file directory"""
    try:
        xes_files = []
        print("Checking for XES files in the original_xes_file directory...")
        
        # Check the data/original_xes_file directory for XES files
        xes_dir = "../data/original_xes_file"
        
        # If running from parent directory, use relative path
        if not os.path.exists(xes_dir):
            xes_dir = "./data/original_xes_file"
        
        # Additional fallback for different working directories
        if not os.path.exists(xes_dir):
            # Try absolute path based on current file location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            xes_dir = os.path.join(os.path.dirname(current_dir), "data", "original_xes_file")

        print(f"XES directory path: {xes_dir}")
        print(f"Directory exists: {os.path.exists(xes_dir)}")
        print(f"Current working directory: {os.getcwd()}")

        if os.path.exists(xes_dir):
            print("Checking for XES files in:",  xes_dir)
            file_patterns = glob.glob(f"{xes_dir}/*.xes")
            print(f"Found {len(file_patterns)} XES files")
            for xes_file in file_patterns:
                filename = os.path.basename(xes_file)
                file_name_without_ext = filename.replace('.xes', '')
              #  print(f'Processing XES file: {xes_file}')
                
                # Get file statistics
                file_stats = os.stat(xes_file)
                file_size_mb = round(file_stats.st_size / (1024 * 1024), 2)
                
                # Try to get basic log statistics if possible
                log_stats = {"error": "Statistics unavailable"}

                
                xes_files.append({
                    "id": file_name_without_ext,
                    "filename": filename,
                    "full_path": xes_file,
                    "size_mb": file_size_mb,
                    "log_statistics": log_stats,
                    "last_modified": file_stats.st_mtime
                })
        
        # Sort by filename for consistent ordering
        xes_files.sort(key=lambda x: x['filename'])
        
        return JSONResponse({
            "status": "success",
            "files": xes_files,
            "count": len(xes_files),
            "directory": xes_dir
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available XES files: {str(e)}")

@app.get('/related-models/{log_name}')
async def get_related_models(log_name: str):
    """Get related PNML models for a specific log file"""
    try:
        print(f"Looking for related models for log: {log_name}")
        models = []
        
        # Construct possible paths for the log folder
        possible_paths = [
            f"../data/{log_name}",  # For logs like IP-1_initial_log
            f"./data/{log_name}",
            f"../data/{log_name}_log",  # If the pattern is different
            f"./data/{log_name}_log"
        ]
        
        log_folder_path = None
        for path in possible_paths:
            if os.path.exists(path):
                log_folder_path = path
                print(f"Found log folder at: {log_folder_path}")
                break
        
        if not log_folder_path:
            # Try to find any folder that contains the log name
            data_dirs = ["../data", "./data"]
            for data_dir in data_dirs:
                if os.path.exists(data_dir):
                    for item in os.listdir(data_dir):
                        item_path = os.path.join(data_dir, item)
                        if os.path.isdir(item_path) and log_name in item:
                            log_folder_path = item_path
                            print(f"Found matching folder: {log_folder_path}")
                            break
                    if log_folder_path:
                        break
        
        if not log_folder_path:
            print(f"No folder found for {log_name}")
            return JSONResponse({
                "status": "success",
                "models": [],
                "count": 0,
                "message": f"No folder found for {log_name}"
            })
        
        # Check composed_pnml folder
        composed_folder = os.path.join(log_folder_path, "composed_pnml")
        if os.path.exists(composed_folder):
            pnml_files = glob.glob(os.path.join(composed_folder, "*.pnml"))
            print(f"Found {len(pnml_files)} composed PNML files")
            for pnml_file in pnml_files:
                model = create_model_info(pnml_file, "composed_pnml", log_name)
                if model:
                    models.append(model)
        
        # Check post_processed_pnml folder
        post_processed_folder = os.path.join(log_folder_path, "post_processed_pnml")
        if os.path.exists(post_processed_folder):
            pnml_files = glob.glob(os.path.join(post_processed_folder, "*.pnml"))
            print(f"Found {len(pnml_files)} post-processed PNML files")
            for pnml_file in pnml_files:
                model = create_model_info(pnml_file, "participant", log_name)
                if model:
                    models.append(model)
        
        # # Check first_pnml folder
        # first_folder = os.path.join(log_folder_path, "first_pnml")
        # if os.path.exists(first_folder):
        #     pnml_files = glob.glob(os.path.join(first_folder, "*.pnml"))
        #     print(f"Found {len(pnml_files)} first PNML files")
        #     for pnml_file in pnml_files:
        #         model = create_model_info(pnml_file, "first_pnml", log_name)
        #         if model:
        #             models.append(model)
        
        print(f"Total models found: {len(models)}")
        return JSONResponse({
            "status": "success",
            "models": models,
            "count": len(models),
            "log_name": log_name,
            "folder_path": log_folder_path
        })
        
    except Exception as e:
        print(f"Error in get_related_models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get related models: {str(e)}")

@app.get('/model/{modelId:path}')
def load_model(modelId: str):
    """Load a specific model by ID"""
    try:
        # Try different path configurations to handle different working directories
        model_path = f"../data/{modelId}"
        
        # If relative path doesn't work, try absolute path
        if not os.path.exists(model_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            absolute_model_path = os.path.join(os.path.dirname(current_dir), "data", modelId)
            if os.path.exists(absolute_model_path):
                model_path = absolute_model_path
            else:
                raise HTTPException(status_code=404, detail=f"Model {modelId} not found")
        
        # Return the PNML file
        return "todo"
    

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


def create_model_info(pnml_file, model_type, log_name):
    """Helper function to create model info from PNML file"""
    try:
        filename = os.path.basename(pnml_file)
        model_name = filename.replace('.pnml', '')
        
        # Extract organization name 
        if "Agent" in model_name:
            org_name = model_name.replace('filtered_log_', '').replace('composed_', '')
        else:
            org_name = model_name
        
        # Check for corresponding SVG file in the images folder
        log_folder = os.path.dirname(os.path.dirname(pnml_file))  # Go up two levels from pnml file
        svg_file = os.path.join(log_folder, "images", f"{model_name}.svg")
        has_svg = os.path.exists(svg_file)

        print(f"line 361: {log_name}/{model_type}/{model_name}.pnml")
        
        # Try to get statistics
        statistics = {"error": "Statistics unavailable"}
        try:
            net, im, fm = read_pnml(pnml_file)
            statistics = {
                "places": len(net.places),
                "transitions": len(net.transitions),
                "arcs": len(net.arcs)
            }
        except:
            # If PM4Py is not available, try to parse PNML manually
            with open(pnml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                place_count = content.count('<place')
                transition_count = content.count('<transition')
                arc_count = content.count('<arc')
                statistics = {
                    "places": place_count,
                    "transitions": transition_count,
                    "arcs": arc_count
                }

        
        return {
            "id": f"{log_name}/{model_type}/{model_name}.pnml",
            "name": f"{model_type}: {model_name}",
            "organization": org_name,
            "organizations": [org_name],
            "type": model_type.lower(),
            "pnml_path": pnml_file,
            "svg_path": svg_file if has_svg else None,
            "has_visualization": has_svg,
            "statistics": statistics,
            "file_size": round(os.path.getsize(pnml_file) / 1024, 2)  # KB
        }
    except Exception as e:
        print(f"Error creating model info for {pnml_file}: {e}")
        return None
    


# @app.post('/reprocess/{model_id}')
# async def reprocess_model(model_id: str):
#     """Reprocess a model using the main.py analysis functions"""
#     pass

def get_log_statistics(log_path):
    """Get basic statistics from an XES log file"""
    pass

async def get_organization_model(org_name: str):
    """Get model details for a specific organization"""
    try:
        # Read the post-processed PNML file
        pnml_path = f"../data/edited_processed_pnml/filtered_log_{org_name}.pnml"
        if not os.path.exists(pnml_path):
            pnml_path = f"../data/post_processed_pnml/filtered_log_{org_name}.pnml"
        
        if os.path.exists(pnml_path):
            net, im, fm = read_pnml(pnml_path)
            model_data = convert_petri_net_to_json(net, im, fm, org_name)
            
            return JSONResponse({
                "status": "success",
                "model": model_data,
                "organization": org_name,
                "source_file": f"../data/projected_xes/filtered_log_{org_name}.xes"
            })
        else:
            raise HTTPException(status_code=404, detail=f"No model found for organization {org_name}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load organization model: {str(e)}")



@app.get('/statistics/{log_name}')
def get_model_statistics(log_name):
    """Calculate statistics for the discovered model"""


    results_path = THIS_DIR / 'results.csv'
    stats = None
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            header = next(reader)
            for row in reader:
                if row and row[0].strip() == log_name:
                    # Defensive: handle missing columns
                    stats = {
                        "model": row[0],
                        "fitness": float(row[1]) if row[1] else None,
                        "precision": float(row[2]) if row[2] else None,
                        "entropy_fitness": float(row[3]) if len(row) > 3 and row[3] else None,
                        "entropy_precision": float(row[4]) if len(row) > 4 and row[4] else None
                    }
                    break
        if stats:
            return JSONResponse({"status": "success", "statistics": stats})
        else:
            return JSONResponse({"status": "not found", "message": f"No statistics for {log_name}"}, status_code=404)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading statistics: {str(e)}")



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app', reload=True, reload_dirs=[str(THIS_DIR)], host="0.0.0.0", port=8000
    )