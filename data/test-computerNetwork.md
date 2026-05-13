
- question: "OSI 七层模型中，负责端到端通信控制的是哪一层？"  
  options:  
  A: "网络层"  
  B: "传输层"  
  C: "会话层"  
  D: "表示层"  
  expected_points:

  - "正确答案：B"

  - "传输层负责端到端通信，如TCP/UDP"  
    answerable_from_material: true  
    source_material: "一、OSI模型，第1题"  
    notes: "传输层提供可靠或不可靠的数据传输服务"



- question: "TCP协议属于OSI模型中的哪一层？"  
  options:  
  A: "网络层"  
  B: "数据链路层"  
  C: "传输层"  
  D: "应用层"  
  expected_points:
  
  - "正确答案：C"
  
  - "TCP是传输层协议"  
    answerable_from_material: true  
    source_material: "一、OSI模型，第2题"  
    notes: "TCP提供可靠传输"



- question: "IP协议的主要功能是："  
  options:  
  A: "保证数据可靠传输"  
  B: "数据分段"  
  C: "路由与寻址"  
  D: "流量控制"  
  expected_points:
  
  - "正确答案：C"
  
  - "IP负责逻辑寻址与路由选择"  
    answerable_from_material: true  
    source_material: "二、网络层，第1题"  
    notes: "IP是无连接、不可靠协议"



- question: "HTTP协议默认使用的端口号是："  
  options:  
  A: "21"  
  B: "25"  
  C: "80"  
  D: "443"  
  expected_points:
  
  - "正确答案：C"
  
  - "HTTP默认端口80"  
    answerable_from_material: true  
    source_material: "三、应用层，第1题"  
    notes: "HTTPS是443"



- question: "HTTPS相比HTTP增加了什么机制？"  
  options:  
  A: "压缩"  
  B: "缓存"  
  C: "加密"  
  D: "分段"  
  expected_points:
  
  - "正确答案：C"
  
  - "HTTPS基于TLS实现加密"  
    answerable_from_material: true  
    source_material: "三、应用层，第2题"  
    notes: "保证安全性"



- question: "DNS的作用是："  
  options:  
  A: "数据加密"  
  B: "域名解析"  
  C: "路由选择"  
  D: "流量控制"  
  expected_points:
  
  - "正确答案：B"
  
  - "DNS将域名解析为IP地址"  
    answerable_from_material: true  
    source_material: "三、应用层，第3题"  
    notes: "互联网基础服务"



- question: "TCP三次握手的主要目的是："  
  options:  
  A: "提高速度"  
  B: "建立连接并同步序号"  
  C: "减少丢包"  
  D: "节省带宽"  
  expected_points:
  
  - "正确答案：B"
  
  - "确保双方收发能力正常"  
    answerable_from_material: true  
    source_material: "四、TCP，第1题"  
    notes: "同步序列号"



- question: "TCP三次握手中第二次握手发送的是："  
  options:  
  A: "SYN"  
  B: "ACK"  
  C: "SYN+ACK"  
  D: "FIN"  
  expected_points:
  
  - "正确答案：C"
  
  - "服务器返回SYN+ACK"  
    answerable_from_material: true  
    source_material: "四、TCP，第2题"  
    notes: "确认并请求连接"



- question: "TCP四次挥手中，最后一个状态是："  
  options:  
  A: "ESTABLISHED"  
  B: "FIN_WAIT"  
  C: "TIME_WAIT"  
  D: "CLOSE_WAIT"  
  expected_points:
  
  - "正确答案：C"
  
  - "防止旧连接数据影响新连接"  
    answerable_from_material: true  
    source_material: "四、TCP，第3题"  
    notes: "等待2MSL"



- question: "UDP协议的特点是："  
  options:  
  A: "可靠传输"  
  B: "面向连接"  
  C: "无连接"  
  D: "保证顺序"  
  expected_points:
  
  - "正确答案：C"
  
  - "UDP无连接、不可靠"  
    answerable_from_material: true  
    source_material: "四、UDP，第1题"  
    notes: "适合实时应用"



- question: "TCP提供可靠性的机制不包括："  
  options:  
  A: "确认机制"  
  B: "重传机制"  
  C: "拥塞控制"  
  D: "IP寻址"  
  expected_points:
  
  - "正确答案：D"
  
  - "IP寻址属于网络层"  
    answerable_from_material: true  
    source_material: "四、TCP，第4题"  
    notes: "TCP可靠性机制"



- question: "滑动窗口机制主要用于："  
  options:  
  A: "加密"  
  B: "流量控制"  
  C: "路由"  
  D: "分片"  
  expected_points:
  
  - "正确答案：B"
  
  - "控制发送速率"  
    answerable_from_material: true  
    source_material: "四、TCP，第5题"  
    notes: "避免接收方溢出"



- question: "拥塞控制的慢启动阶段特点是："  
  options:  
  A: "线性增长"  
  B: "指数增长"  
  C: "不增长"  
  D: "随机增长"  
  expected_points:
  
  - "正确答案：B"
  
  - "窗口指数增长"  
    answerable_from_material: true  
    source_material: "四、TCP，第6题"  
    notes: "初始阶段快速探测带宽"



- question: "ARP协议的作用是："  
  options:  
  A: "IP转MAC地址"  
  B: "MAC转IP地址"  
  C: "域名解析"  
  D: "数据加密"  
  expected_points:
  
  - "正确答案：A"
  
  - "地址解析协议"  
    answerable_from_material: true  
    source_material: "二、网络层，第2题"  
    notes: "局域网中使用"



- question: "ICMP协议主要用于："  
  options:  
  A: "传输数据"  
  B: "错误报告"  
  C: "加密通信"  
  D: "文件传输"  
  expected_points:
  
  - "正确答案：B"
  
  - "网络诊断"  
    answerable_from_material: true  
    source_material: "二、网络层，第3题"  
    notes: "如ping命令"



- question: "HTTP请求方法中用于获取资源的是："  
  options:  
  A: "POST"  
  B: "GET"  
  C: "PUT"  
  D: "DELETE"  
  expected_points:
  
  - "正确答案：B"
  
  - "GET用于获取资源"  
    answerable_from_material: true  
    source_material: "三、HTTP，第4题"  
    notes: "最常用方法"



- question: "HTTP状态码200表示："  
  options:  
  A: "请求失败"  
  B: "服务器错误"  
  C: "请求成功"  
  D: "重定向"  
  expected_points:
  
  - "正确答案：C"
  
  - "成功响应"  
    answerable_from_material: true  
    source_material: "三、HTTP，第5题"  
    notes: "最常见状态码"



- question: "HTTP状态码404表示："  
  options:  
  A: "成功"  
  B: "未找到资源"  
  C: "服务器错误"  
  D: "重定向"  
  expected_points:
  
  - "正确答案：B"
  
  - "资源不存在"  
    answerable_from_material: true  
    source_material: "三、HTTP，第6题"  
    notes: "常见错误"



- question: "TCP与UDP的主要区别是："  
  options:  
  A: "是否使用IP"  
  B: "是否可靠"  
  C: "是否使用端口"  
  D: "是否支持HTTP"  
  expected_points:
  
  - "正确答案：B"
  
  - "TCP可靠，UDP不可靠"  
    answerable_from_material: true  
    source_material: "四、TCP/UDP，第7题"  
    notes: "核心区别"



- question: "数据链路层的主要功能是："  
  options:  
  A: "路由选择"  
  B: "帧传输"  
  C: "应用处理"  
  D: "加密"  
  expected_points:
  
  - "正确答案：B"
  
  - "负责帧的传输"  
    answerable_from_material: true  
    source_material: "一、OSI模型，第8题"  
    notes: "包括MAC地址"



- question: "MAC地址的长度通常为："  
  options:  
  A: "16位"  
  B: "32位"  
  C: "48位"  
  D: "64位"  
  expected_points:
  
  - "正确答案：C"
  
  - "48位物理地址"  
    answerable_from_material: true  
    source_material: "二、网络层，第9题"  
    notes: "硬件地址"



- question: "IP地址IPv4长度为："  
  options:  
  A: "16位"  
  B: "32位"  
  C: "64位"  
  D: "128位"  
  expected_points:
  
  - "正确答案：B"
  
  - "IPv4是32位"  
    answerable_from_material: true  
    source_material: "二、网络层，第10题"  
    notes: "IPv6是128位"



- question: "子网掩码的作用是："  
  options:  
  A: "加密数据"  
  B: "划分网络号和主机号"  
  C: "提高速度"  
  D: "解析域名"  
  expected_points:
  
  - "正确答案：B"
  
  - "网络划分"  
    answerable_from_material: true  
    source_material: "二、网络层，第11题"  
    notes: "IP划分基础"



- question: "为什么TCP需要三次握手而不是两次？"  
  options:  
  A: "节省时间"  
  B: "避免历史连接干扰"  
  C: "提高速度"  
  D: "减少流量"  
  expected_points:
  
  - "正确答案：B"
  
  - "防止旧连接请求"  
    answerable_from_material: true  
    source_material: "四、TCP，第12题"  
    notes: "经典面试题"



- question: "为什么挥手需要四次？"  
  options:  
  A: "因为协议规定"  
  B: "双方独立关闭连接"  
  C: "减少延迟"  
  D: "提高安全性"  
  expected_points:
  
  - "正确答案：B"
  
  - "发送和接收独立"  
    answerable_from_material: true  
    source_material: "四、TCP，第13题"  
    notes: "半关闭机制"



- question: "浏览器访问网页的第一步通常是："  
  options:  
  A: "发送HTTP请求"  
  B: "DNS解析"  
  C: "建立TCP连接"  
  D: "渲染页面"  
  expected_points:
  
  - "正确答案：B"
  
  - "先解析域名"  
    answerable_from_material: true  
    source_material: "综合，第1题"  
    notes: "经典流程题"



- question: "在TCP/IP模型中，应用层对应OSI模型的哪几层？"  
  options:  
  A: "应用层"  
  B: "应用层+表示层+会话层"  
  C: "表示层+会话层"  
  D: "应用层+传输层"  
  expected_points:
  
  - "正确答案：B"
  
  - "TCP/IP将OSI高三层合并为应用层"  
    answerable_from_material: true  
    source_material: "一、体系结构，第1题"  
    notes: "模型映射关系"



- question: "数据在网络中逐层封装的过程称为："  
  options:  
  A: "解封装"  
  B: "封装"  
  C: "路由"  
  D: "分段"  
  expected_points:
  
  - "正确答案：B"
  
  - "每一层添加首部信息"  
    answerable_from_material: true  
    source_material: "一、体系结构，第2题"  
    notes: "发送端过程"



- question: "传输层数据单元通常称为："  
  options:  
  A: "帧"  
  B: "分组"  
  C: "段"  
  D: "比特流"  
  expected_points:
  
  - "正确答案：C"
  
  - "TCP称为段"  
    answerable_from_material: true  
    source_material: "一、体系结构，第3题"  
    notes: "不同层命名不同"



- question: "网络层的数据单元通常称为："  
  options:  
  A: "帧"  
  B: "数据报"  
  C: "段"  
  D: "消息"  
  expected_points:
  
  - "正确答案：B"
  
  - "IP数据报"  
    answerable_from_material: true  
    source_material: "一、体系结构，第4题"  
    notes: "IP层单位"



- question: "数据链路层的数据单元称为："  
  options:  
  A: "帧"  
  B: "段"  
  C: "数据报"  
  D: "包"  
  expected_points:
  
  - "正确答案：A"
  
  - "帧结构"  
    answerable_from_material: true  
    source_material: "一、体系结构，第5题"  
    notes: "链路层传输单位"



- question: "物理层传输的数据单位是："  
  options:  
  A: "帧"  
  B: "比特"  
  C: "数据报"  
  D: "段"  
  expected_points:
  
  - "正确答案：B"
  
  - "比特流传输"  
    answerable_from_material: true  
    source_material: "一、体系结构，第6题"  
    notes: "最底层"



- question: "TCP头部中的序列号字段用于："  
  options:  
  A: "加密"  
  B: "标识数据顺序"  
  C: "路由选择"  
  D: "错误检测"  
  expected_points:
  
  - "正确答案：B"
  
  - "保证有序传输"  
    answerable_from_material: true  
    source_material: "四、TCP，第7题"  
    notes: "核心字段"



- question: "TCP头部中的确认号字段表示："  
  options:  
  A: "已发送数据"  
  B: "期望接收的下一个字节"  
  C: "丢失数据"  
  D: "窗口大小"  
  expected_points:
  
  - "正确答案：B"
  
  - "确认机制核心"  
    answerable_from_material: true  
    source_material: "四、TCP，第8题"  
    notes: "ACK机制"



- question: "TCP流量控制主要依赖哪个字段？"  
  options:  
  A: "序列号"  
  B: "确认号"  
  C: "窗口大小"  
  D: "校验和"  
  expected_points:
  
  - "正确答案：C"
  
  - "接收窗口控制发送速率"  
    answerable_from_material: true  
    source_material: "四、TCP，第9题"  
    notes: "滑动窗口"



- question: "TCP校验和的作用是："  
  options:  
  A: "加密数据"  
  B: "检测数据错误"  
  C: "控制流量"  
  D: "路由选择"  
  expected_points:
  
  - "正确答案：B"
  
  - "差错检测"  
    answerable_from_material: true  
    source_material: "四、TCP，第10题"  
    notes: "可靠性机制"



- question: "HTTP协议是基于哪种传输协议？"  
  options:  
  A: "UDP"  
  B: "TCP"  
  C: "IP"  
  D: "ICMP"  
  expected_points:
  
  - "正确答案：B"
  
  - "HTTP基于TCP"  
    answerable_from_material: true  
    source_material: "三、HTTP，第7题"  
    notes: "可靠传输"



- question: "HTTP/1.1默认是否支持长连接？"  
  options:  
  A: "不支持"  
  B: "支持"  
  C: "部分支持"  
  D: "仅HTTPS支持"  
  expected_points:
  
  - "正确答案：B"
  
  - "默认keep-alive"  
    answerable_from_material: true  
    source_material: "三、HTTP，第8题"  
    notes: "减少连接开销"



- question: "DNS查询过程中，客户端首先查询的是："  
  options:  
  A: "根服务器"  
  B: "本地DNS服务器"  
  C: "权威服务器"  
  D: "HTTP服务器"  
  expected_points:
  
  - "正确答案：B"
  
  - "先查本地缓存"  
    answerable_from_material: true  
    source_material: "三、DNS，第4题"  
    notes: "递归查询"



- question: "IP协议是："  
  options:  
  A: "面向连接"  
  B: "无连接"  
  C: "可靠"  
  D: "有序"  
  expected_points:
  
  - "正确答案：B"
  
  - "无连接、不可靠"  
    answerable_from_material: true  
    source_material: "二、网络层，第12题"  
    notes: "基础特性"



- question: "路由器主要工作在OSI模型的哪一层？"  
  options:  
  A: "数据链路层"  
  B: "网络层"  
  C: "传输层"  
  D: "应用层"  
  expected_points:
  
  - "正确答案：B"
  
  - "负责路由转发"  
    answerable_from_material: true  
    source_material: "二、网络层，第13题"  
    notes: "核心设备"



- question: "交换机主要工作在OSI模型的哪一层？"  
  options:  
  A: "物理层"  
  B: "数据链路层"  
  C: "网络层"  
  D: "传输层"  
  expected_points:
  
  - "正确答案：B"
  
  - "基于MAC地址转发"  
    answerable_from_material: true  
    source_material: "一、设备，第1题"  
    notes: "二层设备"



- question: "IP分片的主要原因是："  
  options:  
  A: "提高速度"  
  B: "适应不同MTU"  
  C: "加密数据"  
  D: "减少延迟"  
  expected_points:
  
  - "正确答案：B"
  
  - "链路MTU限制"  
    answerable_from_material: true  
    source_material: "二、网络层，第14题"  
    notes: "分片机制"



- question: "TCP重传机制触发的常见原因是："  
  options:  
  A: "ACK超时"  
  B: "窗口变大"  
  C: "连接建立"  
  D: "数据加密"  
  expected_points:
  
  - "正确答案：A"
  
  - "未收到确认"  
    answerable_from_material: true  
    source_material: "四、TCP，第11题"  
    notes: "超时重传"



- question: "快速重传机制依赖于："  
  options:  
  A: "超时"  
  B: "重复ACK"  
  C: "窗口大小"  
  D: "IP地址"  
  expected_points:
  
  - "正确答案：B"
  
  - "收到多个重复ACK"  
    answerable_from_material: true  
    source_material: "四、TCP，第12题"  
    notes: "提高效率"



- question: "HTTP是无状态协议意味着："  
  options:  
  A: "无法通信"  
  B: "每次请求独立"  
  C: "必须加密"  
  D: "不能缓存"  
  expected_points:
  
  - "正确答案：B"
  
  - "不保存会话信息"  
    answerable_from_material: true  
    source_material: "三、HTTP，第9题"  
    notes: "需要Cookie补充"



- question: "Cookie的主要作用是："  
  options:  
  A: "加密数据"  
  B: "保持会话状态"  
  C: "提高速度"  
  D: "压缩数据"  
  expected_points:
  
  - "正确答案：B"
  
  - "记录用户信息"  
    answerable_from_material: true  
    source_material: "三、HTTP，第10题"  
    notes: "解决无状态问题"



- question: "端口号的主要作用是："  
  options:  
  A: "标识主机"  
  B: "标识进程"  
  C: "标识网络"  
  D: "标识链路"  
  expected_points:
  
  - "正确答案：B"
  
  - "区分不同应用"  
    answerable_from_material: true  
    source_material: "四、传输层，第13题"  
    notes: "进程通信"



- question: "IP地址+端口号的组合称为："  
  options:  
  A: "MAC地址"  
  B: "套接字"  
  C: "子网"  
  D: "路由"  
  expected_points:
  
  - "正确答案：B"
  
  - "Socket"  
    answerable_from_material: true  
    source_material: "四、传输层，第14题"  
    notes: "唯一标识通信端点"



- question: "浏览器缓存属于HTTP机制中的："  
  options:  
  A: "安全机制"  
  B: "性能优化"  
  C: "连接管理"  
  D: "路由机制"  
  expected_points:
  
  - "正确答案：B"
  
  - "减少请求次数"  
    answerable_from_material: true  
    source_material: "三、HTTP，第11题"  
    notes: "提高加载速度"



- question: "CDN的核心作用是："  
  options:  
  A: "加密数据"  
  B: "分布式缓存加速访问"  
  C: "路由控制"  
  D: "域名解析"  
  expected_points:
  
  - "正确答案：B"
  
  - "就近访问资源"  
    answerable_from_material: true  
    source_material: "综合，第2题"  
    notes: "性能优化关键技术"


