# 任务交接约定

简单问题直接回答；多阶段工作建立一个任务目录。目录名只用于可读性，task_id 为稳定 ID。路径使用相对任务根的写法，交给用户时转换成宿主可打开的链接。

## 目录按需要生成

```text
任务目录/
  task.json
  brief.md
  progress.md
  sources/                 原始清单和只读资料引用
  discovery/               candidates.csv、selection.md
  videos/<candidate_id>/   analysis.md、timeline.csv、transcript、evidence/
  production/              scripts.md、storyboards.csv、review.md、shooting-brief.md
  analysis/                field-map.csv、summary.csv/xlsx、report.md、calculation.py/公式、validation.md、按需 next-round.md
  diagnosis/               按需生成的 db 内容或经营诊断
  archive/                 index.csv、案例卡
```

不复制无权保存的原片；允许时可存原片或只引用用户原文件。公司资料不进入技能包和分发压缩包。

## 状态和 ID

task.json 至少包含 task_id、request、platforms、product、created_at、updated_at、inputs、outputs、stages、open_questions。每个阶段状态为 not_requested／pending／in_progress／complete／blocked／skipped_by_user，只有有对应产物且已检查才可标 complete。完成搜索不自动把下载、转写或视觉检查标完成。

用户明确跳过的阶段记 skipped_by_user，并在 scope_decision 中保留原要求、变更和影响；没有做过的检查仍是未核验。仅当本次请求中其余必要阶段均已完成，才把任务 status 标 complete。某次视频拆解完成不自动把技能包全部能力标为已实测。恢复时不重复追问已经跳过的声音、搜索或创作环节。

每条候选 candidate_id 贯穿原链接、视频、证据；每条脚本 script_id＋version 贯穿分镜、审核、后续投放映射。用户素材 ID 和账号 ID 原样保留字符串。

brief.md 固定用户需求、商品事实及证据、受众、品牌要求、时长、资源、授权边界和声明的假设。progress.md 只记当前实际进度、未解决问题、下一步；恢复时不重做有证据的已完成步骤。

## 证据与交接

证据编号关联 source_url／source_file、源时间或作品 ID、观察日期、原始摘录、证据类型、结论。表格证据另关联工作表、业务键/原始行、统计范围和计算代码/公式；输出汇总能追溯到输入和筛选条件。脚本引用已确认商品事实和可借鉴结构，不能复制参考品牌事实到自家。

拍摄任务单区分：确认可拍、需补证、需补素材；不得在未确认时称“可直接发布”。审核表标实际覆盖的文本／画面／声音范围。

内容诊断和案例结论关联脚本版本与已提供证据，不能匹配的单列，不凭记忆合并。记录本次人工输入准备、AI 墙钟耗时、调用费用（未知就未知）、审核和返工时间；没有基线不计算节省比例。
