# Process-Discovery-Typed-Jackson-Nets


## ! Important Prerequirement: **Git Large File Storage (LFS)** Required for Large Data Files

### 1. Installing Git LFS on Windows

- Download and install from the official site:  
  [https://git-lfs.github.com/](https://git-lfs.github.com/)

- Or install via Windows package manager (`winget`):

  ```
  winget install Git.GitLFS
  ```

### Or: Installing Git LFS on MAC
```
brew install git-lfs 
```

### 2. Git clone

```
git clone https://github.com/XufanLU/Process-Discovery-Typed-Jackson-Nets.git
```

### 3.( Optional: If you do not see the event logs *.xes for TASE ) Enter the repository and initialize Git LFS in your repo

```
cd Process-Discovery-Typed-Jackson-Nets
```
```
git lfs install
```
```
git lfs fetch --all
```


## How to use the webapp


Enter the repository

```
cd Process-Discovery-Typed-Jackson-Nets
```
### 1. Create a venv and activate 
```
python -m venv .pd
```
```
source .pd/bin/activate
```


### 2. Install the dependencies
```
pip install -r requirements.txt
```

Note: graphviz also needs to be installed on the device . Please check if it is installed:
```
dot -V 
```

### 3. Run webapp (frontend + backend)
```
python webapp/main.py
```






## File Structure

### `data/`

- `data/original_xes_file/`  
  Contains all the initial XES logs.

- `data/**log/`  
  Contains all the processed files, organized as follows:

  - `data/**log/projected_xes/`  
    Event logs filtered based on organizations (agents).

  - `data/**log/first_pnml/`  
    Initial PNML models discovered using the inductive miner on the projected XES files.

  - `data/**log/post_processed_pnml/`  
    Models after removing source and sink places.

  - `data/**log/composed_pnml/`  
    Composed models with minor places removed.

  - `data/**log/fully_composed_pnml/`  
    Composed models with source and sink places restored.

  - `data/**log/images/`  
    SVG files representing all the models.


### `webapp/ `
webapp/main.py is the main app. this will serve the html wih the process-dicovery-app.js in it 

### `main.py`
The implementation of the algorithm.



