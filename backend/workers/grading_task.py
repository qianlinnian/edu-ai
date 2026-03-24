from workers.celery_app import celery_app


@celery_app.task(name="workers.grading_task.grade_submission")
def grade_submission(submission_id: int):
    """异步批改作业任务"""
    # TODO: 实现批改逻辑
    # 1. 从数据库获取submission
    # 2. 根据作业类型(text/code/image)调用对应批改引擎
    # 3. 生成批注和评分
    # 4. 更新submission状态和grading_result
    # 5. 更新学生知识点掌握度
    print(f"[Grading] 开始批改 submission_id={submission_id}")
    return {"submission_id": submission_id, "status": "graded"}


@celery_app.task(name="workers.grading_task.batch_grade")
def batch_grade(assignment_id: int):
    """批量批改某作业的所有提交"""
    # TODO: 查询所有待批改提交，逐个调用grade_submission
    print(f"[Grading] 批量批改 assignment_id={assignment_id}")
    return {"assignment_id": assignment_id, "status": "completed"}
