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
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphRelationship(BaseModel):
    source_id: str
    target_id: str
    rel_type: str  # CONTAINS, CALLS, IMPLEMENTS, MUTATES


class CodeGraph(BaseModel):
    """
    Production-grade Code Knowledge Graph with Neo4j Cypher query support
    and in-memory graph indexing fallback.
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
        except Exception:
            if driver:
                try:
                    driver.close()
                except Exception:
                    pass
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

        # Sync node to Neo4j via Cypher if connected
        cypher = f"MERGE (n:{node.label} {{id: $id}}) SET n.name = $name"
        self.execute_cypher(cypher, {"id": node.id, "name": node.name})

    def add_relationship(self, rel: GraphRelationship) -> None:
        self.relationships.append(rel)

        # Sync relationship to Neo4j via Cypher if connected
        cypher = f"""
        MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
        MERGE (s)-[r:{rel.rel_type}]->(t)
        """
        self.execute_cypher(cypher, {"source_id": rel.source_id, "target_id": rel.target_id})

    def find_callers(self, target_name: str) -> List[GraphNode]:
        # Try Cypher query first
        cypher = """
        MATCH (s:Function)-[r:CALLS]->(t:Function)
        WHERE t.name = $target_name
        RETURN s.id AS id, s.name AS name
        """
        cypher_results = self.execute_cypher(cypher, {"target_name": target_name})
        if cypher_results:
            callers = []
            for row in cypher_results:
                node_id = row.get("id")
                if node_id in self.nodes:
                    callers.append(self.nodes[node_id])
                else:
                    callers.append(GraphNode(id=node_id, label="Function", name=row.get("name", target_name)))
            return callers

        # In-memory graph traversal fallback
        target_ids = [n.id for n in self.nodes.values() if n.name == target_name]
        caller_ids = [rel.source_id for rel in self.relationships if rel.target_id in target_ids and rel.rel_type == "CALLS"]
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
                except Exception:
                    pass

        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "node_labels": labels,
            "neo4j_driver_available": driver_available
        }
