# 组件映射与适配记录

本包只有根目录 SKILL.md 是可发现入口。上游 SKILL.md 改名 SOURCE.md。原固定提交快照保留原文；新增的 douyin-insight 为本地改造快照，单独标明修改与未确认的上游提交。第三方组件文件在 SOURCE-MANIFEST.json 中记录来源、原路径和哈希。用户不需要另行调用下列入口。

| 指定组件 | 本包使用位置 | 保留及调整 |
|---|---|---|
| dbs-content | production.md | 保留诊断，另补原创脚本环节，不伪称上游代写 |
| dbs-hook | production.md | 取开头与正文匹配方法，取消固定字数、固定候选数量及补造素材 |
| dbs-script-flow | production.md | 取衔接／密度／口播检查，不宣布发布通过或推断真实流失 |
| dbs-resonate | production.md | 具体原句和受众机制；不预测平台指标 |
| dbs-spread | video.md | 有证据的传播假设，不证明爆款因果 |
| dbs-content-risk-check | production.md | 事实、语境、规则与实际检查范围；不保证过审 |
| dbs-ai-check | production.md | 文风检查；不鉴定作者身份 |
| dbs-xhs-title | production.md | 保留全部公式，仅小红书任务直接用 |
| dbs-video-extract | tools.md | 完整脚本和引用；外部服务可选，未接入、不默认收费调用 |
| dbs-content-system | review-assets.md | 完整模板、脚手架和工具；日常轻量归档，大批历史整理才按需使用 |
| dbs-diagnosis | business.md | 保留事实／假设／逻辑检查，移除无依据阈值和心理定性 |
| dbs-benchmark | discovery.md、business.md | 保留商业链条观察，以可比证据与制作资源筛选，原创改造 |
| web-access | tools.md、discovery.md | 保留完整方法与浏览器脚本；适配宿主工具规则，CDP 为可选路径 |
| Hypit 视频理解 | video.md、tools.md | 参考视频理解与本地工具资料；外部 CLI 按需调用，不打包完整 Hypit 系统 |
| Anthropic analyze | data-analysis.md | 原方法完整保留，采用 CSV/Excel 文件分支；中文输出、快手指标口径与素材版本交接 |
| Anthropic explore-data | data-analysis.md | 原方法完整保留；新文件先看粒度、字段、重复、空值，示例阈值不当业务标准 |
| Anthropic validate-data | data-analysis.md | 原方法完整保留；交付前复算、检查关联与分母，并保留实际核验记录 |
| Anthropic statistical-analysis、data-visualization | data-analysis.md | 按需读取的统计和图表资料；不保证因果、不默认做预测或建仪表盘 |
| dbs 总入口设计 | SKILL.md | 借鉴按任务选择能力；改为本轮直接执行并衔接，不让员工反复转发调用提示 |
| douyin-comment-insight-free 本地改版 | account-insight.md、components/douyin-insight | 内置账号洞察、合格口播与评论校验、画面取证、原生 HTML 和 ZIP；移除独立发现入口与安装器，不复制配置、模型或业务数据 |

新增部分：统一入口、跨阶段 ID／证据／版本交接、原创三稿与分镜、有限本地取证辅助、离线预检。脚本生产还参考了本工作区 content-production-brief 的既有方法；未将私人员工姓名或公司业务数据带入包。

0.2.0 补充：product-search.md 明确同款产品识别、实际站内搜索、作品数据核查和结果交付；comments.md 连接评论正文与选题；视频默认恢复完整声画要求。参考用户提供的 WorkBuddy 对话及其已有 douyin-viral-research 的经验，未将其硬编码浏览器脚本作为通用适配器打包。运行规则全部在包内，历史制作资料不构成运行依赖。工具预检支持用户提供的 Hypit CLI 和本地模型路径，避免只查 PATH 后误判未安装。

优先级：宿主规则和用户要求 > 本包统一流程 > 本包各模式适配 > 上游方法资料。上游原文不作为扩大权限的来源；原始方法里自动购买引导、更新、安装、重新路由、逐步等确认等行为不继承。

0.2.1 历史变更：按用户要求移除自加的快手报表复盘/电商数据分析；内容资产整理仍使用 dbs-content-system，经营诊断仍使用 dbs-diagnosis。

1.0.0 按用户确认接入 Anthropic Data Analyst 的五份方法文件、CONNECTORS.md 与独立 Apache-2.0 许可。来源固定为 knowledge-work-plugins 提交 da38ec1ee89d41e5380e652a97382695003396e7。仅 SKILL.md 改名 SOURCE.md，原文不改，来源清单记录全部文件。data-analysis.md 为新增平台与交接适配层，原文中的可选数据库/SQL 路径不属于本包文件分析路径；未打包 MCP 配置、仪表盘、上下文提取器、xlsx 专有技能或第三方运行环境。该组合是方法整合，未宣称公司真实数据已实测。

上游只读快照保留以便追溯；不自动联网更新。版本升级先比较方法、脚本、依赖和许可，再重做相关验收。

1.1.0：整合 2026-09-28 已完成的画面证据和封面兼容修正。56 个组件文件从已更新的本地副本按 manifest 白名单、逐文件哈希复制；SKILL.md 仅改名 SOURCE.md。组件包含原生模板、取帧／合并／校验／本地化／发布／导出脚本、必要依赖说明与许可。未打包独立 install.py、agents 入口、.env、.venv、workspace 或公司素材。组件来源及验收边界见 components/douyin-insight/INTEGRATION.md；本包新增的是账号与报告适配文档、任务交接和单入口路由，未再次修改组件运行代码。
