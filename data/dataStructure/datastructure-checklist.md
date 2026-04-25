- question: "在长度为 n 的顺序表中，在第 i 个位置插入一个元素，平均需要移动元素个数为："
  options:
    A: "n"
    B: "n/2"
    C: "i"
    D: "n-i"
  expected_points:
    - "正确答案：B"
    - "平均情况插入，需移动约一半元素"
  answerable_from_material: true
  source_material: "一、数组与链表，第1题"
  notes: "顺序表插入元素时，需要移动插入位置之后的元素。平均情况下约移动 n/2 个元素。"

- question: "单链表中删除某节点 p 的前驱节点，已知 p 指针，时间复杂度为："
  options:
    A: "O(1)"
    B: "O(log n)"
    C: "O(n)"
    D: "O(n²)"
  expected_points:
    - "正确答案：C"
    - "单链表无法直接访问前驱"
  answerable_from_material: true
  source_material: "一、数组与链表，第2题"
  notes: "单链表只有后继指针，已知 p 也不能直接找到其前驱节点，需要从头遍历。"

- question: "双链表相比单链表的主要优势是："
  options:
    A: "节省空间"
    B: "支持随机访问"
    C: "可双向遍历"
    D: "插入更慢"
  expected_points:
    - "正确答案：C"
    - "双链表增加 prev 指针"
  answerable_from_material: true
  source_material: "一、数组与链表，第3题"
  notes: "双链表每个节点通常包含前驱指针和后继指针，因此可以双向遍历。"

- question: "循环队列中，判断队满的条件是："
  options:
    A: "front == rear"
    B: "front + 1 == rear"
    C: "(rear + 1) % maxSize == front"
    D: "rear == maxSize"
  expected_points:
    - "正确答案：C"
    - "经典循环队列判满条件"
  answerable_from_material: true
  source_material: "二、栈与队列，第4题"
  notes: "循环队列通常牺牲一个存储单元区分队空和队满。队满条件为 (rear + 1) % maxSize == front。"

- question: "用栈实现递归的本质是："
  options:
    A: "队列操作"
    B: "函数调用栈"
    C: "数组模拟"
    D: "指针运算"
  expected_points:
    - "正确答案：B"
    - "系统栈保存调用信息"
  answerable_from_material: true
  source_material: "二、栈与队列，第5题"
  notes: "递归调用过程中，系统使用函数调用栈保存返回地址、局部变量和调用状态。"

- question: "表达式求值中，中缀转后缀主要利用："
  options:
    A: "队列"
    B: "栈"
    C: "数组"
    D: "树"
  expected_points:
    - "正确答案：B"
    - "运算符入栈"
  answerable_from_material: true
  source_material: "二、栈与队列，第6题"
  notes: "中缀表达式转后缀表达式时，通常使用栈处理运算符优先级和括号。"

- question: "递归算法必须具备："
  options:
    A: "循环结构"
    B: "终止条件"
    C: "多重分支"
    D: "指针操作"
  expected_points:
    - "正确答案：B"
    - "否则无限递归"
  answerable_from_material: true
  source_material: "三、递归与广义表，第7题"
  notes: "递归算法必须有递归出口，也就是终止条件。"

- question: "广义表 (a,(b,c)) 的深度为："
  options:
    A: "1"
    B: "2"
    C: "3"
    D: "4"
  expected_points:
    - "正确答案：B"
    - "最大嵌套层数"
  answerable_from_material: true
  source_material: "三、递归与广义表，第8题"
  notes: "外层表为第 1 层，内部子表 (b,c) 为第 2 层，因此深度为 2。"

- question: "一棵有 n 个节点的二叉树，其空指针域个数为："
  options:
    A: "n"
    B: "n+1"
    C: "n-1"
    D: "2n"
  expected_points:
    - "正确答案：B"
    - "空指针 = n+1"
    - "这是重要考点"
  answerable_from_material: true
  source_material: "四、树与森林，第9题"
  notes: "n 个节点共有 2n 个指针域，非空指针对应边数 n-1，所以空指针域为 2n - (n-1) = n+1。"

- question: "已知二叉树前序和中序遍历，能否唯一确定一棵树："
  options:
    A: "不能"
    B: "能"
    C: "仅完全二叉树可以"
    D: "仅满二叉树可以"
  expected_points:
    - "正确答案：B"
    - "经典构造问题"
  answerable_from_material: true
  source_material: "四、树与森林，第10题"
  notes: "前序遍历确定根节点，中序遍历确定左右子树范围，因此可以唯一确定二叉树。"

- question: "森林转二叉树采用："
  options:
    A: "顺序存储"
    B: "左孩子右兄弟表示法"
    C: "哈希映射"
    D: "邻接矩阵"
  expected_points:
    - "正确答案：B"
    - "标准转换方法"
  answerable_from_material: true
  source_material: "四、树与森林，第11题"
  notes: "森林转二叉树通常采用左孩子右兄弟表示法。"

- question: "树的高度定义为："
  options:
    A: "节点数"
    B: "边数"
    C: "最大层数"
    D: "最小路径"
  expected_points:
    - "正确答案：C"
    - "根到最深叶的层数"
  answerable_from_material: true
  source_material: "四、树与森林，第12题"
  notes: "该文档中树的高度按最大层数定义。部分教材可能用边数定义高度，需注意口径。"

- question: "顺序查找的平均查找长度（成功）为："
  options:
    A: "n"
    B: "n/2"
    C: "log n"
    D: "1"
  expected_points:
    - "正确答案：B"
    - "平均比较次数"
  answerable_from_material: true
  source_material: "五、集合与搜索，第13题"
  notes: "严格地说，顺序查找成功时平均查找长度常写为 (n+1)/2。该题选项中最接近的是 n/2。"

- question: "二分查找失败的时间复杂度为："
  options:
    A: "O(1)"
    B: "O(log n)"
    C: "O(n)"
    D: "O(n log n)"
  expected_points:
    - "正确答案：B"
    - "依然是对数级"
  answerable_from_material: true
  source_material: "五、集合与搜索，第14题"
  notes: "二分查找每次将查找区间缩小一半，即使查找失败，时间复杂度仍为 O(log n)。"

- question: "二叉搜索树查找性能取决于："
  options:
    A: "节点值"
    B: "树的高度"
    C: "插入顺序"
    D: "节点个数"
  expected_points:
    - "正确答案：B"
    - "高度决定复杂度"
  answerable_from_material: true
  source_material: "五、集合与搜索，第15题"
  notes: "二叉搜索树查找路径长度由树高决定。平衡时接近 O(log n)，退化时可能为 O(n)。"

- question: "图的邻接矩阵适用于："
  options:
    A: "稀疏图"
    B: "稠密图"
    C: "树"
    D: "DAG"
  expected_points:
    - "正确答案：B"
    - "空间复杂度高"
  answerable_from_material: true
  source_material: "六、图，第16题"
  notes: "邻接矩阵空间复杂度为 O(n²)，适合边较多的稠密图。"

- question: "无向图中边数为 e，则邻接矩阵中非零元素个数为："
  options:
    A: "e"
    B: "2e"
    C: "e/2"
    D: "n"
  expected_points:
    - "正确答案：B"
    - "对称矩阵"
  answerable_from_material: true
  source_material: "六、图，第17题"
  notes: "无向图中每条边在邻接矩阵中对应两个对称位置，因此非零元素个数为 2e。"

- question: "拓扑排序适用于："
  options:
    A: "无向图"
    B: "有向无环图"
    C: "完全图"
    D: "树"
  expected_points:
    - "正确答案：B"
    - "DAG"
  answerable_from_material: true
  source_material: "六、图，第18题"
  notes: "拓扑排序只适用于有向无环图，即 DAG。"

- question: "Dijkstra算法不能处理："
  options:
    A: "正权图"
    B: "负权边"
    C: "稠密图"
    D: "稀疏图"
  expected_points:
    - "正确答案：B"
    - "负权需 Bellman-Ford"
  answerable_from_material: true
  source_material: "六、图，第19题"
  notes: "Dijkstra 算法依赖贪心策略，存在负权边时可能得到错误结果。"

- question: "稳定排序算法是："
  options:
    A: "快速排序"
    B: "堆排序"
    C: "归并排序"
    D: "选择排序"
  expected_points:
    - "正确答案：C"
    - "稳定性经典考点"
  answerable_from_material: true
  source_material: "七、排序，第20题"
  notes: "归并排序通常是稳定排序。快速排序、堆排序、选择排序通常不稳定。"

- question: "堆排序的时间复杂度为："
  options:
    A: "O(n²)"
    B: "O(n log n)"
    C: "O(n)"
    D: "O(log n)"
  expected_points:
    - "正确答案：B"
    - "建堆+调整"
  answerable_from_material: true
  source_material: "七、排序，第21题"
  notes: "堆排序整体时间复杂度为 O(n log n)。"

- question: "快速排序性能最差情况是："
  options:
    A: "随机数组"
    B: "已排序数组（不优化）"
    C: "逆序数组"
    D: "重复元素"
  expected_points:
    - "正确答案：B"
    - "极端划分"
  answerable_from_material: true
  source_material: "七、排序，第22题"
  notes: "当 pivot 选择不优化时，已排序数组可能导致划分极不均衡，快速排序退化为 O(n²)。"

- question: "哈希函数设计原则不包括："
  options:
    A: "均匀性"
    B: "简单性"
    C: "单调性"
    D: "低冲突"
  expected_points:
    - "正确答案：C"
    - "单调性不是要求"
  answerable_from_material: true
  source_material: "八、索引与散列，第23题"
  notes: "哈希函数设计通常强调计算简单、分布均匀、冲突少。单调性不是哈希函数的必要设计原则。"

- question: "负载因子定义为："
  options:
    A: "表长/元素数"
    B: "元素数/表长"
    C: "冲突数/表长"
    D: "查找次数"
  expected_points:
    - "正确答案：B"
    - "α = n/m"
  answerable_from_material: true
  source_material: "八、索引与散列，第24题"
  notes: "负载因子通常表示哈希表中元素数与表长的比值。"

- question: "B树主要用于："
  options:
    A: "内存排序"
    B: "图遍历"
    C: "外存索引"
    D: "栈实现"
  expected_points:
    - "正确答案：C"
    - "数据库/磁盘优化结构"
  answerable_from_material: true
  source_material: "八、索引与散列，第25题"
  notes: "B 树适合外存索引，常用于数据库和文件系统，以减少磁盘 I/O。"