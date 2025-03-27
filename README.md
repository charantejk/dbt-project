remove all the chartd# DBT Metadata Explorer

A comprehensive web application for exploring, visualizing, and documenting your dbt projects' metadata with AI-enhanced descriptions.

## Quick Start Guide

### Backend Setup

1. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the `backend` directory (optional):
   ```
   # Optional: Gemini API key for AI-generated descriptions
   GEMINI_API_KEY=your-api-key-here
   
   # Optional: Enable/disable AI descriptions
   ENABLE_AI_DESCRIPTIONS=true
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

### Start the Backend

1. Run the backend server, pointing to your dbt projects directory:
   ```bash
   cd backend
   python run.py --projects-dir "/path/to/your/dbt/projects"
   ```

   By default, the server will run on `http://0.0.0.0:8000`.

   **Note**: Replace `/path/to/your/dbt/projects` with the actual path to your dbt projects directory. This should be a directory containing one or more dbt project folders.

### Start the Frontend

1. In a new terminal, start the frontend development server:
   ```bash
   cd frontend
   npm start
   ```

   The frontend will be available at `http://localhost:3000`.

## How the Project Works

### Architecture Overview

The DBT Metadata Explorer is built with a modern architecture:

1. **Backend**: Python FastAPI application that parses dbt projects and serves metadata through RESTful APIs
2. **Frontend**: React TypeScript application that provides an intuitive UI for exploring the metadata
3. **AI Integration**: Google's Gemini API for generating intelligent descriptions of models and columns
4. **Advanced Lineage Extraction**: SQL parsing for accurate data lineage detection

### Backend Components

The backend handles several key functions:

1. **Project Discovery**: Scans the specified directory for dbt projects
2. **Metadata Parsing**: Extracts metadata from dbt manifest.json files
3. **Cross-Project Linking**: Identifies and links related models across different projects
4. **AI Description Generation**: Uses Gemini API to generate human-readable descriptions
5. **File Watching**: Monitors dbt projects for changes and updates metadata automatically
6. **API Endpoints**: Provides RESTful APIs for the frontend to consume
7. **Advanced SQL Parsing**: Extracts table dependencies from SQL code for accurate lineage

The main components are:
- `metadata_service.py`: Core service that processes dbt metadata
- `dbt_metadata_parser.py`: Parses dbt manifest files
- `ai_description_service.py`: Generates AI descriptions using Gemini
- `file_watcher_service.py`: Monitors for file changes
- `sql_dependency_service.py`: Advanced SQL parsing for lineage extraction

### Frontend Components

The frontend provides an intuitive interface for exploring the metadata:

1. **Dashboard**: Overview of projects, models, and statistics
2. **Models Explorer**: Browse, search, and filter models across all projects
3. **Model Detail View**: View detailed information about a specific model
4. **Lineage Visualization**: Interactive graph showing relationships between models
5. **Export Functionality**: Export metadata to JSON or YAML format

Key components include:
- `App.tsx`: Main application component
- `ModelsTable.tsx`: Table view of all models with search and filter
- `ModelDetail.tsx`: Detailed view of a single model
- `LineageGraph.tsx`: Visual representation of model dependencies
- `DescriptionEdit.tsx`: Interface for editing AI-generated descriptions

### Data Flow

1. The backend scans dbt projects and extracts metadata
2. SQL code is parsed to extract table dependencies and build lineage graphs
3. AI descriptions are generated for models and columns
4. The frontend fetches this data via API calls
5. Users can browse, search, and visualize the unified schema
6. Users can edit AI-generated descriptions, which are saved back to the backend
7. Changes to dbt projects are detected automatically, and metadata is refreshed

### Key Features

- **Multi-Project Aggregation**: Combines multiple dbt projects into a unified schema
- **Cross-Project Lineage**: Shows dependencies between models across different projects
- **AI-Generated Descriptions**: Automatically generates human-readable descriptions
- **User Corrections**: Allows users to refine AI-generated descriptions
- **Dynamic Documentation**: Updates automatically as dbt models change
- **Export Functionality**: Exports schema and metadata in JSON/YAML format
- **Advanced Lineage Extraction**: Uses SQL parsing to extract accurate lineage relationships

## Advanced Lineage Extraction

The project incorporates advanced SQL parsing techniques, inspired by ChartDB, to extract accurate lineage relationships:

### How It Works

1. **SQL Parsing**: Uses both regex-based detection and structured SQL parsing to extract table dependencies
2. **dbt Macro Support**: Detects and processes dbt-specific macros like `ref()` and `source()`
3. **Schema Resolution**: Resolves schema and table references across projects
4. **Dependency Graph**: Creates a complete directed graph of model dependencies

### Testing the Lineage Extraction

Run the lineage extraction tests:
```bash
./extract_lineage.sh
```

Or run the tests directly:
```bash
python setup_dbt_projects.py test
```

## Troubleshooting

### Backend Issues

- If you see an error about missing dependencies, ensure you've installed all requirements:
  ```bash
  pip install -r backend/requirements.txt
  ```

- If the backend can't find your dbt projects, check the path provided to `--projects-dir`

- For AI description issues, ensure your Gemini API key is correctly set in the `.env` file

- If you encounter SQL parsing issues, check that `sqlparse` and `sqlglot` are installed:
  ```bash
  pip install sqlparse sqlglot
  ```

### Frontend Issues

- If you encounter dependency issues, try:
  ```bash
  cd frontend
  rm -rf node_modules
  npm install
  ```

- If the frontend can't connect to the backend, ensure the backend is running and check for any CORS issues
