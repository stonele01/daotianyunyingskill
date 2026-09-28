# 稻田运营技能

一个供 Agent 使用的中文运营 Skill，面向快手为主、兼顾抖音的内容运营。员工从一个自然语言入口发起任务。

## 能做什么

- 按产品搜索、核对同款参考视频
- 拆解视频画面、字幕、口播、音乐/音效及时间关系
- 生成差异化脚本、分镜并审核事实和内容风险
- 分析授权提供的 Excel/CSV 运营数据，并把结果交接给下一轮选题
- 用 dbskill 方法做内容整理和按需经营诊断
- 按需分析抖音账号与评论，生成含时间点截图、口播证据和未核实事项的 HTML／ZIP 报告

这是方法、资料与有限辅助脚本的组合，不是快手官方服务，也不会自行登录快手后台或自动取得公司数据。实际执行依赖 Agent 宿主提供的浏览器、媒体和文件处理能力。

## 安装/导入

**给你的 Agent 发送项目地址即可安装。**

```text
请帮我安装稻田运营技能：https://github.com/stonele01/daotianyunyingskill
```

项目地址：https://github.com/stonele01/daotianyunyingskill 。下载或更新后查看 SKILL.md 的版本号，带本次账号洞察集成的版本应为 **1.1.0**。本仓库已同步 1.1.0；可从 Code → Download ZIP 获取完整技能。

支持 Skill 不等于所有能力已配置。搜索需要可用的网页／浏览器工具，声画理解需要媒体和音频能力，报表分析需要文件与计算能力。不同 Agent 的安装方式和运行权限分别核对。

1.1.0 已内置抖音洞察的脚本、模板与本地图片处理，无需员工再安装或调用一个独立洞察技能。Node.js、Python、FFmpeg、ASR 和数据服务仍按所用功能准备，不随包分发。配置步骤见 [账号洞察与证据报告](references/account-insight.md)。升级时保留本地配置和业务资料，不把 .env、模型、虚拟环境或报告目录混入分发包。

## 使用示例

```text
分析这份快手素材报表。先检查字段含义、重复和缺失，再按产品和素材比较消耗与成交表现。附计算依据，标出数据不足；指标口径不明确时先问我。
```

## 来源和许可

本项目组合了多个独立授权的第三方组件。**各目录按其自带许可和来源说明分别管理，不存在一个覆盖全仓库的统一开源许可。** 使用或再分发前阅读：

- `THIRD-PARTY-NOTICES.md`
- `SOURCE-MANIFEST.json`
- `upstream/dbskill/LICENSE`（CC BY-NC 4.0；商业用途需取得许可）
- `upstream/anthropic-data/LICENSE`（Apache-2.0）
- `upstream/hypit/LICENSE`（修改版 Apache-2.0，含附加条件）
- web-access 来源的许可说明（当前打包版本有 MIT 元信息声明；完整许可文本仍待补核）

请勿把本 README 或根目录新增文件理解成把整个包重新许可为 MIT、Apache 或其他单一许可。版本记录和组件改动见 `references/components.md`。

## 版本

当前整理版本：1.1.0（2026-09-28）。

本次新增抖音账号洞察与报告组件，接入画面证据、点击放大、证据与未查项、仅校验实际使用封面、图片本地化及中文错误提示。取帧、合并、模板和发布使用今天已改好的组件代码，未另造一套报告系统。

已有组件的合成样例与浏览器回归通过记录，不等于本次组合在真实账号、付费接口或所有 Agent 中已实测通过。总技能的版本和组件来源见 references/components.md 与 SOURCE-MANIFEST.json。

## 员工使用手册

[在线阅读操作手册](https://stonele01.github.io/daotianyunyingskill/)

[下载 Word 操作手册](docs/稻田运营总技能使用手册-1.1.0.docx)

[下载当前完整技能 ZIP](https://github.com/stonele01/daotianyunyingskill/archive/refs/heads/main.zip)
