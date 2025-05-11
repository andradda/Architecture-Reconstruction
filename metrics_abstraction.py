import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def extract_dependencies_and_loc(code_base_path):
    dependencies = set()
    loc_map = {}

    for root, _, files in os.walk(code_base_path):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), code_base_path)
                src_module = rel_path.replace("\\", ".").replace("/", ".")[:-3]
                if src_module.startswith("zeeguu."):
                    src_module = src_module[len("zeeguu."):]

                full_path = os.path.join(root, file)

                try:
                    with open(full_path, "r", encoding="utf8", errors="ignore") as f:
                        lines = f.readlines()
                        loc = sum(1 for line in lines if line.strip())
                        loc_map[src_module] = loc

                        for line in lines:
                            line = line.strip()
                            if line.startswith("import ") or line.startswith("from "):
                                tokens = line.replace("import", "").replace("from", "").strip().split()
                                if tokens:
                                    dst_module = tokens[0]
                                    if dst_module.startswith("zeeguu."):
                                        dst_module = dst_module[len("zeeguu."):]
                                        dependencies.add((src_module, dst_module))
                except Exception:
                    continue

    return dependencies, loc_map


def plot_loc_bubble_char(code_base_path, top_n=10):
    _, locs = extract_dependencies_and_loc(code_base_path)
    top_modules = sorted(locs.items(), key=lambda x: x[1], reverse=True)[:top_n]

    modules, loc_values = zip(*top_modules)
    sizes = np.array(loc_values)

    # scale nodes based on LOC size
    scaled_sizes = (sizes - min(sizes)) / (max(sizes) - min(sizes) + 1e-5)
    areas = 2000 + (scaled_sizes * 8000)

    colors = plt.colormaps["tab10"](np.linspace(0, 1, len(modules)))

    # align nodes into a circular layout
    angle = np.linspace(0, 2 * np.pi, len(modules), endpoint=False)
    radius = 0.2
    x = np.cos(angle) * radius
    y = np.sin(angle) * radius

    plt.figure(figsize=(8, 6))
    for i in range(len(modules)):
        plt.scatter(x[i], y[i], s=areas[i], color=colors[i])
        label = f"{modules[i].split('.')[-1]}\n{loc_values[i]} LOC"
        plt.text(x[i], y[i], label, fontsize=10, ha='center', va='center', color='black', fontfamily='serif')

    plt.axis('off')
    plt.tight_layout()

    padding = 0.05 # from margin
    plt.xlim(min(x) - padding, max(x) + padding)
    plt.ylim(min(y) - padding, max(y) + padding)

    output_dir = "/app/plots"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "top_10_loc_bubbles.png")
    plt.savefig(output_path)


def run_pagerank_analysis(dependencies, top_n=20):
    G = nx.DiGraph()
    G.add_edges_from(dependencies)

    pagerank = nx.pagerank(G)

    # take top n nodes by PageRank score (aka the most important)
    top_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:top_n]
    nodes, scores = zip(*top_nodes)

    # rescale
    scaled_scores = [round(score * 100, 2) for score in scores]
    sizes = [2000 + score * 1000 for score in scaled_scores] 
    colors = cm.viridis(np.linspace(0, 1, len(nodes)))

    # subgraph of the nodes
    subG = G.subgraph(nodes).copy()

    # position layout (somewhat random - needs to be updated for a more clear view :>)
    pos = nx.spring_layout(subG, k=1.2, seed=51, iterations=200)

    plt.figure(figsize=(12, 10))

    nx.draw_networkx(
    subG,
    pos,
    node_color=[colors[nodes.index(node)] for node in subG.nodes],
    node_size=[sizes[nodes.index(node)] for node in subG.nodes],
    arrows=True,
    with_labels=False,
    edge_color="gray",
    connectionstyle="arc3,rad=0.1",
    arrowsize=20,
    width=2,
    )

    for i, node in enumerate(subG.nodes):
        label = f"{node.split('.')[-1]}\n{scaled_scores[nodes.index(node)]}"
        plt.text(
            pos[node][0],
            pos[node][1],
            label,
            fontsize=9,
            ha="center",
            va="center",
            color="black",
            fontweight="bold"
        )

    plt.axis("off")
    plt.tight_layout()

    output_dir = "/app/plots"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pagerank_network_graph.png")
    plt.savefig(output_path)

# Entry point
if __name__ == "__main__":
    code_base_path = "zeeguu-api/zeeguu"
    plot_loc_bubble_char(code_base_path, top_n=10)
    deps, _ = extract_dependencies_and_loc("zeeguu-api/zeeguu")
    run_pagerank_analysis(deps)
