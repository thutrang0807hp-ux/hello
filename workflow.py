"""Validate saved node graphs before they become reusable workspace data."""
import math
from services import ServiceError, text

ALLOWED = {'job': ('draft', 'final'), 'template': ('draft', 'final'), 'draft': ('review', 'final'), 'review': ('final',), 'final': ('review',)}


def validate_workspace(workspace):
    if not isinstance(workspace, dict) or workspace.get('version') != 1:
        raise ServiceError('Phiên bản workspace không hợp lệ.')
    nodes, edges = workspace.get('nodes'), workspace.get('edges')
    if not isinstance(nodes, list) or not 0 <= len(nodes) <= 30 or not isinstance(edges, list) or len(edges) > 100:
        raise ServiceError('Workspace hỗ trợ tối đa 30 node và tối đa 100 kết nối.')
    by_id = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get('type'), str) or node.get('type') not in ALLOWED:
            raise ServiceError('Loại node không hợp lệ.')
        ident = text(node.get('id'), 80)
        if not ident or ident in by_id or not all(c.isalnum() or c in '-_' for c in ident):
            raise ServiceError('ID node cần duy nhất và chỉ chứa chữ, số, dấu - hoặc _.')
        for field in ('x', 'y'):
            value = node.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 20000:
                raise ServiceError('Vị trí node không hợp lệ.')
        text(node.get('content'))
        text(node.get('title'), 1000)
        by_id[ident] = node
    connections = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ServiceError('Kết nối không hợp lệ.')
        source, target = edge.get('from'), edge.get('to')
        if not isinstance(source, str) or not isinstance(target, str) or source not in by_id or target not in by_id or source == target or (source, target) in connections:
            raise ServiceError('Kết nối cần hai node hợp lệ và không trùng.')
        if by_id[target]['type'] not in ALLOWED[by_id[source]['type']]:
            raise ServiceError('Hai loại node không có luồng dữ liệu phù hợp.')
        connections.add((source, target))
    visiting, visited = set(), set()
    def visit(ident):
        if ident in visiting:
            raise ServiceError('Workspace không được có kết nối vòng lặp.')
        if ident in visited:
            return
        visiting.add(ident)
        for source, target in connections:
            if source == ident:
                visit(target)
        visiting.remove(ident)
        visited.add(ident)
    for ident in by_id:
        visit(ident)
    if 'scale' in workspace:
        scale = workspace['scale']
        if type(scale) not in (int, float) or not math.isfinite(scale) or not .25 <= scale <= 2:
            raise ServiceError('Mức phóng canvas không hợp lệ.')
    return workspace
