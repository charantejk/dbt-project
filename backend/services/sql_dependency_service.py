import re
import json
from typing import List, Dict, Any, Optional, Tuple, Set
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function, Parenthesis, Token
from sqlparse.tokens import Keyword, DML, Wildcard, Name, Punctuation
import logging

logger = logging.getLogger(__name__)

class SQLDependencyService:
    """
    Service for extracting table dependencies from SQL code
    Based on ChartDB's db-dependency.ts functionality
    """
    
    def __init__(self):
        try:
            from sqlparse import parse, sql
            from sqlparse.tokens import DML, Keyword
            self.sqlparse_available = True
        except ImportError:
            print("Warning: sqlparse not available, installing...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'sqlparse'])
            from sqlparse import parse, sql
            from sqlparse.tokens import DML, Keyword
            self.sqlparse_available = True
        
        try:
            from sqlglot import parse as sqlglot_parse, expressions
            self.sqlglot_available = True
        except ImportError:
            print("Warning: sqlglot not available, installing...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'sqlglot'])
            from sqlglot import parse as sqlglot_parse, expressions
            self.sqlglot_available = True
    
    def extract_table_dependencies(self, sql_code: str) -> List[Dict[str, str]]:
        """
        Extract table dependencies from SQL code
        Returns a list of dicts with schema and table name
        """
        if not sql_code:
            return []
        
        # Extract dbt macros first (ref and source calls)
        tables_from_dbt = self._extract_dbt_macros(sql_code)
        
        # Try SQL parsing for regular tables - this might fail on dbt templates
        try:
            # We need to preprocess SQL to remove dbt macros before parsing
            clean_sql = self._remove_dbt_macros(sql_code)
            tables_from_sqlglot = self._extract_tables_sqlglot(clean_sql)
        except Exception as e:
            print(f"SQL parsing error (continuing with regex-based parsing): {e}")
            tables_from_sqlglot = []
        
        # Always try regex as a fallback
        tables_from_regex = self._extract_tables_regex(sql_code)
        
        # Combine results from all methods
        combined_tables = tables_from_dbt.copy()
        
        # Add tables from sqlglot if they're not already in the list
        for table in tables_from_sqlglot:
            table_key = f"{table.get('schema', '')}.{table['table_name']}"
            if not any(f"{t.get('schema', '')}.{t['table_name']}" == table_key for t in combined_tables):
                combined_tables.append(table)
        
        # Add tables from regex if they're not already in the list
        for table in tables_from_regex:
            table_key = f"{table.get('schema', '')}.{table['table_name']}"
            if not any(f"{t.get('schema', '')}.{t['table_name']}" == table_key for t in combined_tables):
                combined_tables.append(table)
        
        # Filter out duplicate tables without schema
        filtered_tables = self._filter_duplicate_tables(combined_tables)
        
        return filtered_tables
    
    def _extract_dbt_macros(self, sql_code: str) -> List[Dict[str, str]]:
        """
        Extract tables referenced in dbt macros like ref() and source()
        """
        if not sql_code:
            return []
            
        tables = []
        
        # Pattern for ref() macros: {{ ref('model_name') }}
        ref_pattern = r'{{\s*ref\([\'"]([^\'"]+)[\'"]\)\s*}}'
        for match in re.finditer(ref_pattern, sql_code):
            model_name = match.group(1)
            tables.append({
                'schema': None,
                'table_name': model_name,
                'source_type': 'dbt_ref'
            })
        
        # Pattern for source() macros: {{ source('source_name', 'table_name') }}
        source_pattern = r'{{\s*source\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)\s*}}'
        for match in re.finditer(source_pattern, sql_code):
            source_name, table_name = match.groups()
            tables.append({
                'schema': source_name,
                'table_name': table_name,
                'source_type': 'dbt_source'
            })
            
        return tables
    
    def _remove_dbt_macros(self, sql_code: str) -> str:
        """
        Remove dbt macros from SQL code to make it parseable by standard SQL parsers
        Replaces {{ ... }} with placeholder tables
        """
        if not sql_code:
            return ""
            
        # Replace ref() macros with placeholder table references
        sql_code = re.sub(
            r'{{\s*ref\([\'"]([^\'"]+)[\'"]\)\s*}}',
            lambda m: f"ref_{m.group(1)}",
            sql_code
        )
        
        # Replace source() macros with placeholder table references
        sql_code = re.sub(
            r'{{\s*source\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)\s*}}',
            lambda m: f"{m.group(1)}_{m.group(2)}",
            sql_code
        )
        
        # Replace any other macros/jinja with empty string
        sql_code = re.sub(r'{%.*?%}', '', sql_code)
        sql_code = re.sub(r'{{.*?}}', '', sql_code)
        
        return sql_code
    
    def _extract_tables_sqlglot(self, sql_code: str) -> List[Dict[str, str]]:
        """Extract tables using sqlglot parser"""
        try:
            from sqlglot import parse as sqlglot_parse
            
            # Preprocess SQL to handle some common issues
            sql_code = self._preprocess_sql(sql_code)
            
            # Parse SQL using sqlglot
            parsed = sqlglot_parse(sql_code)
            
            tables = []
            for statement in parsed:
                # Recursively extract table references from the AST
                for table_ref in self._extract_table_refs_from_sqlglot(statement):
                    schema = table_ref.get('schema')
                    table_name = table_ref.get('table')
                    
                    if table_name:
                        tables.append({
                            'schema': schema,
                            'table_name': table_name
                        })
            
            return tables
            
        except Exception as e:
            print(f"Error parsing SQL with sqlglot: {e}")
            return []
    
    def _extract_table_refs_from_sqlglot(self, node) -> List[Dict[str, str]]:
        """
        Recursively extract table references from sqlglot AST
        Returns a list of dicts with schema and table info
        """
        tables = []
        
        if hasattr(node, 'args'):
            # This is a SQL expression or statement
            for arg_name, arg_value in node.args.items():
                if arg_name == 'this' and hasattr(arg_value, 'name') and hasattr(arg_value, 'db'):
                    # This might be a table reference
                    table_info = {
                        'table': getattr(arg_value, 'name', None),
                        'schema': getattr(arg_value, 'db', None)
                    }
                    if table_info['table']:
                        tables.append(table_info)
                
                # Recursively process nested nodes
                if isinstance(arg_value, (list, tuple)):
                    for item in arg_value:
                        tables.extend(self._extract_table_refs_from_sqlglot(item))
                elif hasattr(arg_value, 'args'):
                    tables.extend(self._extract_table_refs_from_sqlglot(arg_value))
        
        return tables
    
    def _extract_tables_regex(self, sql_code: str) -> List[Dict[str, str]]:
        """Extract tables using regex patterns for common SQL patterns"""
        if not sql_code:
            return []
        
        # Preprocess SQL to handle common issues
        sql_code = self._preprocess_sql(sql_code)
        
        tables = []
        
        # Pattern for FROM and JOIN clauses with optional schema
        # This pattern handles quoted and unquoted identifiers
        table_pattern = r'(?:FROM|JOIN)\s+(?:([a-zA-Z0-9_"]+)\.)?([a-zA-Z0-9_"]+)'
        for match in re.finditer(table_pattern, sql_code, re.IGNORECASE):
            schema, table_name = match.groups()
            
            # Remove quotes if present
            if schema and (schema.startswith('"') or schema.startswith('`')):
                schema = schema[1:-1]
            if table_name and (table_name.startswith('"') or table_name.startswith('`')):
                table_name = table_name[1:-1]
            
            # Skip common SQL functions that might be mistaken for tables
            if table_name.lower() in ('select', 'where', 'group', 'having', 'order', 'limit'):
                continue
                
            tables.append({
                'schema': schema,
                'table_name': table_name
            })
        
        # Pattern for source() and ref() macros in dbt
        dbt_source_pattern = r'{{\s*source\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)\s*}}'
        for match in re.finditer(dbt_source_pattern, sql_code):
            source_name, table_name = match.groups()
            tables.append({
                'schema': source_name,  # In dbt, source first param is like a schema
                'table_name': table_name,
                'source_type': 'dbt_source'
            })
        
        dbt_ref_pattern = r'{{\s*ref\([\'"]([^\'"]+)[\'"]\)\s*}}'
        for match in re.finditer(dbt_ref_pattern, sql_code):
            ref_name = match.group(1)
            tables.append({
                'schema': None,
                'table_name': ref_name,
                'source_type': 'dbt_ref'
            })
        
        return tables
    
    def _filter_duplicate_tables(self, tables: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter out duplicate tables without schema
        If we have tables with the same name but different schemas, prioritize the one with schema
        """
        table_map = {}
        
        for table in tables:
            table_name = table['table_name']
            existing_table = table_map.get(table_name)
            
            # If we don't have this table yet, or the new one has schema but existing doesn't
            if not existing_table or (table.get('schema') and not existing_table.get('schema')):
                table_map[table_name] = table
        
        return list(table_map.values())
    
    def _preprocess_sql(self, sql_code: str) -> str:
        """Preprocess SQL to handle common issues that might cause parsing problems"""
        if not sql_code:
            return ""
        
        # Remove comments
        sql_code = re.sub(r'--.*$', '', sql_code, flags=re.MULTILINE)
        sql_code = re.sub(r'/\*.*?\*/', '', sql_code, flags=re.DOTALL)
        
        # Normalize whitespace
        sql_code = re.sub(r'\s+', ' ', sql_code).strip()
        
        # Handle Jinja/dbt macros by replacing them with placeholders
        # Replace {{ config(...) }} with empty string
        sql_code = re.sub(r'{{\s*config\([^}]*\)\s*}}', '', sql_code)
        
        # For other macros, we'll leave them as is for now as they might contain table references
        
        return sql_code
    
    def extract_lineage_from_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract lineage relationships from a list of dbt models
        Returns a list of source->target relationships
        """
        lineage = []
        model_by_name = {}
        
        # First, build a lookup of models by name
        for model in models:
            model_name = model.get('name')
            if model_name:
                if model_name not in model_by_name:
                    model_by_name[model_name] = []
                model_by_name[model_name].append(model)
        
        # Then process each model to extract dependencies
        for target_model in models:
            sql = target_model.get('sql', '')
            if not sql:
                continue
                
            # Extract table dependencies from the SQL
            table_deps = self.extract_table_dependencies(sql)
            
            for dep in table_deps:
                source_type = dep.get('source_type')
                table_name = dep.get('table_name')
                schema_name = dep.get('schema')
                
                if source_type == 'dbt_ref' and table_name in model_by_name:
                    # This is a ref() call
                    for source_model in model_by_name[table_name]:
                        lineage.append({
                            "source": source_model['id'],
                            "target": target_model['id'],
                            "type": "ref"
                        })
                
                elif source_type == 'dbt_source':
                    # This is a source() call
                    # In dbt, source first param is the source name (like a schema)
                    # We need to find if there's a model with this name in the given schema/source
                    for model_name, source_models in model_by_name.items():
                        for source_model in source_models:
                            # Check if this model appears to be the source referenced
                            if (source_model.get('name') == table_name and 
                                source_model.get('schema') == schema_name):
                                lineage.append({
                                    "source": source_model['id'],
                                    "target": target_model['id'],
                                    "type": "source"
                                })
                
                else:
                    # This is a direct table reference
                    # Try to find a model matching this table name
                    if table_name in model_by_name:
                        for source_model in model_by_name[table_name]:
                            # If schema is specified, make sure it matches
                            if not schema_name or source_model.get('schema') == schema_name:
                                lineage.append({
                                    "source": source_model['id'],
                                    "target": target_model['id'],
                                    "type": "direct_reference"
                                })
        
        return lineage

class SQLDependencyExtractor:
    """
    Extracts dependencies from SQL code.
    Can identify upstream tables/models and column-level dependencies.
    """
    
    def __init__(self):
        self.dependencies = set()
        self.column_dependencies = {}  # Maps target_column -> [source_columns]
    
    def parse_sql(self, sql_text: str) -> Tuple[Set[str], Dict[str, List[Tuple[str, str]]]]:
        """
        Parse SQL to extract model dependencies and column-level dependencies
        
        Returns:
            Tuple containing:
            - Set of model dependencies
            - Dict mapping target column names to list of source columns with their models
        """
        self.dependencies = set()
        self.column_dependencies = {}
        
        if not sql_text:
            return set(), {}
        
        try:
            # Parse the SQL
            statements = sqlparse.parse(sql_text)
            
            for statement in statements:
                if statement.get_type() == 'SELECT':
                    # Extract model dependencies
                    self._extract_dependencies_from_select(statement)
                    
                    # Extract column dependencies
                    self._extract_column_dependencies(statement)
            
            # Convert column dependencies to include model info
            processed_column_deps = {}
            for target_col, source_cols in self.column_dependencies.items():
                processed_source_cols = []
                for source_col in source_cols:
                    # Try to determine which model this column is from
                    possible_models = self._find_model_for_column(source_col, sql_text)
                    for model in possible_models:
                        processed_source_cols.append((model, source_col))
                
                if processed_source_cols:
                    processed_column_deps[target_col] = processed_source_cols
                    
            return self.dependencies, processed_column_deps
            
        except Exception as e:
            logger.error(f"Error parsing SQL: {str(e)}")
            return set(), {}
    
    def _extract_dependencies_from_select(self, statement):
        """Extract table/model dependencies from a SELECT statement"""
        # Find all FROM and JOIN clauses
        from_seen = False
        tables = []
        
        for token in statement.tokens:
            if token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
                continue
                
            if from_seen and token.ttype is not Keyword:
                if isinstance(token, IdentifierList):
                    # Multiple tables in the FROM clause
                    for identifier in token.get_identifiers():
                        if hasattr(identifier, 'value'):
                            tables.append(identifier.value)
                elif isinstance(token, Identifier):
                    # Single table in the FROM clause
                    tables.append(token.value)
                from_seen = False
            
            # Check for JOINs
            if token.ttype is Keyword and 'JOIN' in token.value.upper():
                # Next token should be the table name
                next_token = statement.token_next(statement.token_index(token))[1]
                if isinstance(next_token, Identifier):
                    tables.append(next_token.value)
                    
        # Process any ref() or source() calls
        for table in tables:
            # Check for ref() calls
            ref_matches = re.findall(r'ref\([\'"]([^\'"]+)[\'"]\)', table)
            for match in ref_matches:
                self.dependencies.add(match)
                
            # Check for more complex ref() calls with project
            ref_project_matches = re.findall(r'ref\([\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\)', table)
            for match in ref_project_matches:
                model_name, project_name = match
                self.dependencies.add(f"{model_name} ({project_name})")
                
            # Check for source() calls
            source_matches = re.findall(r'source\([\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\)', table)
            for match in source_matches:
                source_name, table_name = match
                self.dependencies.add(f"{table_name} (source:{source_name})")
    
    def _extract_column_dependencies(self, statement):
        """Extract column-level dependencies from SELECT statement"""
        # First, identify column aliases in the SELECT clause
        column_aliases = self._extract_column_aliases(statement)
        
        # Then, trace each column to find its dependencies
        for alias, expression in column_aliases.items():
            source_columns = self._extract_source_columns(expression)
            if source_columns:
                if alias not in self.column_dependencies:
                    self.column_dependencies[alias] = set()
                self.column_dependencies[alias].update(source_columns)
    
    def _extract_column_aliases(self, statement) -> Dict[str, str]:
        """Extract column aliases from SELECT clause"""
        aliases = {}
        select_seen = False
        in_select_clause = False
        
        for token in statement.tokens:
            # Find the SELECT keyword
            if token.ttype is DML and token.value.upper() == 'SELECT':
                select_seen = True
                continue
                
            # Process identifiers in SELECT clause
            if select_seen and not in_select_clause:
                if token.ttype is not Keyword:
                    in_select_clause = True
                    
                    # Check if it's a column list
                    if isinstance(token, IdentifierList):
                        # Process each column
                        for item in token.get_identifiers():
                            self._process_column_item(item, aliases)
                    else:
                        # Single column
                        self._process_column_item(token, aliases)
                        
            # End of SELECT clause
            if in_select_clause and token.ttype is Keyword and token.value.upper() in ['FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                break
                
        return aliases
    
    def _process_column_item(self, item, aliases):
        """Process a single column item to extract alias"""
        # Check for "expression AS alias" pattern
        alias = None
        expression = None
        
        # Find the AS keyword to identify alias
        as_idx = None
        for i, token in enumerate(item.tokens):
            if token.ttype is Keyword and token.value.upper() == 'AS':
                as_idx = i
                break
                
        if as_idx is not None:
            # Alias is after the AS keyword
            if as_idx + 1 < len(item.tokens):
                alias_token = item.tokens[as_idx + 1]
                if isinstance(alias_token, Identifier) or alias_token.ttype is Name:
                    alias = alias_token.value
                    
            # Expression is before the AS keyword
            expression_tokens = item.tokens[:as_idx]
            if expression_tokens:
                expression = ''.join(token.value for token in expression_tokens)
        else:
            # No AS keyword, but might still have alias or just be a column
            if isinstance(item, Identifier):
                # Check if it has a dot, indicating table.column
                if '.' in item.value:
                    expression = item.value
                    alias = item.value.split('.')[-1]
                else:
                    alias = item.value
                    expression = alias
                    
        if alias and expression:
            aliases[alias] = expression
            
        return aliases
    
    def _extract_source_columns(self, expression) -> Set[str]:
        """Extract source columns from an expression"""
        source_columns = set()
        
        # Simple case: direct column reference
        # Match table.column pattern
        table_column_matches = re.findall(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)', expression)
        for match in table_column_matches:
            table, column = match
            source_columns.add(f"{table}.{column}")
            
        # Simpler case: just column name
        # Only add simple column names if there are no table.column matches
        if not table_column_matches:
            column_matches = re.findall(r'\b([a-zA-Z][a-zA-Z0-9_]*)\b', expression)
            source_columns.update(column_matches)
            
        return source_columns
    
    def _find_model_for_column(self, column, sql_text) -> List[str]:
        """Try to determine which model a column belongs to"""
        models = []
        
        # If the column is in table.column format
        if '.' in column:
            table_alias = column.split('.')[0]
            
            # Find alias definitions in FROM or JOIN clauses
            alias_matches = re.findall(r'(?:FROM|JOIN)\s+([^\s]+)\s+(?:AS\s+)?(' + re.escape(table_alias) + r')\b', sql_text, re.IGNORECASE)
            for match in alias_matches:
                table, alias = match
                # Extract model name from ref() or source() if present
                ref_match = re.search(r'ref\([\'"]([^\'"]+)[\'"]\)', table)
                if ref_match:
                    models.append(ref_match.group(1))
                    continue
                    
                ref_project_match = re.search(r'ref\([\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\)', table)
                if ref_project_match:
                    model_name, project_name = ref_project_match.groups()
                    models.append(f"{model_name} ({project_name})")
                    continue
                    
                source_match = re.search(r'source\([\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\)', table)
                if source_match:
                    source_name, table_name = source_match.groups()
                    models.append(f"{table_name} (source:{source_name})")
                    continue
                    
                # If no ref or source, use the table name itself
                models.append(table)
        
        return models 