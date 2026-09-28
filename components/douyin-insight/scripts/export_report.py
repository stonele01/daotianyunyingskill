"""Export one account only, with shared assets and no machine-specific evidence paths."""
from __future__ import annotations
import argparse,json,re,zipfile
from pathlib import Path
import os
from frame_evidence import local_asset, validate_visual_evidence
WORKSPACE = Path(os.getenv("DOUYIN_INSIGHT_WORKSPACE") or Path(__file__).resolve().parents[1]/"workspace")
def valid_account(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",value):raise ValueError("Invalid account")
    return value

def export(account,output,site):
    account=valid_account(account);site=Path(site).resolve();output=Path(output).resolve()
    index=json.loads((site/'comment-insight-index.json').read_text(encoding='utf-8'));row=next((r for r in index['reports'] if r['accountId']==account),None)
    if not row:raise ValueError('该账号尚未发布报告')
    page=(site/f'{account}.html').read_text(encoding='utf-8');match=re.search(r'const pageData=(.*?);\s*/\* INSIGHT_DATA_END',page,re.S)
    if not match:raise ValueError('报告数据格式无效')
    data=json.loads(match.group(1))
    def clean(v):
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ('spokenScriptPath','asrMetadataPath','subtitlePath','sourceAnalysis')}
        if isinstance(v,list):return [clean(x) for x in v]
        return v
    data=clean(data);blob=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    page=page[:match.start(1)]+blob+page[match.end(1):]
    paths=set()
    for v in [data.get('avatar'),*(w.get('cover') for w in data.get('works',[]))]:
        if isinstance(v,str) and v.startswith('assets/'):
            p=(site/v).resolve()
            if not p.is_relative_to(site):raise ValueError('资源路径越界')
            if p.is_file():paths.add(p)
    errors=validate_visual_evidence(data,site)
    if errors:raise ValueError('; '.join(errors))
    for analysis in data.get('workAnalyses',[]):
        work_id=str(analysis.get('referenceId') or analysis.get('reference_id'))
        for frame in analysis.get('frameEvidence',[]):
            paths.add(local_asset(site,f"assets/frames/{work_id}/{frame['file']}"))
    for folder in ('assets/ui','assets/icons','assets/vendor'):
        paths.update(p for p in (site/folder).rglob('*') if p.is_file())
    index['reports']=[row]
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix(output.suffix+'.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'{account}.html',page)
        homepage=(site/'comment-insight-index.html').read_text(encoding='utf-8')
        z.writestr('index.html',homepage);z.writestr('comment-insight-index.html',homepage)
        z.writestr('comment-insight-index-data.js','window.COMMENT_INSIGHT_INDEX='+json.dumps(index,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n')
        z.writestr('comment-insight-index.json',json.dumps(index,ensure_ascii=False,indent=2))
        for p in sorted(paths):z.write(p,p.relative_to(site))
    temp.replace(output);return {'accountId':account,'archive':str(output),'entrypoint':'index.html','note':'包含本账号原始评论与分析；分享前自行核对。封面、帧图、脚本和样式随包导出，可离线打开。'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--account',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--site',type=Path,default=WORKSPACE/'site');a=ap.parse_args()
    print(json.dumps(export(a.account,a.output,a.site),ensure_ascii=False,indent=2))
