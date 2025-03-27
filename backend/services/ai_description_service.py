import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

class AIDescriptionService:
    """Service for generating AI descriptions for models and columns using Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            print("Set it using: export GEMINI_API_KEY='your-api-key'")
        else:
            print(f"Using Gemini API key: {self.api_key[:5]}...{self.api_key[-4:]}")
        
        # Updated to use gemini-2.0-flash-lite model as specified
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-lite:generateContent"
    
    def _make_api_request(self, prompt: str) -> Optional[str]:
        """Make a request to Gemini API to generate content"""
        if not self.api_key:
            print("Error: Gemini API key not set")
            return None
        
        try:
            # Prepare the request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 200,
                }
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Error from Gemini API: {response.status_code} - {response.text}")
                return None
            
            # Parse the response
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        # Return the full text without any truncation
                        description = parts[0]["text"].strip()
                        # Check for truncation indicators and log a warning if found
                        if description.endswith('...') or description.endswith('…'):
                            print(f"Warning: AI description appears to be truncated: {description}")
                        return description
            
            print("Unexpected response format from Gemini API")
            return None
            
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return None
    
    def generate_column_description(self, column_name: str, model_name: str, sql_context: str = None, 
                                   column_type: str = None, table_context: str = None) -> Optional[str]:
        """Generate a description for a column based on its name and context"""
        # Build a detailed prompt with all available context
        prompt = f"""
        As a database expert, provide a concise, accurate, and helpful description (2-3 sentences) for a column in a database table.

        Column Name: {column_name}
        Model/Table Name: {model_name}
        Column Data Type: {column_type or 'Unknown'}
        """
        
        # Add table context if available
        if table_context:
            prompt += f"\nTable Purpose: {table_context}"
        
        # Add SQL context if available (with reasonable size limit)
        if sql_context:
            # Extract relevant SQL for this column to provide better context
            # Look for the column name in the SQL
            relevant_sql = ""
            if column_name in sql_context:
                # Try to find SQL snippets related to this column
                lines = sql_context.split("\n")
                for i, line in enumerate(lines):
                    if column_name in line:
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        relevant_sql += "\n".join(lines[start:end]) + "\n\n"
            
            # If no relevant SQL found or it's too short, use a portion of the full SQL
            if len(relevant_sql) < 100 and sql_context:
                relevant_sql = sql_context[:1200] + "..." if len(sql_context) > 1200 else sql_context
            
            prompt += f"\n\nSQL Context: {relevant_sql}"
        
        prompt += """
        
        Base your description on the naming conventions, data type, and context provided. Be specific about:
        1. What data this column contains
        2. The purpose of this data in the model
        3. Any business meaning or calculation logic if apparent
        
        Keep the description informative and useful for data analysts.
        """
        
        # Create specific payload for column descriptions
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 300,  # Adequate tokens for column descriptions
            }
        }
        
        try:
            # Make the API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Error from Gemini API: {response.status_code} - {response.text}")
                return None
            
            # Parse the response
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        description = parts[0]["text"].strip()
                        if description.endswith('...') or description.endswith('…'):
                            print(f"Warning: Column description appears to be truncated: {description}")
                        return description
            
            print("Unexpected response format from Gemini API for column description")
            return None
            
        except Exception as e:
            print(f"Error calling Gemini API for column description: {str(e)}")
            return None
    
    def generate_model_description(self, model_name: str, project_name: str, 
                                 sql_code: str = None, column_info: List[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a description for a model based on its name, SQL code, and column information"""
        # Start building the prompt with the model name and project
        prompt = f"""
        As a dbt expert, provide a concise and accurate description (3-5 sentences) for a dbt model.

        Model Name: {model_name}
        Project: {project_name}
        """
        
        # Add column information if available
        if column_info and len(column_info) > 0:
            prompt += f"\n\nColumns ({len(column_info)}):\n"
            for column in column_info[:15]:  # Include more columns for better context
                prompt += f"- {column.get('name', 'Unknown')} ({column.get('type', 'Unknown')})\n"
            
            if len(column_info) > 15:
                prompt += f"- ... and {len(column_info) - 15} more columns\n"
        
        # Add SQL code context if available (increased size for better context)
        if sql_code:
            sql_excerpt = sql_code[:1500] + "..." if len(sql_code) > 1500 else sql_code
            prompt += f"\n\nSQL Code:\n{sql_excerpt}"
        
        prompt += """
        
        Based on the model name, columns, and SQL code:
        1. Describe the purpose of this model
        2. Explain what data it processes or produces
        3. Mention its role in the data pipeline
        4. Note any important transformations or business logic
        
        Keep the description clear, technical, and useful for data analysts. Provide a complete description without any truncation.
        """
        
        # Make the API request with increased token limit for model descriptions
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 400,  # Increased token limit for model descriptions
            }
        }
        
        try:
            # Make the API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Error from Gemini API: {response.status_code} - {response.text}")
                return None
            
            # Parse the response
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        # Return the full text without any truncation
                        description = parts[0]["text"].strip()
                        if description.endswith('...') or description.endswith('…'):
                            print(f"Warning: Model description appears to be truncated: {description}")
                        return description
            
            print("Unexpected response format from Gemini API for model description")
            return None
            
        except Exception as e:
            print(f"Error calling Gemini API for model description: {str(e)}")
            return None
    
    def enrich_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich metadata with AI-generated descriptions"""
        # Check if API key is available
        if not self.api_key:
            print("Warning: No Gemini API key provided for AI descriptions. Returning original metadata.")
            return metadata
            
        print("Enriching metadata with AI-generated descriptions...")
        
        # Enrich model descriptions
        if "models" in metadata and isinstance(metadata["models"], list):
            for model in metadata["models"]:
                if not model.get("description") or model.get("description") == "":
                    # Get project name
                    project_name = model.get("project", "Unknown")
                    
                    # Prepare SQL context if available
                    sql_code = model.get("sql")
                    
                    # Prepare column information if available
                    column_info = model.get("columns", [])
                    
                    # Generate model description
                    description = self.generate_model_description(
                        model_name=model.get("name", "Unknown"),
                        project_name=project_name,
                        sql_code=sql_code,
                        column_info=column_info
                    )
                    
                    if description:
                        model["ai_description"] = description
                        print(f"Added AI description for model: {model.get('name')}")
                    
                # Enrich column descriptions
                if "columns" in model and isinstance(model["columns"], list):
                    for column in model["columns"]:
                        if not column.get("description") or column.get("description") == "":
                            # Generate column description
                            description = self.generate_column_description(
                                column_name=column.get("name", "Unknown"),
                                model_name=model.get("name", "Unknown"),
                                sql_context=model.get("sql"),
                                column_type=column.get("type"),
                                table_context=model.get("description") or model.get("ai_description")
                            )
                            
                            if description:
                                column["ai_description"] = description
                                print(f"Added AI description for column: {column.get('name')} in model: {model.get('name')}")
                            
            return metadata
        
    async def suggest_columns(self, model_name: str, existing_columns: List[str]) -> List[Dict]:
        """Generate column suggestions for a model"""
        prompt = f"""
        I'm designing a dbt model named '{model_name}' that already has these columns:
        {', '.join(existing_columns)}
        
        Please suggest 3-5 additional columns that would logically complement this model.
        
        For each suggested column, provide:
        1. A clear name in snake_case format
        2. The appropriate data type (string, integer, float, timestamp, boolean)
        3. A brief but helpful description of what the column represents
        
        Format your response as a JSON array of objects like this:
        [
          {{"name": "column_name", "type": "data_type", "description": "Description of the column"}},
          ...
        ]
        
        Only include the JSON array in your response, nothing else.
        """
        
        try:
            result = self._make_api_request(prompt)
            if not result:
                return []
                
            # Find the JSON part in the response
            json_start = result.find('[')
            json_end = result.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                suggestions = json.loads(json_str)
                return suggestions
            else:
                print("Could not find JSON array in response")
                return []
                
        except Exception as e:
            print(f"Error suggesting columns: {str(e)}")
            return []
            
    async def suggest_column_description(self, model_name: str, column_name: str, column_type: str) -> str:
        """Generate a description for a column"""
        prompt = f"""
        For a dbt model named '{model_name}', write a clear, concise description (1-2 sentences) for this column:
        
        Column Name: {column_name}
        Data Type: {column_type}
        
        The description should explain:
        1. What this column represents
        2. How it's used or what business value it provides
        
        Keep it brief but informative for data analysts.
        """
        
        try:
            result = self._make_api_request(prompt)
            return result or ""
        except Exception as e:
            print(f"Error suggesting column description: {str(e)}")
            return "" 