import pandas as pd
import os
import heapq
import networkx as nx
import matplotlib.pyplot as plt

# setting
LOG_DIR = "nba_logs"
PROP_LINES = {
    "LeBron James": {"PTS": 25.5},
    "Anthony Davis": {"REB": 12.5},
    "D'Angelo Russell": {"AST": 6.0},
    "Austin Reaves": {"PTS": 14.5},
    "Rui Hachimura": {"REB": 5.5},

    "Jayson Tatum": {"PTS": 27.0},
    "Jaylen Brown": {"PTS": 23.5},
    "Jrue Holiday": {"AST": 6.5},
    "Derrick White": {"FG3M": 3.5},
    "Kristaps Porzingis": {"REB": 7.5},

    "Nikola Jokic": {"AST": 9.5},
    "Jamal Murray": {"PTS": 20.5},
    "Michael Porter Jr.": {"FG3M": 2.5},
    "Aaron Gordon": {"REB": 6.5},
    "Kentavious Caldwell-Pope": {"FG3M": 2.0},

    "Stephen Curry": {"PTS": 28.5},
    "Klay Thompson": {"FG3M": 3.5},
    "Draymond Green": {"AST": 7.0},
    "Andrew Wiggins": {"REB": 4.5},
    "Kevon Looney": {"REB": 7.5}
}

ALPHA = 0.6
BETA = 0.4
RECENT_GAMES = 10

# load in game logs
def load_game_logs():
    player_logs = {}
    for file in os.listdir(LOG_DIR):
        if file.endswith(".csv"):
            name = file.replace("_", " ").replace(".csv", "")
            df = pd.read_csv(os.path.join(LOG_DIR, file))
            player_logs[name] = df.head(RECENT_GAMES)
    return player_logs

# hit rate calc.
def calc_hit_rate(logs, stat, line):
    if stat not in logs.columns:
        return 0.0
    return (logs[stat] > line).mean()

# conditional hit rates
def conditional_correlation(logs1, logs2, stat1, stat2, line1, line2):
    if stat1 not in logs1.columns or stat2 not in logs2.columns:
        return 0.0
    h1 = (logs1[stat1] > line1).astype(int)
    h2 = (logs2[stat2] > line2).astype(int)
    if h1.sum() == 0:
        return 0.0
    return (h1 & h2).sum() / h1.sum()

# graph
# directed graph where nodes are player props, and edge weights are influence between player props
# based on conditional correlation and hit rates.
def build_graph(player_logs):
    graph = {}
    props = {}

    players = list(PROP_LINES.keys())
    for p1 in players:
        props[p1] = {}
        for stat, line in PROP_LINES[p1].items():
            hit_rate = calc_hit_rate(player_logs[p1], stat, line)
            props[p1][stat] = hit_rate

    for p1 in players:
        graph[p1] = {}
        stat1, line1 = list(PROP_LINES[p1].items())[0]
        for p2 in players:
            if p1 == p2:
                continue
            stat2, line2 = list(PROP_LINES[p2].items())[0]
            corr = conditional_correlation(player_logs[p1], player_logs[p2], stat1, stat2, line1, line2)
            score = ALPHA * corr + BETA * props[p2][stat2]
            graph[p1][p2] = score
    return graph, props

# Main Algorithm
# Customalgorithm to find paths of maximum influence.
# Instead of minimizing distance, I maximize the % of times it would hit.
def max_influence_algo(graph, start):
        # scores all nodes to 0,start node is 1
    scores = {node: 0 for node in graph}
    scores[start] = 1
        # Track the prev node on optimal path to each node
    prev = {node: None for node in graph}
        # Max-heap priority queue initialized with start node
    heap = [(-1, start)]

        # explore nodes while the heap is not empty
    while heap:
                # Pop the node with the highest current score
        curr_score_neg, node = heapq.heappop(heap)
                # Convert back to pos. cuz heapq is a min-heap by default
        curr_score = -curr_score_neg
                # Explore each neighboring node and compute new score
        for neighbor, weight in graph[node].items():
                        # Multiply to add up the influence along the path
            new_score = curr_score * weight
                        # If new influence score is greater, update 
            if new_score > scores[neighbor]:
                scores[neighbor] = new_score
                                # Record the best path to this neighbor
                prev[neighbor] = node
                                # Push the updated path to the heap (as a max-heap using negative score)
                heapq.heappush(heap, (-new_score, neighbor))
    return scores, prev

def get_path(prev, end):
    path = []
    while end:
        path.append(end)
        end = prev.get(end)
    return path[::-1]

# visuals
def visualize_graph(graph):
    G = nx.DiGraph()
    for src, targets in graph.items():
        G.add_node(src)
        for tgt, weight in targets.items():
            G.add_edge(src, tgt, weight=round(weight, 2))

    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
    nx.draw_networkx_labels(G, pos, font_size=6)
    nx.draw_networkx_edges(G, pos, arrows=True)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
    plt.title("NBA Prop Influence Graph")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# main
if __name__ == "__main__":
    logs = load_game_logs()
    graph, props = build_graph(logs)
    start_player = input("Enter starting player name (exact match): ")
    if start_player not in PROP_LINES:
        raise ValueError(f"{start_player} not in PROP_LINES. Please check the name.")
    scores, prev = max_influence_algo(graph, start_player)

    print(f"\nTop 5 most likely props to hit if {start_player} hits:")
    sorted_scores = sorted([(p, s) for p, s in scores.items() if p != start_player], key=lambda x: x[1], reverse=True)[:5]

    for target, score in sorted_scores:
        path = get_path(prev, target)
        if not path:
            continue
        readable_path = [f"{p} o{list(PROP_LINES[p].keys())[0]}" for p in path]
        print(f"Path: {' -> '.join(readable_path)} | Score: {score:.4f}")

    visualize_graph(graph)
