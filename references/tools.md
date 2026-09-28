# 工具接入与降级路径

先检查宿主实际提供的工具。一次只准备本次任务需要的能力，不安装整套软件来做一个局部任务。可运行 `python <技能目录>/scripts/preflight.py` 查看本地可执行文件是否可见；这不检查登录、不读取凭证、不启动服务，也不代表业务已跑通。

## 1. 网页：接入 web-access 的获取方法

读 [web-access 原文](../upstream/web-access/SOURCE.md)，复用“先明确目标、观察页面结构、按结果调整路径、核对真实内容”的方法。

宿主已有搜索、网页读取、浏览器工具时直接使用该受支持工具。遵守该工具的操作规则，不通过额外 CDP、网络请求或读取浏览器文件绕过限制。静态资料不必启动浏览器。需要动态页面或登录态时使用可用浏览器；连接成功仍需验证目标作品和指标实际出现。

宿主没有可用浏览器工具、且允许直接连接 CDP 时，可选包内 web-access：

1. Node.js 22+、Chrome／Edge 和浏览器远程调试权限是实际依赖。先检查，无可用环境时给出缺项，不自行安装／修改浏览器设置。
2. `check-deps.mjs` 会写 config.env、启动代理并可能需要用户确认连接，**它不是纯只读预检**。已获对应授权后才能执行：
   `node <技能目录>/upstream/web-access/scripts/check-deps.mjs --browser edge`
3. 检查成功后读 [CDP API](../upstream/web-access/references/cdp-api.md) 和 [迁移说明](../upstream/web-access/references/migration-2.5.3.md)，使用实际返回的 target。新建任务标签页；只关闭自己创建的页。
4. 源文 `${CLAUDE_SKILL_DIR}` 在本包指向 `upstream/web-access`，不能指向整个技能根。代理端口以本次实际配置为准，不把另一个未知本地服务当成代理。
5. 导航成功不等于取得内容。遇登录、验证或加载页按真实状态处理；不循环重试相同失败路径。不绕过验证码／付费墙，不调用浏览历史查找脚本来补普通产品搜索。

原文中“所有联网必须经过此技能”“继续即接受风险”“自动查历史”“鼓励多 Agent”不作为本包规则。权限由用户和宿主决定，本包不要求多 Agent。Jina 属于可选第三方服务，公司私密 URL 不交给它。

## 2. 视频：优先现有 Hypit 局部能力

本包包含 Hypit 视频理解方法，**没有打包 Hypit CLI 本体**。已有 CLI 时先读 `hypit media --help`，核对版本支持的选项。无需为了本地 probe／frames／tiles 引入 Studio、生成和渲染。

PATH 找不到 hypit 只说明当前命令不可见。用户或既有项目给出准确安装位置时，先检查该处的 package.json 和 CLI 入口；可运行 `python <技能目录>/scripts/preflight.py --hypit-entry <已知的hypit.mjs路径>`，存在后用 `node <该入口> help media` 核对本地媒体命令。不要扫描整盘或读取秘密配置。后续示例中的 hypit 均可替换为这一显式调用方式，不能因此认定所有服务已准备好。

源码确认的命令示例，路径替换为实际文件及新输出目录：

```text
hypit media probe source.mp4
hypit media frames source.mp4 --at 0,3,6 --label-time --to evidence/keyframes
hypit media tile source.mp4 --start 0 --end 12 --every 1 --columns 4 --cell 480 --to evidence/overview.jpg
hypit media tiles source.mp4 --start 6.8 --end 8.4 --every-frame --columns 4 --rows 3 --cell 480 --to evidence/detail
hypit media cut source.mp4 --start 6.8 --end 8.4 --label-time --to evidence/detail.mp4
```

窗口必须在实际时长内，输出不能覆盖已有证据。变帧率密集检查使用 every-frame 和实际源时间。粗略 boundaries 只找待检查变化，不直接当最终镜头切点。

已核查的 Hypit 0.2.12 中，media cut 按输入流保留视频/音频；把 MP4 输入的输出名改为 WAV 不会自动变成音轨提取，可能报 WAV 不支持视频流。需要独立音频时先用已有音轨，或本包 media_evidence.py --audio 提取；随后对该音频文件使用 media cut 输出 WAV。失败可能留下不完整文件，记录为失败，后续使用新输出路径，不能把文件存在当成功。

`hypit media fetch <已支持且有权获取的URL> --to source.mp4` 是独立网络下载能力；其 yt-dlp 环境可能未准备，不承诺支持所有快手分享链接。安装、下载运行环境需要相应授权。

`hypit transcribe source.mp4 --language zh --to transcript.json` 依赖已选择并可用的转写服务。可能是本地 WhisperX，也可能上传到付费服务；执行前确认实际服务和既有授权，不靠读取秘密配置判断。原环境说明在 [local-tools](../upstream/hypit/skills/hypit/references/environment/local-tools.md)，其中安装命令仅供管理员准备，不自动执行。

本地 probe、frames、tile、boundaries、cut 的独立运行能力与 transcribe、联网 fetch 分开记录。`help media` 的本地说明不能推广为所有命令零网络、零准备。用户要求声音分析时，应完成语音及听音证据链；不要为了避开依赖只交抽帧图。

## 3. 没有 Hypit：本地证据辅助

用户不想安装整个 Hypit 时，本包 `scripts/media_evidence.py` 用已有 Python 3.11+、ffmpeg、ffprobe 做元数据、保留实际时间的原分辨率抽帧和可选音轨提取。它是有限降级能力，不冒充 Hypit，不含识字、语音识别、联网下载或视频生成。

```text
python <技能目录>/scripts/media_evidence.py source.mp4 --out evidence/overview --every 2
python <技能目录>/scripts/media_evidence.py source.mp4 --out evidence/detail --start 6.8 --end 8.4 --every-frame --max-frames 120
python <技能目录>/scripts/media_evidence.py source.mp4 --out evidence/audio-view --every 3 --audio
```

时间窗口为左闭右开 `[start, end)`。输出 probe.json、manifest.json、带源时间文件名的 PNG；如果 Pillow 已有则另输出带时间标签图和分页总览，原图始终保留。抽帧达到上限时标可能截断，不能宣称覆盖全段；用缩小窗口补查。Pillow 未安装不自动安装，按文件名和 manifest 定位原帧。音轨输出只负责保存，不负责听懂。

宿主能看视频／听音则使用实际提供的能力；只有看图能力就按证据范围分析，缺语音转写可接用户已有字幕或获准服务。三者都不可用时说明具体缺项，请提供可读材料。

预检中的 Python 模块结果只针对当前解释器；另一已知 Python 环境可能已有 ASR。只检查明确的解释器和模型目录，不扫描凭证或整盘资料。本包还提供 `scripts/transcribe_local.py`：在已有 faster-whisper 的解释器中运行，显式传入已缓存模型目录，全程 offline，不安装、不下载模型、不调用外部 API：

```text
<已有ASR的Python> <技能目录>/scripts/transcribe_local.py audio.wav --model-dir <已有模型快照目录> --out asr-raw.json --language zh
```

可用 `--vad` 作一次有针对性的复核。输出永远是待核对的机器转写，不能以进程成功替代听音／逐词确认；按 video.md 的非空结果核验规则处理。原始记录包含模型和时间设置，业务报告只采用已核实文字。

缓存目录存在不代表模型完整。可先用 `preflight.py --asr-model-dir <已知模型目录>` 核对必要文件；该检查不载入模型，也不保证文件格式兼容。失败时保留具体缺项，不自动下载；同一不可用路径不要无变化地重试。

## 4. dbs-video-extract：可选外部数据／转写

读 [原组件](../upstream/dbskill/dbs-video-extract/SOURCE.md)。包内保留 references 和四个脚本，不默认执行其凭证预检或引导充值。只有用户已选择并授权 TikHub／轻抖、已安全配置、确认本次可花费和数据可发送时，才读取相关 API 文档和脚本并按其 CLI 使用。

TikHub 的本组件结构化数据范围明确列抖音、小红书、视频号，快手必须另核服务支持。轻抖是否接受具体快手链接以当前服务结果为准。只取得文字稿就交付文字稿，不能标视觉分析完成。不得把 API Key 放入聊天、产物、命令行或压缩包。

## 5. 数据分析与文字工作

Data Analyst 通过宿主实际可用的文件读取与代码执行工具运行，默认处理用户提供的文件。已有 pandas 用于 CSV/Excel 计算，openpyxl 用于 xlsx 读写；图表可用已有 matplotlib/plotly 等。先核对实际解释器与依赖，不因上游写“上传文件”就上传到第三方；不自动安装库。缺 Excel 读取能力时可请用户导出 CSV，缺计算能力时明确本次范围。宿主有适用的表格技能时遵循其文件处理规则，本包负责业务口径与分析方法。

不包含 Anthropic xlsx 专有技能，不打包完整 data 插件的 MCP 配置，不自动连接数据库、BI 或快手后台。上游代码示例需要根据当前字段生成实际计算，不能将示例结果当作用户数据。

搜索候选、分镜和审核也可以保存为表格；文字创作和 dbskill 诊断由宿主模型执行，效果受模型与输入资料影响，不是离线脚本自动保证。

所有可选依赖分别记录“可见／已配置／本次调用成功／业务验收通过”，不要混为一个就绪状态。
