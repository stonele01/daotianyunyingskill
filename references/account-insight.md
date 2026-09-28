# 抖音账号洞察与画面证据报告

适用于抖音对标账号、评论需求、完整口播拆解、金句和带截图的账号报告。由稻田运营总入口完成，不让员工重新调用另一技能。组件根目录为 `<总技能目录>/components/douyin-insight`，以下脚本路径均以此为根。快手找参考和报表分析仍走原流程，不能用抖音接口或指标代替。

## 按已有材料选择路径

- 只有产品：先用 discovery.md 找同款作品；不把该组件当成全网产品搜索工具。
- 有抖音号或主页：核对账号身份；需要账号报告时使用组件采集、转写与分析流程。
- 已有视频：直接按 video.md 分析声音、字幕和画面；需要报告用图时可直接用 prep_frames.mjs，不为取帧再采集账号。
- 已有采集、转写或已校验 analysis.json：复用材料，补缺项。查看历史不重新采集，已有报告只读，不因升级自动重建。
- 已有快手数据或本地无账号视频：可以使用取帧能力并交付原 analysis.md／timeline.csv；当前 HTML 模板含抖音账号语义，不能捏造抖音身份、指标或链接来套用。完整 HTML 账号报告以抖音数据为范围。

## 运行准备与配置

先读 [组件流程](../components/douyin-insight/SOURCE.md)，仅在相应步骤读其 references。组件提供代码和模板，不包含 Python／Node.js／FFmpeg、ASR 模型、数据额度或登录状态。原版写 Codex 的语义分析职责，在本总技能中由当前具备所需能力的 Agent 承担；其他 Agent 的业务调用仍需各自验证。

采集与转写由用户已配置并授权的服务提供。组件默认云端转写，不能因为有此默认就自动上传公司视频或调用收费服务；沿用当前任务已有授权，否则先确认服务和数据范围。不要为了初始化执行独立技能安装器或输出密钥。优先复用已就绪的环境和已核验转写。

运行 workflow.py、transcribe_works.py 前，为本次子进程设置 `DOUYIN_INSIGHT_WORKSPACE=<任务绝对路径>/account-insight`。该设置优先于组件 .env，确保业务资料不落进安装目录。用宿主进程环境传值，不修改全局环境。服务凭据通过管理员配置的进程环境或组件自己的本地 .env 提供；不从其他技能偷读或复制凭据。发行包只有 .env.example。

首次在该组件使用采集／转写时参考 [配置说明](../components/douyin-insight/references/setup.md) 和 [云端转写说明](../components/douyin-insight/references/high-speed.md)。doctor 只检查配置与依赖，不能证明密钥有效、余额充足或业务已通过。已有独立技能的 .venv 可由管理员显式指定为解释器，但本包不依赖任何个人盘符。

## 账号分析与交接

1. 用 workflow.py inspect 检查本任务历史，沿用真实抖音号；昵称或主页无法唯一核验时才询问。
2. 需要新采集且已授权时 prepare；默认最多 30 条作品、每条最多 100 条实际返回评论，不能称全量。使用命令返回的 runDir、analysisInput 等路径，不自行猜测。浏览器或其他来源的数据不直接冒充该接口输出，先依 [schema](../components/douyin-insight/references/analysis-schema.md) 核对字段和 ID。
3. 转写复用同源完整证据。ASR 合格只说明机器完整性检查通过，重要文字仍核对；音乐、音效及音画关系继续遵循 video.md，不因拿到口播就宣告声音分析完成。
4. 按 schema 写 findings.json、work-findings.json，评论结论绑定原评论 ID，口播分段覆盖真实 ASR，不修改原始材料。仅 completed 且 transcriptComplete=true 的转写可进入 qualifiedWorkIds；失败项保留状态。
5. 执行 finalize_analysis.py 完成评论、口播、金句证据校验。没有合格口播仍可交付评论与视觉部分，但不伪造口播或合格状态。
6. 用户还要求脚本时，直接交给 production.md，输出总技能约定的三条差异稿。组件中的二创角度必须遵守其来源限制；若一条母作品不足以产生三个合法衍生，不强塞三个角度进报告。可基于自家已确认事实另写原创脚本，注明其依据，单独存入 production/。

账号与作品 ID 沿用实际来源。候选 candidate_id 与作品 awemeId 不同的，保存映射到任务 sources/；报告中的 referenceId 使用已核对的作品 ID。stage、产物、缺口和后续脚本版本回写总任务 progress.md/task.json，不能只生成报告就结束用户要求的完整任务。

## 带画面证据的报告

详细 schema、取帧和发布参数见 [画面证据流程](../components/douyin-insight/references/frame-evidence.md)。不要在发布后的 HTML 上打补丁。

1. 先总览，再按关键区间密集取帧。核对清晰原帧与实际源时间，选择代表帧；复用已有足够证据，不机械重复全片抽样。
2. 将 frames.json 的 frameEvidence 引用进 authored-works.json；同时填真实 evidenceNotes、uncertainties、verification。帧时间单位为秒，ASR 的 startMs/endMs 是毫秒。file 只能是文件名，图片放在 `site/assets/frames/<referenceId>/`。
3. build_report.mjs 以已校验分析为基底合并视觉字段，保留原分析和口播合格状态。新增／修改口播须再走 finalize_analysis.py，不能用合并器绕过证据校验。无口播作品允许视觉证据，不补造台词。
4. 报告实际用到的头像、封面须本地化。已有本地图就复用；获授权下载时使用 localize_assets.py --download，不联网时用 --offline 并明确占位。未渲染的远程封面无需全量下载。缺证据截图仍阻止发布，封面占位图不能冒充视频证据。
5. publish_report.py 显式传 --output-dir，export_report.py 显式传 --site 和 --output。脚本使用组件自带原生模板，报告可显示带时间的图集、放大查看、帧数、证据说明和未核事项。字段为空不生成空区块，图片错误给出中文说明。

命令中的 COMP 和 TASK 代表组件根目录与本次任务的绝对路径，执行时替换，不写死开发者目录：

```text
node COMP/scripts/prep_frames.mjs --video INPUT.mp4 --work-id WORK_ID --site TASK/site --evidence TASK/frame-review --every 1 --dense 2:4:0.25
node COMP/scripts/build_report.mjs --input VALIDATED.json --works AUTHORED.json --output TASK/visual-analysis.json
python COMP/scripts/localize_assets.py --data TASK/visual-analysis.json --output TASK/prepared.json --site TASK/site --offline
python COMP/scripts/publish_report.py --account ACCOUNT --data TASK/prepared.json --output-dir TASK/site
python COMP/scripts/export_report.py --account ACCOUNT --site TASK/site --output TASK/report.zip
```

密集区间仅为参数示例，须在真实视频时长内；代表帧选择按 frame-evidence.md 的 --select 流程完成。已有 prepared.json/site 时用新任务版本目录，不覆盖用户旧报告。

## 交付与失败处理

交付报告 HTML、完整 ZIP、分析摘要和真实覆盖范围；保留结构化分析和原证据在任务目录。ZIP 仅含当前账号必要资源，报告保留真实评论，分享前按业务范围确认。没有得到视频、声音、评论的部分分别标未完成，下载封面成功不能升级这些状态。

图片准备失败可使用明确占位继续；证据缺图、证据校验或 JS 语法失败先修正再发布。模板依赖不满足时交付已有 Markdown、CSV 和截图，明确 HTML 未完成。原生报告的技术验收记录见组件来源说明；接入完成不等于真实账号采集、付费转写或跨 Agent 全流程已实测。
