# src/aigraphcodescan/app.py
import json
import os
import uuid
import logging
import argparse
from neo4j import GraphDatabase
from fast_graphrag import GraphRAG

def get_logger():
    parser = argparse.ArgumentParser(description="Run graph extraction.")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args, unknown = parser.parse_known_args()

    # Default level is ERROR, no normal logs or debug logs unless --debug is used
    logging_level = logging.DEBUG if args.debug else logging.ERROR
    logging.basicConfig(level=logging_level)
    logger = logging.getLogger(__name__)

    # Return both args and logger so we can use args if needed
    return logger, args

logger, args = get_logger()

# Environment-driven configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DIRECTORY_PATH = os.getenv("DIRECTORY_PATH", "../badcode/")
WORKING_DIR = os.getenv("WORKING_DIR", "./test")

DOMAIN = os.getenv("DOMAIN",
    "As a code review expert, your role will be to carefully examine the code "
    "for potential security flaws. Focus on how the input can be passed to a function or method, "
    "the input location, sanitization, tainting, control and dataflow"
)

EXAMPLE_QUERIES = [
    "What are the functions used?",
    "What are the objects and methods used?",
    "Which functions take input from the user?",
    "What are the sinks?",
    "What is the control flow?",
    "What is the data flow?",
    "Which vulnerable functions are used?",
    "Which inputs are not tainted after reaching the sink?",
    "What is the filename?",
    "What is the linenumber?",
]
ENTITY_TYPES = ["Type", "Category", "Filename", "Linenumber", "Input", "Function", "Object", "Method", "Tainted", "Untainted", "Sink"]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

grag = GraphRAG(
    working_dir=WORKING_DIR,
    domain=DOMAIN,
    example_queries="\n".join(EXAMPLE_QUERIES),
    entity_types=ENTITY_TYPES,
)

def test_connection():
    """Tests the Neo4j connection by running a simple query."""
    try:
        with driver.session() as session:
            result = session.run("RETURN 'Connection Successful' AS message")
            for record in result:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(record["message"])
    except Exception as e:
        logger.error(f"Connection test failed: {e}")

def clear_database():
    """Deletes all nodes and relationships in the database."""
    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Database cleared.")
    except Exception as e:
        logger.error(f"Error clearing the database: {e}")

def initialize_database():
    """Initializes the Neo4j database with constraints."""
    try:
        with driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Database initialized with constraints.")
    except Exception as e:
        logger.error(f"Error initializing the database: {e}")

def query_grag_json(grag, query):
    """
    Queries grag and ensures the response is valid JSON.
    Retries indefinitely until it gets valid JSON.
    """
    while True:
        response = grag.query(query).response
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Response: {response}")
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError as e:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Invalid JSON, retrying... Error: {e}")
            continue

def push_to_neo4j(json_data):
    """
    Pushes JSON data to Neo4j.
    Expects data in one of these formats:
    - A single object { "filename": "", "vulnerability": "", "linenumber": "" }
    - A list of such objects
    """
    if not json_data:
        logger.error("No data to push to Neo4j.")
        return

    # If single object, convert to list for consistency
    if isinstance(json_data, dict):
        json_data = [json_data]

    try:
        with driver.session() as session:
            for item in json_data:
                entity_id = str(uuid.uuid4())
                filename = item.get("filename", "Unknown")
                vulnerability = item.get("vulnerability", "Unknown")
                linenumber = item.get("linenumber", "Unknown")

                query = """
                MERGE (n:Entity {
                    id: $id,
                    Filename: $filename,
                    vulnerability: $vulnerability,
                    Linenumber: $linenumber
                })
                """
                session.run(query, id=entity_id, filename=filename, vulnerability=vulnerability, linenumber=linenumber)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Graph data successfully pushed to Neo4j.")
    except Exception as e:
        logger.error(f"Error pushing data to Neo4j: {e}")

def main():
    test_connection()
    clear_database()
    initialize_database()

    # Insert files into grag
    for dirpath, dirnames, filenames in os.walk(DIRECTORY_PATH):
        for fname in filenames:
            file_path = os.path.join(dirpath, fname)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        grag.insert(content)
                except UnicodeDecodeError:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Skipping {file_path} due to encoding issues.")
                    continue

    # Query grag for JSON data
    query = (
        "which entities that involve functions, methods, get inputs and are vulnerable to top25 sans attacks.\n"
        "List along with the corresponding file names and line numbers.\n"
        "Please respond with JSON only. No additional text. The format must be:\n"
        "```json\n"
        "{\n"
        "  \"filename\": \"string\",\n"
        "  \"vulnerability\": \"string\",\n"
        "  \"linenumber\": \"string\"\n"
        "}\n"
        "```"
    )

    data = query_grag_json(grag, query)
    push_to_neo4j(data)

