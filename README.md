# AIGraphCodeScan

**AIGraphCodeScan** is a tool designed for performing security reviews of codebases using graph analysis. The package utilizes Neo4j and Fast GraphRAG to query and visualize relationships within the code, helping identify potential security risks and vulnerabilities by analyzing the structure and flow of the code.

## Features

- **Graph-based Code Analysis**: Leverages graph theory to analyze code relationships and interactions.
- **Neo4j Integration**: Stores and queries code structure and data flow in a Neo4j graph database.
- **Security Review**: Helps identify potential security vulnerabilities based on the code's structure and relationships.

## Installation

### Prerequisites

Ensure you have Python 3.6 or higher installed. You will also need a Neo4j instance running to store and query code-related data.

### Installation Steps

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/tcosolutions/aigraphcodescan.git
cd aigraphcodescan
pip install -e .
```

### Requirements

- Python 3.6+
- `neo4j >= 4.0.0`
- `fast_graphrag >= 0.1.0`
- `argparse`, `logging`, `json`

## Usage

Once installed, you can use the `aigraphcodescan` command to run the security review.

```bash
aigraphcodescan --debug
```

Export env variable for OpenAI (api key) and Neo4j settings (see code)

```
export NEO4J_URI = "bolt://localhost:7687")
export NEO4J_USER = "neo4j"
export NEO4J_PASSWORD = "password"
```

The command will start the graph-based security review process. The `--debug` option enables more detailed logging output.

## Example Workflow

1. **Run the security scan**: Use the `aigraphcodescan` command to analyze your codebase.
2. **Review findings**: Based on the graph analysis, the tool will provide insights into potential security vulnerabilities, such as unexpected interactions between modules, exposed endpoints, or insecure data flows.
3. **Improve your code**: Use the output to guide security improvements in your codebase.

## Contributing

We welcome contributions to **AIGraphCodeScan**. If you find a bug or have a suggestion, please open an issue or submit a pull request.

## License

This project is licensed under the AGPL 3.0 License - see the [LICENSE](LICENSE) file for details.
