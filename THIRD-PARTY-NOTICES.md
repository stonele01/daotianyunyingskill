# 来源、许可与部署事项

整理日期：2026-09-28。包名 daotianyunyingskill，版本 1.1.0；该名称不代表原作者或平台官方产品。制作本地技能包没有完成账号授权、服务订购或真实业务验收。

## dbskill

- 作者：dontbesilent；仓库 https://github.com/dontbesilent2025/dbskill
- 固定提交：3ec74054d7e049642a77ff86e0bdea8786c444dc
- 原许可：[CC BY-NC 4.0 原许可文件](upstream/dbskill/LICENSE)，许可链接 https://creativecommons.org/licenses/by-nc/4.0/
- 选中的 12 个模块及其目录支持文件保留原文，SKILL.md 仅重命名为 SOURCE.md；本包新增适配层见 references/components.md。
- 公司内部经营使用不能仅因“不对外卖技能”就自动视为非商业使用。公司使用／改编授权尚待用户提供或向作者确认；不将整个组合包重新标成 MIT 或无限制商业许可。

## web-access

- 作者：一泽 Eze；仓库 https://github.com/eze-is/web-access
- 固定提交：33eef84a55b1919396a80e7a55650a07bb83f590
- 原 SOURCE.md 元信息声明 MIT；该固定版本未找到独立完整 LICENSE 文件。保留原声明与来源，分发／公司部署前补核完整授权文本，不替作者补造许可原文。
- 打包了方法、scripts、references 和配置模板；没有个人配置、浏览器资料、Cookie 或密钥。

## Hypit

- 作者：Hypit.AI；仓库 https://github.com/hypit-ai/hypit
- 固定提交：8a3af4fbac9c8291725d91040337950905baad6a
- [原许可](upstream/hypit/LICENSE)：修改版 Apache 2.0，明确允许本组织内部及商业工作；对外多租户服务、商业再分发等有额外条件，保留原署名与许可。
- 本包仅保留视频理解和本地工具资料，并编写有限命令适配；CLI 本体、模型、Studio、编辑器和渲染系统未包含。
- 原始 Hypit 文档链接涉及未打包的生成／渲染材料时，仅为原文上下文，不属于本包运行依赖；运行以 references/tools.md 中明确列出的能力为准。

## Anthropic Data Analyst

- 作者：Anthropic；仓库 https://github.com/anthropics/knowledge-work-plugins
- 固定提交：da38ec1ee89d41e5380e652a97382695003396e7，来源为 data 子目录。
- [原许可](upstream/anthropic-data/LICENSE)：Apache License 2.0；保留全部原始许可与署名。该许可不改变本包其他组件的许可。
- 保留 analyze、explore-data、validate-data、statistical-analysis、data-visualization 五份方法及 CONNECTORS.md；原 SKILL.md 仅更名 SOURCE.md，内容不改。自有适配文件为 references/data-analysis.md，修改与映射记录见 references/components.md。
- 不包含 Anthropic xlsx 专有材料、数据库连接配置和完整 Claude 插件安装器；也不表示已购买或连接 Anthropic 服务。

## 抖音账号洞察与报告组件

- 原项目：https://github.com/whwhw/douyin-comment-insight-free 。本包使用 2026-09-28 的本地改造副本，未确认它对应上游哪个提交，不将其标成原版最新发布。
- 组件根许可为 MIT，原版权文字保存在 components/douyin-insight/LICENSE。本地改造包含画面证据 schema、取帧与合并脚本、模板渲染、离线资源、图片准备及实际渲染范围校验。
- 模板所带第三方前端库按各自许可管理：Lucide 许可、GSAP 声明和来源见组件 assets/vendor。MIT 不替换 GSAP 的独立条款，也不改变本包其他组件授权。
- 完整文件来源与 SHA-256 见 SOURCE-MANIFEST.json。本包不附凭据、登录状态、付费额度、原始账号材料或个人运行环境。

## 运行依赖与业务数据

Python、FFmpeg、Pillow、宿主 Agent／模型、浏览器和付费数据／ASR 服务按各自许可与条款使用。本包不附它们的二进制或模型。第三方模型费用、API 费用与订阅费用分别计算；没有实际调用不编造费用。

参考视频、商品资料、账号和后台数据的取得／处理权限由实际业务授权确定，代码公开不代表数据可自由使用。分发包不得含真实业务素材和任何凭证。

## 尚待确认的部署事项（集中维护）

1. dbskill 公司内部业务使用和改编的许可范围。
2. web-access 完整许可文本及目标宿主允许的浏览器接入方式。
3. 若选付费取数／转写：服务支持平台、数据处理范围、价格、账号与调用授权。
4. 真实公司产品／视频的小样试用，以及指定 Agent 中的实际发现与调用；它们属于部署后的验证事项，不扩大制作交付范围。
