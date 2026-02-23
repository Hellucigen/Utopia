from utils import normalize_concept, generate_node_id
def run(graph, am, current_text=None):
    """执行 Answer 动作：打印当前最高激活节点的名称"""
    if am.activations:
        max_node_id = max(am.activations, key=am.activations.get)
        node = graph.nodes[max_node_id]
        name = node.attributes.get('name', max_node_id)
        print(f'>{name}')
    else:
        print('当前无激活节点')
