class BOMCycleError(Exception):
    """BOM 中存在循环引用。"""
    pass


def check_bom_cycle(root_id: int, edges: dict[int, list[int]]) -> None:
    """检测从 root_id 出发是否存在循环引用。

    edges: {product_id: [子产品 product_id, ...], ...}
    若检测到循环，抛出 BOMCycleError。使用 DFS + 路径标记。
    """
    # 状态：0=未访问，1=当前路径中，2=已完成
    state: dict[int, int] = {}

    def dfs(node: int) -> None:
        if state.get(node) == 1:
            raise BOMCycleError(f"BOM 循环引用检测到: 节点 {node} 在当前路径中重复出现")
        if state.get(node) == 2:
            return  # 已验证无环
        state[node] = 1  # 标记当前路径中
        for child in edges.get(node, []):
            dfs(child)
        state[node] = 2  # 完成

    dfs(root_id)
