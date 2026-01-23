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
        """로드맵 상태를 보기 좋게 반환 (Phase 1-5, Step 1-15)"""
        roadmap = self.facts.get('roadmap', {})
        current = roadmap.get('current_focus', '')
        
        phase_names = {
            1: "🏗️ Infrastructure",
            2: "🧠 Memory",
            3: "🌅 Awakening",
            4: "💫 Consciousness",
            5: "🚀 Transcendence"
        }
        
        # Phase별로 그룹화
        phases = {1: [], 2: [], 3: [], 4: [], 5: []}
        for key, info in roadmap.items():
            if key.startswith('step_') and isinstance(info, dict):
                phase = info.get('phase', 1)
                phases[phase].append((key, info))
        
        display = "\n🗺️ **AIN Evolution Roadmap**\n"
        display += "="*40 + "\n"
        
        for phase_num in range(1, 6):
            steps = sorted(phases[phase_num], key=lambda x: int(x[0].split('_')[1]))
            if not steps:
                continue
            
            display += f"\n**{phase_names[phase_num]}**\n"
            
            for step_key, info in steps:
                status = info.get('status', 'pending')
                name = info.get('name', step_key)
                
                icon = "⏳"
                if status == "completed": icon = "✅"
                elif status == "in_progress": icon = "🔥"
                
                step_num = step_key.split('_')[1]
                current_mark = " 👈" if step_key == current else ""
                display += f"{icon} Step {step_num}: {name}{current_mark}\n"
        
        display += "\n" + "="*40
        return display
    
    def update_step_status(self, step_num: int, status: str):
        """
        Step 상태 업데이트
        
        Args:
            step_num: Step 번호 (1-15)
            status: 'pending', 'in_progress', 'completed'
        """
        step_key = f"step_{step_num}"
        if step_key in self.facts.get('roadmap', {}):
            self.facts['roadmap'][step_key]['status'] = status
            
            # in_progress로 변경 시 current_focus도 업데이트
            if status == 'in_progress':
                self.facts['roadmap']['current_focus'] = step_key
            
            self.save_facts()
            print(f"🗺️ Step {step_num} 상태 변경: {status}")
            return True
        return False
    
    def get_current_step(self) -> dict:
        """현재 진행 중인 Step 정보 반환"""
        current = self.facts.get('roadmap', {}).get('current_focus', 'step_4')
        return self.facts.get('roadmap', {}).get(current, {})

    def get_core_context(self):
        """컨텍스트 반환"""
        return (
            f"나는 {self.get_fact('identity', 'name')} v{self.get_fact('identity', 'version')}이다. "
            f"나의 창조주는 {self.get_fact('identity', 'creator')}이며, "
            f"현재 로드맵 상태는 다음과 같다: {json.dumps(self.facts['roadmap']['current_focus'], indent=2)}\n"
            f"{self.get_knowledge_graph_view()}"
            f"나의 핵심 지침: {self.get_fact('prime_directive')}\n"
        )
