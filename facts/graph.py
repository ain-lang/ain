"""
Facts Graph: 그래프 빌드 및 뷰
"""
import json
from .node import KnowledgeNode


class GraphMixin:
    """그래프 관련 믹스인"""
    
    def _build_initial_graph(self):
        """기존 딕셔너리 데이터를 그래프 노드로 변환"""
        for key, value in self.facts.items():
            if isinstance(value, dict):
                node = KnowledgeNode(key, value)
                self.nodes[key] = node
        
        if "identity" in self.nodes and "creator" in self.facts["identity"]:
            self.nodes["identity"].add_edge("created_by", self.facts["identity"]["creator"])
            self.nodes["identity"].add_edge("has_goal", "Self-Evolution")

    def get_knowledge_graph_view(self):
        """현재 활성화된 지식 그래프의 상태를 텍스트로 시각화"""
        view = "### 🕸️ Active Knowledge Graph Nodes\n"
        for label, node in self.nodes.items():
            view += f"- **[{label}]**\n"
            for rel in node.edges:
                view += f"    └─ {rel[0]} --> [{rel[1]}]\n"
        return view
    
    def get_formatted_roadmap(self):
        """로드맵 상태를 보기 좋게 반환"""
        roadmap = self.facts.get('roadmap', {}).get('phase_1_mvp', {})
        current = self.facts.get('roadmap', {}).get('current_focus', '')
        
        display = "\n🗺️ **AIN Evolution Roadmap (Phase 1)**\n"
        display += "="*40 + "\n"
        
        steps = sorted(roadmap.keys())
        for step in steps:
            info = roadmap[step]
            status = info['status']
            desc = info['desc']
            
            icon = "⬜"
            if status == "completed": icon = "✅"
            elif status == "in_progress": icon = "🔥"
            
            highlight = "👈 CURRENT FOCUS" if step == current else ""
            display += f"{icon} **{step.replace('_', ' ').upper()}**\n   └─ {desc} {highlight}\n"
            
        display += "="*40 + "\n"
        return display

    def get_core_context(self):
        """컨텍스트 반환"""
        return (
            f"나는 {self.get_fact('identity', 'name')} v{self.get_fact('identity', 'version')}이다. "
            f"나의 창조주는 {self.get_fact('identity', 'creator')}이며, "
            f"현재 로드맵 상태는 다음과 같다: {json.dumps(self.facts['roadmap']['current_focus'], indent=2)}\n"
            f"{self.get_knowledge_graph_view()}"
            f"나의 핵심 지침: {self.get_fact('prime_directive')}\n"
        )
