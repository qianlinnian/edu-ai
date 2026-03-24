from workers.celery_app import celery_app


@celery_app.task(name="workers.embedding_task.process_resource")
def process_resource(resource_id: int):
    """异步处理课程资料：解析 -> 分块 -> 向量化 -> 存储"""
    # TODO: 实现文档处理pipeline
    # 1. 从MinIO下载文件
    # 2. 根据文件类型解析(PDF/Word/PPT/Markdown)
    # 3. 文本分块(按段落/固定长度，overlap)
    # 4. 调用Embedding API生成向量
    # 5. 存入resource_chunks表(含向量)
    # 6. 更新course_resources.is_processed = True
    print(f"[Embedding] 处理资料 resource_id={resource_id}")
    return {"resource_id": resource_id, "status": "processed"}
