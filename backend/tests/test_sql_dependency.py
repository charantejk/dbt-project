import unittest
import sys
import os
import json

# Add the parent directory to the path to be able to import the services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.sql_dependency_service import SQLDependencyService

class TestSQLDependencyService(unittest.TestCase):
    """Test the SQL dependency extraction functionality"""

    def setUp(self):
        self.dependency_service = SQLDependencyService()
    
    def test_extract_table_dependencies_simple(self):
        """Test extracting simple table dependencies"""
        sql = """
        SELECT a.id, a.name, b.value
        FROM users a
        JOIN orders b ON a.id = b.user_id
        WHERE a.active = true
        """
        
        # Extract dependencies
        dependencies = self.dependency_service.extract_table_dependencies(sql)
        
        # Check that we found both tables
        self.assertGreaterEqual(len(dependencies), 2)
        
        # Convert to a set of tuples for easier comparison
        table_names = {dep['table_name'] for dep in dependencies}
        self.assertIn('users', table_names)
        self.assertIn('orders', table_names)
    
    def test_extract_dbt_macros(self):
        """Test extracting dbt macros directly"""
        sql = """
        WITH users AS (
            SELECT * FROM {{ ref('stg_users') }}
        ),
        orders AS (
            SELECT * FROM {{ ref('stg_orders') }}
        )
        
        SELECT 
            u.id,
            u.name,
            COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        """
        
        # Extract dependencies using the direct macro extraction
        dependencies = self.dependency_service._extract_dbt_macros(sql)
        
        # Check that we found both refs
        self.assertEqual(len(dependencies), 2)
        
        # Check that they're correctly identified as dbt refs
        refs = [dep for dep in dependencies if dep.get('source_type') == 'dbt_ref']
        self.assertEqual(len(refs), 2)
        
        # Check the ref names
        ref_names = {ref['table_name'] for ref in refs}
        self.assertIn('stg_users', ref_names)
        self.assertIn('stg_orders', ref_names)
    
    def test_extract_dbt_sources(self):
        """Test extracting dbt source() macros directly"""
        sql = """
        WITH source_data AS (
            SELECT * FROM {{ source('raw', 'customers') }}
        ),
        other_source AS (
            SELECT * FROM {{ source('raw', 'orders') }}
        )
        
        SELECT 
            c.id,
            c.name,
            o.order_date
        FROM source_data c
        LEFT JOIN other_source o ON c.id = o.customer_id
        """
        
        # Extract dependencies using the direct macro extraction
        dependencies = self.dependency_service._extract_dbt_macros(sql)
        
        # Check that we found both sources
        self.assertEqual(len(dependencies), 2)
        
        # Check that they're correctly identified as dbt sources
        sources = [dep for dep in dependencies if dep.get('source_type') == 'dbt_source']
        self.assertEqual(len(sources), 2)
        
        # Check the source names and schemas
        for source in sources:
            self.assertEqual(source['schema'], 'raw')
            self.assertIn(source['table_name'], ['customers', 'orders'])
    
    def test_mixed_dependencies(self):
        """Test extracting mixed types of dependencies"""
        sql = """
        WITH model_data AS (
            SELECT * FROM {{ ref('stg_model') }}
        ),
        source_data AS (
            SELECT * FROM {{ source('raw', 'source_table') }}
        ),
        direct_table AS (
            SELECT * FROM public.some_table
        )
        
        SELECT 
            a.id,
            b.name,
            c.value
        FROM model_data a
        JOIN source_data b ON a.id = b.id
        JOIN direct_table c ON a.id = c.id
        """
        
        # Extract all dependencies
        dependencies = self.dependency_service.extract_table_dependencies(sql)
        
        # Should find all dependency types
        self.assertGreaterEqual(len(dependencies), 3)
        
        # Check each type is present
        dbt_refs = [dep for dep in dependencies if dep.get('source_type') == 'dbt_ref']
        dbt_sources = [dep for dep in dependencies if dep.get('source_type') == 'dbt_source']
        direct_tables = [dep for dep in dependencies if not dep.get('source_type') and 'some_table' in dep['table_name']]
        
        self.assertGreaterEqual(len(dbt_refs), 1)
        self.assertGreaterEqual(len(dbt_sources), 1)
        self.assertGreaterEqual(len(direct_tables), 1)
        
        # Verify specific tables
        ref_names = {ref['table_name'] for ref in dbt_refs}
        source_names = {src['table_name'] for src in dbt_sources}
        
        self.assertIn('stg_model', ref_names)
        self.assertIn('source_table', source_names)
        
        # Check for the direct table
        found_direct = False
        for dep in dependencies:
            if dep.get('table_name') == 'some_table' or dep.get('table_name') == 'public.some_table':
                found_direct = True
                break
        self.assertTrue(found_direct, "Direct table reference not found")
    
    def test_lineage_extraction(self):
        """Test the complete lineage extraction from models"""
        # Create test models
        models = [
            {
                "id": "project1_model1",
                "name": "model1",
                "project": "project1",
                "sql": "SELECT * FROM {{ ref('model2') }}"
            },
            {
                "id": "project1_model2",
                "name": "model2",
                "project": "project1",
                "sql": "SELECT * FROM {{ source('raw', 'table1') }}"
            },
            {
                "id": "project1_table1",
                "name": "table1",
                "project": "project1",
                "schema": "raw",
                "sql": "SELECT * FROM external_source"
            }
        ]
        
        # Extract lineage
        lineage = self.dependency_service.extract_lineage_from_models(models)
        
        # Should have 2 relationships
        self.assertEqual(len(lineage), 2)
        
        # Check the relationships
        model1_deps = [l for l in lineage if l['target'] == 'project1_model1']
        model2_deps = [l for l in lineage if l['target'] == 'project1_model2']
        
        # model1 depends on model2
        self.assertEqual(len(model1_deps), 1)
        self.assertEqual(model1_deps[0]['source'], 'project1_model2')
        self.assertEqual(model1_deps[0]['type'], 'ref')
        
        # model2 depends on table1
        self.assertEqual(len(model2_deps), 1)
        self.assertEqual(model2_deps[0]['source'], 'project1_table1')
        self.assertEqual(model2_deps[0]['type'], 'source')

if __name__ == '__main__':
    unittest.main() 