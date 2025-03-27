#!/bin/bash

# Extract lineage from dbt projects
echo "Running advanced SQL lineage extraction..."
python setup_dbt_projects.py

# Run tests for the SQL dependency service
echo "Running SQL dependency tests..."
python setup_dbt_projects.py test 