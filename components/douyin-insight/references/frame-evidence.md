# 画面证据拆解

适用于已取得本地视频、需要把经过核对的画面和证据带进账号报告的任务。取帧脚本只处理媒体，画面描述、字幕和分析由 Agent 核对后填写。不要从 ASR 空结果推断没有人声，也不要用画面字幕替代音频原文。

## 数据约定

`authored-works.json` 可以是以作品 ID 为键的对象，也可以是带 `referenceId` 的数组。每个作品新增以下可选字段；`scripts/build_report.mjs` 透传至 `analysis.json` 的 `workAnalyses`：

```json
{
  "example-work": {
    "frameEvidence": [
      {"t": 1.25, "file": "t1.25.jpg", "label": "产品出场", "caption": "示例画面描述，需回查原帧", "sub": "画面实际出现的字"}
    ],
    "evidenceNotes": [
      {"claim": "待说明的判断", "evidence": "1.25秒关键帧及其核对记录", "source": "模型观察 / 字幕核对"}
    ],
    "uncertainties": ["静帧不能确认完整运镜；需要回看片段"],
    "verification": {"asrModels": [], "frameChecks": "逐一核对清晰原帧、源时间与字幕"}
  }
}
```

- `t` 是相对视频起始帧的**秒数**；ASR 的 `startMs/endMs` 仍是毫秒，不能混用。
- `file` 只能是本地图片文件名，路径固定为 `site/assets/frames/<referenceId>/<file>`。禁止 URL、绝对路径、目录穿越。
- `label/caption` 必填；没有屏幕字幕时省略 `sub`。不填写猜测的“合理台词”。
- 四个字段都可省略。空数组/空 verification 不渲染空区块；有证据说明但没有帧图时，可以只出现说明块。
- 图片存在、字段合法只表示技术检查通过；语义、字幕准确度和听音证据仍须核对。

## 取帧与人工/模型标注

依赖现有 Node.js、FFmpeg/FFprobe；不安装工具、下载模型或调用外部 API。可用 `--ffmpeg`、`--ffprobe` 指定可执行文件。

先做总览和关键区间，输出目录必须是新目录：

```text
node scripts/prep_frames.mjs --video source.mp4 --work-id example-work --site task/site --evidence task/review-pass1 --every 1 --dense 2:4:0.25
```

`--dense 起点:终点:步长` 可重复；密集采样默认步长 0.25 秒，必须小于总览间隔。每 2 秒一帧是稀疏抽样，不是比 1 秒更密集。默认最多 600 帧，超限报错并要求缩小范围或放宽间隔，不静默截断。

查看 `contact-*.jpg` 后，回查 `raw-*.png`，将代表帧的实际时间和确认过的文字写入 `selected.json`：

```json
[{"t":1.25,"label":"产品出场","caption":"已核对的画面描述","sub":"已核对的屏幕字"}]
```

再次运行，使用新的证据目录并加入 `--select selected.json`。脚本保留全分辨率 PNG；报告 JPG 宽度不超过 880px（不放大小图），FFmpeg `q=3` 近似高质量而非严格的百分比 80。时间取实际解码帧，`frames.json` 同时记录请求时间与实际时间；变帧率也不能把请求时间当作真实帧时间。带时间文字的是供检查的缩略图，报告图片不遮盖原字幕。

将 `site/assets/frames/<workId>/frames.json` 中的 `frameEvidence` 原样引用进 authored 文件，避免手抄路径和时间；源视频、本地绝对路径及逐帧清单留在任务证据目录，不进入共享报告。

## 合并、校验和发布

```text
node scripts/build_report.mjs --input validated-analysis.json --common authored-common.json --works authored-works.json --output task/analysis.json
python scripts/publish_report.py --account example --data task/analysis.json --output-dir task/site
python scripts/export_report.py --account example --site task/site --output task/report.zip
```

`build_report.mjs` 是本次新增的通用合并器，与旧会话里写死 offrelax 路径的同名脚本不同。它保留其他作品和字段，不重算关键词，不生成虚假的 ASR 文件，也不升级口播合格状态。新增或修改口播结论仍走原 `finalize_analysis.py` 校验；已校验的 `analysis.json` 可作为纯画面扩展的输入。

发布会检查画面 schema、本地图片存在、路径安全及模板 JS 语法；语法失败时不写报告。Node.js 为此新增发布依赖，非默认 PATH 可用 `--node` 指定。

发布与导出不读取 `.env`，输出目录显式传参或从进程环境 `DOUYIN_INSIGHT_WORKSPACE` 读取。采集、转写的原配置方法不变。仅准备报告实际使用的头像和封面；未被界面引用的远程封面可留在原数据中，不阻止发布。对实际使用的远程图片，先运行下述 localize_assets.py，发布本身仍不联网。已有代码和业务数据分别保管。

原生模板支持点击帧图放大、Esc 关闭、键盘返回，首卡及其他作品卡均显示帧数。没有合格口播时只展示已有视觉证据，不借此把作品标为口播合格。发布始终从模板重建，不需要事后字符串补丁。

## 交付验收

- 离线打开新报告及索引，外部请求和控制台错误均为 0；已有作品/评论/拆解内容不丢失。
- 首卡和其他卡帧数正确；打开抽屉，两个新区块有真实内容，每张图片 `naturalWidth > 0`，放大和关闭可用。
- 无新字段或字段全空：不产生新区块、徽标或空标题，原有展示保持一致。
- 同一输入重复发布：数据、HTML 内容一致，区块不叠加；重新打开仍可查看图片。
- 导出的 ZIP 只包含当前账号引用的帧图和共用资源；解压后离线能打开。

本地自动验收脚本：`node scripts/test_frame_evidence.cjs --help`。它使用临时样例目录，不操作真实账号页面。


## 封面准备与旧数据迁移（2026-09-28 修订）

当前模板会使用：账号头像；带分析且口播合格的初始作品卡；selectedWorks 的全部作品卡（含未合格口播）；按 works 的四项互动总和排序的前四条作品。原模板会先创建前四条的封面节点，随后覆盖其父区块；它们不是最终常驻的列表，但为防止中间渲染触发图片请求，仍纳入少量准备范围。初始卡即使后续被模板移除，插入 DOM 时也可能请求图片，因此同样纳入范围。viralWorks 目前只参与数量统计，latestWorks 未用于显示封面；不能拿这两个数组代替实际渲染范围。

只处理这个范围。其余作品的远程封面、账号信息、评论和分析原文保持原样，不要求把 30 条或上千条作品的所有封面下载一遍。模板以后增加新的图片展示位置时，需同步修改范围函数并补浏览器测试。

已获本次公开图片下载授权时，用前置工具准备图片：

```text
python scripts/localize_assets.py --data task/analysis.json --output task/prepared.json --site task/site --download
python scripts/publish_report.py --account example --data task/prepared.json --output-dir task/site
```

工具只取实际需要的图片，携带 Referer、限制图片大小、原子写入并复用重复 URL；不读取密钥或浏览器登录。下载失败或原本地封面缺失时，使用明确的占位图并在报告 warnings 注明具体作品，不声称取得了原图。原 analysis.json 不被覆盖。需要完全不联网时把 `--download` 换成 `--offline`，远程图片会用占位图；不能把占位图当成视频或产品识别证据。已有合规本地图时无需运行该工具。

注意：前置工具不会隐藏缺失的画面证据帧。frameEvidence 指向的原图丢失仍阻止发布，以免把证据缺失伪装为完整报告。

### 旧版 frameEvidence.file

旧格式 `assets/frames/<referenceId>/t18.jpg` 迁移成 `t18.jpg`。先逐条检查：

1. 前缀必须精确等于本条作品的 `assets/frames/<referenceId>/`；作品 ID 不匹配时停止，不能只截取最后一段。
2. 剩下部分必须是单个文件名，不含斜杠、反斜杠、`..` 路径段、URL、查询参数或百分号编码。
3. 核对 `site/assets/frames/<referenceId>/<文件名>` 确实存在且解析后仍在 site 内。
4. 仅在新的分析副本中修改 file 字段，保留 t、label、caption、sub，随后执行发布校验。纯文件名的新数据不用再次转换。

### 补充验收

- 1070 条作品的样例允许保留未渲染的远程封面；只处理实际引用的封面。
- 无 frameEvidence 的新采集形态，经图片准备后发布成功；打开总览、入选作品、排名前四详情和索引均无外部请求。
- 未准备的实际可见远程图或缺失本地图给出“报告图片校验失败：作品…的封面…”友好提示，无裸 traceback。
- 图片下载失败时，报告保留 warning，占位图正常加载；未读取凭据。
