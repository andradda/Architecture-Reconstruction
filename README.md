# Architecture-Reconstruction

This repository includes a set of scripts used to recosntruct the architecture of [Zeeguu-API](https://github.com/zeeguu/api), including module abstraction, size metrics, and network-based analysis using PageRank.

The project runs inside a Docker container, which executes all analysis scripts. Generated plots are saved to a mounted local folder.

To build the image and start the analysis run:

```bash
docker-compose up --build
```

To explore the module dependency graph interactively, open Neo4j in the browser at:
[http://localhost:7474](http://localhost:7474)

**Login credentials:**

- **Username:** `neo4j`
- **Password:** `strong_password`

Once logged in, you can run Cypher queries to inspect the graph:

```cypher
MATCH (a:Module)-[r:DEPENDS_ON]->(b:Module)
RETURN a, r, b
```

To view abstracted modules (after applying depth-based abstraction) use `AbstractModule`.
