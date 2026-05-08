这两个提交分别补充了后端 B 在 M2/M3 阶段的资源管理能力和文档材料。

f085ca8 主要是代码提交，补齐课程资料的删除、重试和清理脚本，使资源处理失败后可以重新派发任务，也方便演示前清理课程资料。

2e87415 主要是文档提交，整理了后端 B 的工作日志、周报、M3 后端任务拆解和汇报材料草稿。其中 pyc 文件属于误提交产物，后续建议清理。


f085ca8
feat: 补齐课程资源删除、重试与清理脚本

本次提交主要补齐 M2 课程资源管理的稳定性能力。

1. 在课程资源接口中新增资源删除能力：
   - 新增 DELETE /api/v1/courses/{course_id}/resources/{resource_id}
   - 删除资源时先清理 resource_chunks，再删除 course_resources
   - 同时尝试删除 MinIO 中对应的原始文件，MinIO 删除采用 best-effort，不影响数据库删除结果

2. 新增资源处理重试能力：
   - 新增 POST /api/v1/courses/{course_id}/resources/{resource_id}/retry
   - 对失败或已结束的资源，可清空旧 chunk，重置 processing_status、processing_error、chunk_count、is_processed
   - 重新派发 Celery process_resource 任务，避免必须重新上传文件

3. 扩展 MinIO 存储工具：
   - 在 backend/core/storage.py 中新增 remove_object()
   - 用于统一删除 MinIO 对象

4. 新增课程资源清理脚本：
   - 新增 backend/script/clear_course_resources.py
   - 支持按 course_id 清理课程资源和 resource_chunks
   - 支持 --dry-run 预览删除内容
   - 支持 --delete-minio 同步尝试清理 MinIO 文件

整体作用：
- 让课程资料管理具备“可删除、可重试、可清理”的能力
- 方便 M2 演示和联调时重置课程资源状态
- 降低资源处理失败后只能手动清数据库的成本

2e87415
docs: 补充后端B阶段文档和 M3 任务说明

本次提交主要是文档和阶段材料整理。

1. 新增后端 B 工作日志：
   - docs/codex-work-loglqy.md
   - 记录本阶段协作过程、环境准备、Docker 启动、后端联调和周报生成过程

2. 新增后端周报：
   - docs/weekly-report-2026-04-20-2026-04-26-lqy.md
   - 总结后端 B 在练习评判、掌握度更新、学情分析、预警生成、接口接入和分支同步方面的工作

3. 新增 M3 后端 B 任务说明：
   - m3-backend-b-tasks.md
   - 明确 M3 阶段后端 B 的任务边界：
     - 作业提交后的批改任务落库
     - grading_results / submission_annotations 写入
     - student_knowledge_mastery 更新
     - learning_alerts 薄弱点预警生成
     - analytics / exercises 接口联动验证

4. 新增汇报材料草稿：
   - ppt_text.md
   - ppt_text_en.md
   - ppt_text_gbk.md
   - rbs-wbs-schedule-diagrams(1).md

注意：
- 该提交中包含 results/pyc_check/storage.pyc.2682853858224，这是编译产物/检查产物，不建议长期保留在仓库中。
- 后续如果整理仓库，可以单独提交一次删除该 pyc 文件。
