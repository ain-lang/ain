"""
Facts Node: 지식 그래프의 단일 노드
"""


class KnowledgeNode:
    """지식 그래프의 단일 노드"""
    
    def __init__(self, label, data=None):
        self.label = label
        self.data = data if data else {}
        self.edges = []  # (relation, target_node_label)

    def add_edge(self, relation, target_label):
        self.edges.append((relation, target_label))

    def addedge(self, relation, target_label):
        """AIN의 오타 대응을 위한 별칭"""
        self.add_edge(relation, target_label)

    def __getattr__(self, name):
        """동적 메소드 매핑: 오타를 정식 이름으로 연결"""
        mapping = {
            "addedge": self.add_edge,
            "to_dict": self.to_dict,
            "add_edge": self.add_edge
        }
        fuzzy_name = name.replace("_", "").lower()
        for k, v in mapping.items():
            if k.replace("_", "").lower() == fuzzy_name:
                return v
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def to_dict(self):
        return {
            "data": self.data,
            "relations": [f"--({r})--> [{t}]" for r, t in self.edges]
        }
