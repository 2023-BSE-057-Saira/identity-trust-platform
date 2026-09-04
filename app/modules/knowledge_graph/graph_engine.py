"""
Identity Knowledge Graph.

Built with NetworkX rather than Neo4j - deliberate choice, matching the
project's established pattern (see trust_scoring/engine.py) of choosing
lightweight, explainable, install-safe tools over heavier infra when the
functional requirement doesn't demand it. A directed multigraph rebuilt
from Postgres on each request is more than sufficient for this project's
data volume and avoids adding another database service + driver to
install under a 1-week deadline.

Nodes carry a `type` attribute: user | document | device | ip | phone | fraud_case
Edges carry a `relation` attribute describing how the two nodes are linked.
"""

from typing import Dict, List
import networkx as nx
from sqlalchemy.orm import Session

from app.models import User, Document, VerificationSession

# A session is treated as evidence of fraud once its risk is "high" -
# same cutoff as trust_scoring/engine.py - or it was explicitly failed.
FRAUD_TRUST_SCORE_CUTOFF = 45.0


def _user_node(user_id: str) -> str:
    return f"user:{user_id}"


def _document_node(doc_id: str) -> str:
    return f"document:{doc_id}"


def _device_node(fingerprint: str) -> str:
    return f"device:{fingerprint}"


def _ip_node(ip: str) -> str:
    return f"ip:{ip}"


def _phone_node(phone: str) -> str:
    return f"phone:{phone}"


def _fraud_case_node(session_id: str) -> str:
    return f"fraud_case:{session_id}"


def build_identity_graph(db: Session) -> nx.MultiDiGraph:
    """
    Rebuilds the full identity knowledge graph from the current DB state.
    Called fresh per-request - fine at this data scale (demo/coursework),
    and it means the graph is always consistent with the DB with zero
    separate sync logic to maintain.
    """
    g = nx.MultiDiGraph()

    users = db.query(User).all()
    for u in users:
        g.add_node(_user_node(u.id), type="user", label=u.email, role=u.role)
        if u.phone_number:
            g.add_node(_phone_node(u.phone_number), type="phone", label=u.phone_number)
            g.add_edge(_user_node(u.id), _phone_node(u.phone_number), relation="has_phone")

    documents = db.query(Document).all()
    for d in documents:
        g.add_node(
            _document_node(d.id), type="document", label=d.document_type,
            is_forged=bool(d.is_forged),
        )
        if d.user_id:
            g.add_edge(_user_node(d.user_id), _document_node(d.id), relation="uploaded")

    sessions = db.query(VerificationSession).all()
    for s in sessions:
        if s.device_fingerprint:
            g.add_node(_device_node(s.device_fingerprint), type="device", label=s.device_fingerprint[:12])
            g.add_edge(_user_node(s.user_id), _device_node(s.device_fingerprint), relation="used_device")

        if s.ip_address:
            g.add_node(_ip_node(s.ip_address), type="ip", label=s.ip_address)
            g.add_edge(_user_node(s.user_id), _ip_node(s.ip_address), relation="used_ip")

        is_high_risk = (
            (s.trust_score is not None and s.trust_score < FRAUD_TRUST_SCORE_CUTOFF)
            or s.status == "failed"
        )
        if is_high_risk:
            g.add_node(
                _fraud_case_node(s.id), type="fraud_case", label=f"Session {s.id[:8]}",
                trust_score=s.trust_score, status=s.status,
            )
            g.add_edge(_user_node(s.user_id), _fraud_case_node(s.id), relation="flagged_in")
            if s.document_id:
                g.add_edge(_document_node(s.document_id), _fraud_case_node(s.id), relation="evidence_in")

    return g


def graph_to_json(g: nx.MultiDiGraph) -> Dict:
    """
    Serializes the graph into a simple {nodes, edges} shape any frontend
    graph library (vis.js, d3, cytoscape) can consume directly for the
    Executive Dashboard / investigation view.
    """
    nodes = [{"id": n, **data} for n, data in g.nodes(data=True)]
    edges = [
        {"source": u, "target": v, "relation": data.get("relation")}
        for u, v, data in g.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


def get_user_subgraph_json(db: Session, user_id: str, hops: int = 2) -> Dict:
    """
    Returns the neighborhood around one user out to `hops` edges - this is
    the "Compare this face with previous records" / investigation-summary
    view: everything connected to a specific person, not the whole graph.
    """
    g = build_identity_graph(db)
    start = _user_node(user_id)
    if start not in g:
        return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

    undirected = g.to_undirected()
    nodes_in_reach = nx.single_source_shortest_path_length(undirected, start, cutoff=hops).keys()
    sub = g.subgraph(nodes_in_reach)
    return graph_to_json(sub)


def detect_fraud_rings(db: Session, min_users: int = 2) -> List[Dict]:
    """
    Fraud ring detection: finds clusters of DIFFERENT users connected through
    a shared device or shared IP address. Two strangers whose accounts touch
    the same device fingerprint or the same IP is a classic account-takeover
    / synthetic-identity-ring signal. This is the case study's "fraud ring
    detection" bonus differentiator, built directly on top of the same
    graph rather than as a separate system.
    """
    g = build_identity_graph(db)

    # Only keep user<->device and user<->ip edges for this analysis -
    # document/phone/fraud_case nodes would connect everything trivially
    # through a shared user, which isn't the signal we're after here.
    shared_edges = [
        (u, v) for u, v, d in g.edges(data=True)
        if d.get("relation") in ("used_device", "used_ip")
    ]
    ring_graph = nx.Graph()
    ring_graph.add_edges_from(shared_edges)

    rings = []
    for component in nx.connected_components(ring_graph):
        users_in_component = {n for n in component if n.startswith("user:")}
        shared_nodes = {n for n in component if n.startswith("device:") or n.startswith("ip:")}
        if len(users_in_component) >= min_users:
            rings.append({
                "users": sorted(users_in_component),
                "shared_devices_or_ips": sorted(shared_nodes),
                "ring_size": len(users_in_component),
            })

    return sorted(rings, key=lambda r: r["ring_size"], reverse=True)
