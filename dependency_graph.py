from neo4j import GraphDatabase
import os

# load the environment variables (from docker-compose.yml)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "testpassword")

def extract_module_dependencies(code_base_path):
    dependencies = set()
    for root, _, files in os.walk(code_base_path):
        for file in files:
            if file.endswith(".py"):
                # receive relative path to all .py files and normalize to module name
                rel_path = os.path.relpath(os.path.join(root, file), code_base_path)
                src_module = rel_path.replace("\\", ".").replace("/", ".")[:-3]
                if src_module.startswith("zeeguu."):
                    src_module = src_module[len("zeeguu."):]

                with open(os.path.join(root, file), "r", encoding="utf8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("import ") or line.startswith("from "):
                            tokens = line.replace("import", "").replace("from", "").strip().split()
                            if tokens:
                                dst_module = tokens[0]
                                if not dst_module.startswith("zeeguu."):
                                    continue  # skip any other external imports
                                dst_module = dst_module[len("zeeguu."):]
                                dependencies.add((src_module, dst_module))
    return dependencies

def upload_to_neo4j(dependencies):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        session.execute_write(clear_db)
        for src, dst in dependencies:
            session.execute_write(create_dependency, src, dst)
    driver.close()

def clear_db(tx):
    tx.run("MATCH (n) DETACH DELETE n")

# uses Cypher for neo4j
def create_dependency(tx, src, dst):
    tx.run("""
        MERGE (a:Module {name: $src})
        MERGE (b:Module {name: $dst})
        MERGE (a)-[:DEPENDS_ON]->(b)
    """, src=src, dst=dst)

if __name__ == "__main__":
    deps = extract_module_dependencies("zeeguu-api/zeeguu")
    upload_to_neo4j(deps)
