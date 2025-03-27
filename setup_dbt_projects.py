import os
import json
import shutil
import subprocess
import glob
import re
import sys
from typing import Dict, Any

# Add the backend folder to path so we can import from services
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

# Import our services
from backend.services.metadata_service import MetadataService
from backend.services.dbt_metadata_parser import parse_dbt_projects, save_metadata

def create_directories(path):
    """Create directories if they don't exist"""
    if not os.path.exists(path):
        os.makedirs(path)

def create_file(path, content):
    """Create a file with the given content"""
    with open(path, 'w') as f:
        f.write(content)

def setup_dbt_projects():
    """Set up sample dbt projects for the application"""
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_dbt_projects')
    
    # Create the base directory for sample projects
    create_directories(base_dir)
    
    projects = ['ecommerce', 'finance', 'marketing']
    
    for project in projects:
        project_dir = os.path.join(base_dir, project)
        
        # Create project directories
        create_directories(project_dir)
        create_directories(os.path.join(project_dir, 'models'))
        create_directories(os.path.join(project_dir, 'models', 'staging'))
        create_directories(os.path.join(project_dir, 'models', 'marts'))
        
        # Create dbt_project.yml
        create_file(
            os.path.join(project_dir, 'dbt_project.yml'),
            f"""name: '{project}'
version: '1.0.0'
config-version: 2

profile: '{project}'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

models:
  {project}:
    staging:
      +materialized: view
    marts:
      +materialized: table
"""
        )
        
        # Create basic source files
        create_file(
            os.path.join(project_dir, 'models', 'sources.yml'),
            f"""version: 2

sources:
  - name: {project}
    database: raw_data
    schema: {project}
    tables:
      - name: raw_orders
        description: Raw orders data
        columns:
          - name: order_id
            description: Unique order identifier
          - name: customer_id
            description: Customer identifier
          - name: order_date
            description: Date when the order was placed
          - name: status
            description: Order status
          - name: amount
            description: Order amount
"""
        )
    
    # Create specific models for each project
    create_ecommerce_models(os.path.join(base_dir, 'ecommerce'))
    create_finance_models(os.path.join(base_dir, 'finance'))
    create_marketing_models(os.path.join(base_dir, 'marketing'))
    
    print(f"Sample dbt projects created in {base_dir}")
    return base_dir

def create_ecommerce_models(project_dir):
    """Create models for the ecommerce project"""
    # Staging models
    create_file(
        os.path.join(project_dir, 'models', 'staging', 'stg_orders.sql'),
        """WITH source_data AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        status,
        amount
    FROM {{ source('ecommerce', 'raw_orders') }}
)

SELECT
    order_id,
    customer_id,
    order_date,
    status,
    amount
FROM source_data"""
    )
    
    create_file(
        os.path.join(project_dir, 'models', 'staging', 'stg_customers.sql'),
        """WITH source_data AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        registration_date,
        segment
    FROM {{ source('ecommerce', 'raw_customers') }}
)

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    registration_date,
    segment
FROM source_data"""
    )
    
    # Mart models
    create_file(
        os.path.join(project_dir, 'models', 'marts', 'customer_orders.sql'),
        """WITH customers AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        segment
    FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        status,
        amount
    FROM {{ ref('stg_orders') }}
),

customer_orders AS (
    SELECT
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.segment,
        COUNT(o.order_id) AS order_count,
        SUM(o.amount) AS total_spend,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS most_recent_order_date
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY 1, 2, 3, 4, 5
)

SELECT * FROM customer_orders"""
    )

def create_finance_models(project_dir):
    """Create models for the finance project"""
    # Staging models
    create_file(
        os.path.join(project_dir, 'models', 'staging', 'stg_transactions.sql'),
        """WITH source_data AS (
    SELECT
        transaction_id,
        order_id,
        transaction_date,
        payment_method,
        amount,
        status
    FROM {{ source('finance', 'raw_transactions') }}
)

SELECT
    transaction_id,
    order_id,
    transaction_date,
    payment_method,
    amount,
    status
FROM source_data"""
    )
    
    # Mart models
    create_file(
        os.path.join(project_dir, 'models', 'marts', 'order_revenue.sql'),
        """-- This model links with data from ecommerce project using order_id as the common key

WITH transactions AS (
    SELECT
        transaction_id,
        order_id,
        transaction_date,
        payment_method,
        amount,
        status
    FROM {{ ref('stg_transactions') }}
    WHERE status = 'completed'
),

-- Cross-project reference
ecommerce_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date
    FROM {{ ref('stg_orders', 'ecommerce') }}
),

order_revenue AS (
    SELECT
        t.order_id,
        eo.customer_id,
        eo.order_date,
        t.transaction_date,
        SUM(t.amount) AS revenue,
        COUNT(t.transaction_id) AS transaction_count,
        MAX(t.payment_method) AS payment_method
    FROM transactions t
    LEFT JOIN ecommerce_orders eo ON t.order_id = eo.order_id
    GROUP BY 1, 2, 3, 4
)

SELECT * FROM order_revenue"""
    )

def create_marketing_models(project_dir):
    """Create models for the marketing project"""
    # Staging models
    create_file(
        os.path.join(project_dir, 'models', 'staging', 'stg_campaigns.sql'),
        """WITH source_data AS (
    SELECT
        campaign_id,
        campaign_name,
        channel,
        start_date,
        end_date,
        budget,
        target_segment
    FROM {{ source('marketing', 'raw_campaigns') }}
)

SELECT
    campaign_id,
    campaign_name,
    channel,
    start_date,
    end_date,
    budget,
    target_segment
FROM source_data"""
    )
    
    create_file(
        os.path.join(project_dir, 'models', 'staging', 'stg_customer_interactions.sql'),
        """WITH source_data AS (
    SELECT
        interaction_id,
        customer_id,
        campaign_id,
        interaction_date,
        channel,
        interaction_type,
        conversion_flag
    FROM {{ source('marketing', 'raw_customer_interactions') }}
)

SELECT
    interaction_id,
    customer_id,
    campaign_id,
    interaction_date,
    channel,
    interaction_type,
    conversion_flag
FROM source_data"""
    )
    
    # Mart models
    create_file(
        os.path.join(project_dir, 'models', 'marts', 'campaign_performance.sql'),
        """-- This model links with data from ecommerce and finance projects

WITH campaigns AS (
    SELECT
        campaign_id,
        campaign_name,
        channel,
        start_date,
        end_date,
        budget,
        target_segment
    FROM {{ ref('stg_campaigns') }}
),

interactions AS (
    SELECT
        interaction_id,
        customer_id,
        campaign_id,
        interaction_date,
        channel,
        interaction_type,
        conversion_flag
    FROM {{ ref('stg_customer_interactions') }}
),

-- Cross-project reference to ecommerce
customer_data AS (
    SELECT
        customer_id,
        segment,
        order_count,
        total_spend
    FROM {{ ref('customer_orders', 'ecommerce') }}
),

-- Cross-project reference to finance
revenue_data AS (
    SELECT
        customer_id,
        SUM(revenue) as total_revenue
    FROM {{ ref('order_revenue', 'finance') }}
    GROUP BY 1
),

campaign_performance AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.channel,
        c.start_date,
        c.end_date,
        c.budget,
        c.target_segment,
        COUNT(DISTINCT i.customer_id) AS reached_customers,
        COUNT(DISTINCT CASE WHEN i.conversion_flag = true THEN i.customer_id END) AS converted_customers,
        SUM(CASE WHEN i.conversion_flag = true THEN cd.order_count ELSE 0 END) AS attributed_orders,
        SUM(CASE WHEN i.conversion_flag = true THEN rd.total_revenue ELSE 0 END) AS attributed_revenue,
        CASE 
            WHEN c.budget > 0 THEN SUM(CASE WHEN i.conversion_flag = true THEN rd.total_revenue ELSE 0 END) / c.budget 
            ELSE 0 
        END AS roi
    FROM campaigns c
    LEFT JOIN interactions i ON c.campaign_id = i.campaign_id
    LEFT JOIN customer_data cd ON i.customer_id = cd.customer_id
    LEFT JOIN revenue_data rd ON i.customer_id = rd.customer_id
    GROUP BY 1, 2, 3, 4, 5, 6, 7
)

SELECT * FROM campaign_performance"""
    )

if __name__ == "__main__":
    setup_mode = len(sys.argv) > 1 and sys.argv[1] == "setup"
    run_tests = len(sys.argv) > 1 and sys.argv[1] == "test"
    
    if setup_mode:
        print("Setting up dbt projects...")
        setup_dbt_projects()
    elif run_tests:
        print("Running tests...")
        # Run the SQL dependency tests
        import unittest
        from backend.tests.test_sql_dependency import TestSQLDependencyService
        
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSQLDependencyService)
        unittest.TextTestRunner(verbosity=2).run(test_suite)
    else:
        print("Refreshing metadata with enhanced lineage extraction...")
        # Initialize the metadata service with the sample dbt projects
        # Try different project paths based on where the projects might be
        potential_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbt_pk", "dbt"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_dbt_projects"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbt_projects"),
        ]
        
        projects_dir = None
        for path in potential_paths:
            if os.path.exists(path) and os.listdir(path):
                projects_dir = path
                break
        
        if not projects_dir:
            print("Warning: No dbt projects found. Setting up sample projects...")
            setup_dbt_projects()
            projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_dbt_projects")
            
            # Also copy to dbt_pk/dbt for compatibility with existing code
            dbt_pk_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dbt_pk", "dbt")
            os.makedirs(dbt_pk_dir, exist_ok=True)
            for item in os.listdir(projects_dir):
                src = os.path.join(projects_dir, item)
                dst = os.path.join(dbt_pk_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            projects_dir = dbt_pk_dir
            
        print(f"Using dbt projects directory: {projects_dir}")
        metadata_service = MetadataService(dbt_projects_dir=projects_dir)
        
        # Refresh the metadata to extract lineage with the new SQL parsing approach
        metadata_service.refresh()
        
        # Print summary of the extracted lineage
        lineage = metadata_service.get_lineage()
        print(f"\nExtracted {len(lineage)} lineage relationships")
        
        if lineage:
            print("\nSample lineage relationships:")
            for i, link in enumerate(lineage[:5]):
                print(f"  {link.get('source', 'unknown')} → {link.get('target', 'unknown')} ({link.get('type', 'unknown')})")
        
        print("\nSetup and lineage extraction complete.")
        print("\nTo run the application:")
        print("1. Run the backend: ./start.sh")
        print("2. In another terminal, run the frontend: cd frontend && npm start")
        print("3. Open http://localhost:3000 in your browser") 