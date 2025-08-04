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

# Add parent directory to path to import project modules
sys.path.append(str(Path(__file__).parent.parent))


try:
  # from pd import process_discovery_pipeline
    from pnml import export_to_pnml
    from eval import evaluate_model
    # Import the main processing functions from the parent main.py
    from main import apply_inductive_miner, projection_based_on_organization, add_identifiers, post_processing
except ImportError:
    # Fallback if modules are not available
    print("Warning: Could not import project modules. Using mock functions.")
    def process_discovery_pipeline(*args, **kwargs):
        return {"places": [], "transitions": [], "arcs": []}
    def export_to_pnml(*args, **kwargs):
        return "<pnml></pnml>"
    def evaluate_model(*args, **kwargs):
        return {"fitness": 0.8, "precision": 0.75}

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


@app.on_event("startup")
async def startup_event():
    """Initialize the application with IP-1_initial_log.xes processing"""
    try:
        # Check if IP-1_initial_log.xes exists and process it if needed
        pass
    except Exception as e:
        print(f"Error during startup processing: {e}")

@app.get('/analyzed-models')
async def get_analyzed_models():
    """Get all previously analyzed models from edited_processed_pnml folder"""
    try:
        models = []
        
        # Check the edited_processed_pnml directory for existing models
        pnml_dir = "../data/edited_processed_pnml"
        if not os.path.exists(pnml_dir):
            pnml_dir = "./data/edited_processed_pnml"
        if os.path.exists(pnml_dir):
            pnml_files = glob.glob(f"{pnml_dir}/*.pnml")
            
            for pnml_file in pnml_files:
                filename = os.path.basename(pnml_file)
                model_name = filename.replace('.pnml', '')
                
                # Extract organization name (Agent 1, Agent 2, etc.)
                org_name = model_name.replace('filtered_log_', '')
                
                # Check for corresponding SVG file
                svg_file = pnml_file.replace('.pnml', '.svg')
                has_svg = os.path.exists(svg_file)
                
                try:
                    # Try to read PNML to get basic statistics using PM4Py if available
                    statistics = {"error": "Statistics unavailable"}
                    try:
                        net, im, fm = read_pnml(pnml_file)
                        statistics = {
                            "places": len(net.places),
                            "transitions": len(net.transitions),
                            "arcs": len(net.arcs)
                        }
                    except:
                        # If PM4Py is not available, try to parse PNML manually for basic info
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
                    
                    models.append({
                        "id": model_name,
                        "name": model_name,
                        "organization": org_name,
                        "organizations": [org_name],
                        "pnml_path": pnml_file,
                        "svg_path": svg_file if has_svg else None,
                        "has_visualization": has_svg,
                        "statistics": statistics,
                        "file_size": round(os.path.getsize(pnml_file) / 1024, 2)  # KB
                    })
                except Exception as e:
                    print(f"Error reading {pnml_file}: {e}")
                    # Still add the model even if we can't read it
                    models.append({
                        "id": model_name,
                        "name": model_name,
                        "organization": org_name,
                        "organizations": [org_name],
                        "pnml_path": pnml_file,
                        "svg_path": svg_file if has_svg else None,
                        "has_visualization": has_svg,
                        "statistics": {"error": "Could not read model"},
                        "file_size": round(os.path.getsize(pnml_file) / 1024, 2)
                    })
        
        return JSONResponse({
            "status": "success",
            "models": models,
            "count": len(models)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analyzed models: {str(e)}")

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
                print(f'Processing XES file: {xes_file}')
                
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
                model = create_model_info(pnml_file, "Composed", log_name)
                if model:
                    models.append(model)
        
        # Check post_processed_pnml folder
        post_processed_folder = os.path.join(log_folder_path, "post_processed_pnml")
        if os.path.exists(post_processed_folder):
            pnml_files = glob.glob(os.path.join(post_processed_folder, "*.pnml"))
            print(f"Found {len(pnml_files)} post-processed PNML files")
            for pnml_file in pnml_files:
                model = create_model_info(pnml_file, "Post-processed", log_name)
                if model:
                    models.append(model)
        
        # Check first_pnml folder
        first_folder = os.path.join(log_folder_path, "first_pnml")
        if os.path.exists(first_folder):
            pnml_files = glob.glob(os.path.join(first_folder, "*.pnml"))
            print(f"Found {len(pnml_files)} first PNML files")
            for pnml_file in pnml_files:
                model = create_model_info(pnml_file, "Initial", log_name)
                if model:
                    models.append(model)
        
        # Check edited_processed_pnml folder (additional fallback)
        edited_folder = os.path.join(log_folder_path, "edited_processed_pnml")
        if os.path.exists(edited_folder):
            pnml_files = glob.glob(os.path.join(edited_folder, "*.pnml"))
            print(f"Found {len(pnml_files)} edited PNML files")
            for pnml_file in pnml_files:
                model = create_model_info(pnml_file, "Edited", log_name)
                if model:
                    models.append(model)
        
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
            "id": f"{log_name}_{model_type}_{model_name}",
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
    


@app.post('/reprocess/{model_id}')
async def reprocess_model(model_id: str):
    """Reprocess a model using the main.py analysis functions"""
    pass

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

async def get_initial_log_info():
    """Get information about the initial log"""
    try:
        log_path = "../data/IP-1_initial_log.xes"
        if os.path.exists(log_path):
            # Read log to get basic statistics
            log = xes_importer.apply(log_path)
            
            return JSONResponse({
                "status": "success",
                "log_info": {
                    "path": log_path,
                    "traces": len(log),
                    "events": sum(len(trace) for trace in log),
                    "size_mb": os.path.getsize(log_path) / (1024 * 1024)
                }
            })
        else:
            raise HTTPException(status_code=404, detail="Initial log not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get initial log info: {str(e)}")





def calculate_model_statistics(model_data):
    """Calculate statistics for the discovered model"""
    pass



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app', reload=True, reload_dirs=[str(THIS_DIR)], host="0.0.0.0", port=8000
    )