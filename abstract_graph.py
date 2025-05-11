from neo4j import GraphDatabase
import os
from collections import defaultdict

# Neo4j connection from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "testpassword")

# Adjust depth here (e.g., 1 = zeeguu.core, 2 = zeeguu.core.model)
ABSTRACTION_DEPTH = 2

def abstract_name(full_name, depth):
    return ".".join(full_name.split(".")[:depth])

def abstract_dependencies(driver, depth):
    with driver.session() as session:
        # Get all fine-grained dependencies
        result = session.run("""
            MATCH (a:Module)-[:DEPENDS_ON]->(b:Module)
            RETURN a.name AS src, b.name AS dst
        """)
        pairs = result.data()

        # Group by abstraction level
        grouped_deps = set()
        abstract_size = defaultdict(set)  # maps abstract name → set of modules inside

        for row in pairs:
            src = abstract_name(row["src"], depth)
            dst = abstract_name(row["dst"], depth)
            if src != dst:
                grouped_deps.add((src, dst))
            abstract_size[src].add(row["src"])
            abstract_size[dst].add(row["dst"])

        # Clear abstract graph
        session.run("MATCH (n:AbstractModule) DETACH DELETE n")

        # Write abstraction
        for src, dst in grouped_deps:
            session.run("""
                MERGE (a:AbstractModule {name: $src})
                MERGE (b:AbstractModule {name: $dst})
                MERGE (a)-[:DEPENDS_ON]->(b)
            """, src=src, dst=dst)

        # Add polymetric info
        for mod, modules in abstract_size.items():
            session.run("""
                MATCH (m:AbstractModule {name: $mod})
                SET m.size = $size
            """, mod=mod, size=len(modules))

        print(f"✅ Abstracted {len(abstract_size)} groups with depth={depth}")

if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    abstract_dependencies(driver, ABSTRACTION_DEPTH)
    driver.close()
