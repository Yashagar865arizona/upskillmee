"""
Simple test script to test the learning plan extraction and cleaning functions.
"""

import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_learning_plan(text, validate_only=False):
    """
    Extract, clean and validate a learning plan JSON from text.
    
    Args:
        text: The text containing JSON data
        validate_only: If True, validates the JSON without modifying it
        
    Returns:
        On success: JSON string (if validate_only=True) or dictionary (if validate_only=False)
        On failure: Error string (if validate_only=True) or None (if validate_only=False)
    """
    try:
        # Log the input text
        if not text or not isinstance(text, str):
            logger.info("No text to extract learning plan from")
            return None if not validate_only else "Error: No input text provided"
            
        logger.info(f"Processing text (length: {len(text)})")
        
        # Extract JSON if it's wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if json_match:
            json_str = json_match.group(1)
            logger.info(f"Extracted JSON from markdown code block (length: {len(json_str)})")
        elif text.strip().startswith('{') and text.strip().endswith('}'):
            json_str = text.strip()
            logger.info("Text appears to be JSON")
        else:
            logger.info("No JSON found in text")
            return None if not validate_only else "Error: No JSON found in the text"
        
        # Parse the JSON
        logger.info(f"Parsing JSON: {json_str[:100]}...")
        parsed = json.loads(json_str)
        
        # Validate that it's a dictionary
        if not isinstance(parsed, dict):
            logger.info("Parsed JSON is not a dictionary")
            return None if not validate_only else "Error: Parsed JSON is not a dictionary"
            
        # Check for projects field
        if "projects" not in parsed:
            logger.info("No 'projects' field in parsed JSON")
            
            # Try to transform other formats
            if "timeline" in parsed:
                logger.info("Found 'timeline' field, attempting to transform")
                
                # Convert timeline format to projects format
                projects = []
                
                # Extract from weekly timeline if available
                if 'weekly' in parsed['timeline'] and isinstance(parsed['timeline']['weekly'], list):
                    for i, week in enumerate(parsed['timeline']['weekly']):
                        if isinstance(week, dict) and 'milestones' in week:
                            projects.append({
                                'title': f"Week {i+1}: {parsed.get('title', 'Learning Plan')}",
                                'description': parsed.get('overview', ''),
                                'tasks': week.get('milestones', []),
                                'skills': [],
                                'weeks': f"Week {i+1}"
                            })
                
                # If no projects were created, create a default one
                if not projects:
                    projects.append({
                        'title': parsed.get('title', 'Learning Plan'),
                        'description': parsed.get('overview', ''),
                        'tasks': [],
                        'skills': [],
                        'weeks': "Week 1"
                    })
                
                parsed = {'projects': projects}
                logger.info(f"Transformed timeline format to projects format")
            else:
                return None if not validate_only else "Error: Missing 'projects' field in JSON response"
        
        # Validate each project has required fields
        for i, project in enumerate(parsed['projects']):
            if not isinstance(project, dict):
                msg = f"Project {i} is not a dictionary"
                logger.info(msg)
                return None if not validate_only else f"Error: {msg}"
            
            if 'title' not in project:
                project['title'] = f"Week {i+1}: Learning Plan"
            
            if 'description' not in project:
                project['description'] = ""
            
            if 'tasks' not in project or not isinstance(project['tasks'], list):
                project['tasks'] = []
            
            if 'skills' not in project or not isinstance(project['skills'], list):
                project['skills'] = []
            
            if 'weeks' not in project:
                project['weeks'] = f"Week {i+1}"
        
        logger.info(f"Successfully processed learning plan with {len(parsed['projects'])} projects")
        
        # Return the appropriate result based on the validate_only flag
        if validate_only:
            return json.dumps(parsed, ensure_ascii=False)
        else:
            return parsed
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return None if not validate_only else f"Error: JSON decode error - {str(e)}"
    except Exception as e:
        logger.error(f"Error processing learning plan: {str(e)}")
        return None if not validate_only else f"Error: {str(e)}"

# Legacy functions that now use the unified implementation
def clean_json_string(json_str):
    """
    Clean and validate JSON string from AI response
    
    This is a legacy function that uses the unified process_learning_plan function.
    """
    return process_learning_plan(json_str, validate_only=True)

def extract_learning_plan(text):
    """
    Extract a learning plan from text if it exists
    
    This is a legacy function that uses the unified process_learning_plan function.
    """
    return process_learning_plan(text, validate_only=False)

# Test data as constants to avoid duplication
TEST_DATA = {
    "valid_json": """
    {
      "projects": [
        {
          "title": "Week 1: HTML Basics",
          "description": "Introduction to HTML",
          "tasks": ["Learn HTML tags", "Create a simple webpage"],
          "skills": ["HTML", "Web Development"],
          "weeks": "Week 1"
        }
      ]
    }
    """,
    
    "timeline_json": """
    {
      "title": "Web Development Learning Plan",
      "overview": "A comprehensive plan to learn web development",
      "timeline": {
        "weekly": [
          {
            "milestones": ["Learn HTML", "Create a simple webpage"],
            "projects": ["Personal Website"]
          }
        ]
      }
    }
    """,
    
    "invalid_json": "This is not JSON",
    
    "markdown_json": """
    Here's a learning plan:
    
    ```json
    {
      "projects": [
        {
          "title": "Week 1: HTML Basics",
          "description": "Introduction to HTML",
          "tasks": ["Learn HTML tags", "Create a simple webpage"],
          "skills": ["HTML", "Web Development"],
          "weeks": "Week 1"
        }
      ]
    }
    ```
    """
}

def run_tests(test_func, func_name):
    """Run a series of tests on the given function with standard test data"""
    logger.info(f"Running tests for {func_name}...")
    
    # Test 1: Valid JSON with projects
    result1 = test_func(TEST_DATA["valid_json"])
    logger.info(f"Test 1 Result ({func_name}): {result1}")
    
    # Test 2: JSON with timeline format
    result2 = test_func(TEST_DATA["timeline_json"])
    logger.info(f"Test 2 Result ({func_name}): {result2}")
    
    # Test 3: Invalid JSON
    result3 = test_func(TEST_DATA["invalid_json"])
    logger.info(f"Test 3 Result ({func_name}): {result3}")
    
    # Test 4: JSON in markdown code block
    result4 = test_func(TEST_DATA["markdown_json"])
    logger.info(f"Test 4 Result ({func_name}): {result4}")

# Legacy test functions that now use the unified implementation
def test_process_learning_plan():
    """Test the process_learning_plan function with various inputs"""
    # Test with validate_only=True
    run_tests(lambda x: process_learning_plan(x, validate_only=True), "process_learning_plan (validate_only=True)")
    
    # Test with validate_only=False
    run_tests(lambda x: process_learning_plan(x, validate_only=False), "process_learning_plan (validate_only=False)")

# Keep these for backward compatibility
def test_clean_json_string():
    """Test the clean_json_string function with various inputs"""
    run_tests(clean_json_string, "clean_json_string")

def test_extract_learning_plan():
    """Test the extract_learning_plan function with various inputs"""
    run_tests(extract_learning_plan, "extract_learning_plan")

# Run tests if script is executed directly
if __name__ == "__main__":
    test_process_learning_plan()
    test_clean_json_string()
    test_extract_learning_plan() 