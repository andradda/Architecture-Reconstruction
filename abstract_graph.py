from neo4j import GraphDatabase
import os
from collections import defaultdict

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "testpassword")

# depth = 1, 2 means - e.g. 1 = zeeguu.core, 2 = zeeguu.core.model (will not go more in-depth - it is just noise - too much detail)
ABSTRACTION_DEPTH = 2

def abstract_name(full_name, depth):
    return ".".join(full_name.split(".")[:depth])

def abstract_dependencies(driver, depth):
    with driver.session() as session:
        # get all dependencies with Cypher
        result = session.run("""
            MATCH (a:Module)-[:DEPENDS_ON]->(b:Module)
            RETURN a.name AS src, b.name AS dst
        """)
        pairs = result.data()

        # group by abstraction level
        grouped_deps = set()
        abstract_size = defaultdict(set) 

        for row in pairs:
            src = abstract_name(row["src"], depth)
            dst = abstract_name(row["dst"], depth)
            if src != dst:
                grouped_deps.add((src, dst))
            abstract_size[src].add(row["src"])
            abstract_size[dst].add(row["dst"])

        # clear abstract graph
        session.run("MATCH (n:AbstractModule) DETACH DELETE n")

        # write abstraction with Cypher
        for src, dst in grouped_deps:
            session.run("""
                MERGE (a:AbstractModule {name: $src})
                MERGE (b:AbstractModule {name: $dst})
                MERGE (a)-[r:DEPENDS_ON]->(b)
                ON CREATE SET r.weight = 1
                ON MATCH SET r.weight = r.weight + 1
            """, src=src, dst=dst)

        # add info
        for mod, modules in abstract_size.items():
            session.run("""
                MATCH (m:AbstractModule {name: $mod})
                SET m.size = $size
            """, mod=mod, size=len(modules))

if __name__ == "__main__":
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    abstract_dependencies(driver, ABSTRACTION_DEPTH)
    driver.close()
