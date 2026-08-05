from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    relationships: List[GraphRelationship] = Field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_relationship(self, rel: GraphRelationship) -> None:
        self.relationships.append(rel)

    def find_callers(self, target_name: str) -> List[GraphNode]:
        target_ids = [n.id for n in self.nodes.values() if n.name == target_name]
        caller_ids = [rel.source_id for rel in self.relationships if rel.target_id in target_ids and rel.rel_type == "CALLS"]
        return [self.nodes[cid] for cid in caller_ids if cid in self.nodes]

    def get_summary(self) -> Dict[str, int]:
        labels = {}
        for node in self.nodes.values():
            labels[node.label] = labels.get(node.label, 0) + 1
        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "node_labels": labels
        }
