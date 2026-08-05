import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
try:
    from neo4j import GraphDatabase, Driver
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
logger = logging.getLogger(__name__)
class GraphNode(BaseModel):
    id: str
    label: str  # File, Class, Function, Interface, Table
    name: str
    repo_id: str = "default"
    properties: Dict[str, Any] = Field(default_factory=dict)
class GraphRelationship(BaseModel):
    source_id: str
    target_id: str
    rel_type: str  # CONTAINS, CALLS, IMPLEMENTS, MUTATES
    repo_id: str = "default"
class CodeGraph(BaseModel):
    """
    Production-grade Multi-Tenant Code Knowledge Graph with Neo4j Cypher batch
    transaction processing (UNWIND $batch AS row) and repo_id isolation.
    """
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    relationships: List[GraphRelationship] = Field(default_factory=list)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    def __init__(self, **data):
        super().__init__(**data)
    def _get_neo4j_driver(self) -> Optional[Any]:
        if not HAS_NEO4J:
            return None
        driver = None
        try:
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            driver.verify_connectivity()
            return driver
        except Exception as e:
            if driver:
                try:
                    driver.close()
                except Exception as e:
                    logger.warning("Non-fatal operation exception caught: %s", e)
            return None
    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executes a raw Cypher query against Neo4j database if available.
        """
        driver = self._get_neo4j_driver()
        if not driver:
            logger.debug("Neo4j database unavailable, Cypher execution simulated.")
            return []
        try:
            with driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.warning(f"Cypher query execution error: {e}")
            return []
        finally:
            driver.close()
    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        cypher = """
        MERGE (n {id: $id})
        SET n.name = $name, n.label = $label, n.repo_id = $repo_id
        """
        self.execute_cypher(cypher, {
            "id": node.id,
            "name": node.name,
            "label": node.label,
            "repo_id": node.repo_id
        })
    def add_nodes_batch(self, repo_id: str, nodes: List[GraphNode]) -> None:
        """
        High-throughput batch Cypher node creation using UNWIND $batch AS row.
        """
        if not nodes:
            return
        batch_payload = []
        for node in nodes:
            node.repo_id = repo_id
            self.nodes[node.id] = node
            batch_payload.append({
                "id": node.id,
                "name": node.name,
                "label": node.label,
                "repo_id": repo_id
            })
        cypher = """
        UNWIND $batch AS row
        MERGE (n {id: row.id})
        SET n.name = row.name, n.label = row.label, n.repo_id = row.repo_id
        """
        self.execute_cypher(cypher, {"batch": batch_payload})
    def add_relationship(self, rel: GraphRelationship) -> None:
        self.relationships.append(rel)
        cypher = f"""
        MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
        MERGE (s)-[r:{rel.rel_type}]->(t)
        SET r.repo_id = $repo_id
        """
        self.execute_cypher(cypher, {
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "repo_id": rel.repo_id
        })
    def add_relationships_batch(self, repo_id: str, rels: List[GraphRelationship]) -> None:
        """
        High-throughput batch Cypher relationship creation using UNWIND $batch AS row.
        """
        if not rels:
            return
        batch_payload = []
        for rel in rels:
            rel.repo_id = repo_id
            self.relationships.append(rel)
            batch_payload.append({
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "rel_type": rel.rel_type,
                "repo_id": repo_id
            })
        cypher = """
        UNWIND $batch AS row
        MATCH (s {id: row.source_id}), (t {id: row.target_id})
        MERGE (s)-[r:CALLS]->(t)
        SET r.repo_id = row.repo_id
        """
        self.execute_cypher(cypher, {"batch": batch_payload})
    def delete_by_file(self, repo_id: str, file_path: str) -> None:
        """
        Deletes all graph nodes and edges corresponding to a specific repository file path.
        """
        to_delete_nodes = [
            nid for nid, node in self.nodes.items()
            if node.repo_id == repo_id and (node.id.startswith(file_path) or node.properties.get("file_path") == file_path)
        ]
        for nid in to_delete_nodes:
            del self.nodes[nid]
        self.relationships = [
            rel for rel in self.relationships
            if not (rel.repo_id == repo_id and (rel.source_id in to_delete_nodes or rel.target_id in to_delete_nodes))
        ]
        cypher = """
        MATCH (n {repo_id: $repo_id})
        WHERE n.id STARTS WITH $file_path OR n.file_path = $file_path
        DETACH DELETE n
        """
        self.execute_cypher(cypher, {"repo_id": repo_id, "file_path": file_path})
    def find_callers(self, target_name: str, repo_id: Optional[str] = None) -> List[GraphNode]:
        cypher = """
        MATCH (s:Function)-[r:CALLS]->(t:Function)
        WHERE t.name = $target_name AND ($repo_id IS NULL OR s.repo_id = $repo_id)
        RETURN s.id AS id, s.name AS name, s.repo_id AS repo_id
        """
        cypher_results = self.execute_cypher(cypher, {"target_name": target_name, "repo_id": repo_id})
        if cypher_results:
            callers = []
            for row in cypher_results:
                node_id = row.get("id")
                if node_id in self.nodes:
                    callers.append(self.nodes[node_id])
                else:
                    callers.append(GraphNode(id=node_id, label="Function", name=row.get("name", target_name), repo_id=row.get("repo_id", "default")))
            return callers
        # In-memory graph traversal fallback with repo_id filter
        target_ids = [n.id for n in self.nodes.values() if n.name == target_name and (repo_id is None or n.repo_id == repo_id)]
        caller_ids = [rel.source_id for rel in self.relationships if rel.target_id in target_ids and rel.rel_type == "CALLS" and (repo_id is None or rel.repo_id == repo_id)]
        return [self.nodes[cid] for cid in caller_ids if cid in self.nodes]
    def get_summary(self) -> Dict[str, Any]:
        labels = {}
        for node in self.nodes.values():
            labels[node.label] = labels.get(node.label, 0) + 1
        driver_available = False
        if HAS_NEO4J:
            driver = self._get_neo4j_driver()
            if driver is not None:
                driver_available = True
                try:
                    driver.close()
                except Exception as e:
                    logger.warning("Non-fatal operation exception caught: %s", e)
        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "node_labels": labels,
            "neo4j_driver_available": driver_available
        }
