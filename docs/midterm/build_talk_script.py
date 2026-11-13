"""Format the speaking manuscript; never loads research models or raw candidates."""
from pathlib import Path
import json
import re

HERE=Path(__file__).resolve().parent
slides=json.loads((HERE/'slides.json').read_text(encoding='utf-8'))
source=(HERE/'talk-script.md').read_text(encoding='utf-8')
parts=re.split(r'^## Slide (\d+)(?:[^\n]*)\s*$',source,flags=re.M)
sections={int(parts[i]):parts[i+1].strip() for i in range(1,len(parts),2)}
assert sorted(sections)==list(range(1,29))
assert len(slides)==28 and sum(s['seconds'] for s in slides[:24])==1200

def tex(value):
    return ''.join({'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','{':r'\{','}':r'\}'}.get(c,c) for c in value)

def clock(seconds):return f'{seconds//60:02}:{seconds%60:02}'

intro='Đọc các đoạn văn; phần trong ngoặc vuông là nhắc thao tác, không đọc thành tiếng. Mốc thời gian là mục tiêu từ bộ slide, chưa phải thời lượng nói thử đã đo. Có thể dừng ở bảng/sơ đồ; bốn slide dự phòng chỉ dùng khi được hỏi.'
lines=[r'\documentclass[12pt,a4paper]{article}',r'\input{common.tex}',r'\fancyhead[L]{\small Lời thuyết trình — IT5417}',r'\fancyhead[R]{\small 24 slide chính / khoảng 20 phút}',r'\setstretch{1.15}',r'\setlength{\parindent}{0pt}',r'\setlength{\parskip}{6pt}',r'\begin{document}',r'{\Large\bfseries Lời thuyết trình bảo vệ giữa kỳ}\par',tex(intro),r'\medskip']
md=['# Lời thuyết trình bảo vệ giữa kỳ','', '**Cách dùng:** '+intro,'']
timeline=[];elapsed=0;main_words=0
for index,slide in enumerate(slides,1):
    body=sections[index]
    body=re.sub(r'^\*\*Thời gian.*?\*\*\s*\n','',body,flags=re.M).strip()
    title=slide['title'].replace('\n',' ')
    if index<=24:
        duration=slide['seconds'];end=elapsed+duration
        timing=f'{clock(elapsed)}–{clock(end)} · {duration} giây'
        timeline.append({'slide':index,'start':elapsed,'end':end,'seconds':duration})
        elapsed=end
        main_words+=len(re.sub(r'\[[^\]]*\]','',body).split())
    else:timing='Dự phòng — ngoài thời lượng 20 phút'
    if index>1 and index%2==1:lines.append(r'\clearpage')
    if index==25:lines.append(r'{\Large\bfseries Phần dự phòng — chỉ dùng khi được hỏi}\par')
    lines += [r'\subsection*{'+tex(f'Slide {index}. {title}')+'}',r'{\small\color{gray}'+tex(timing)+'}\par']
    for para in body.split('\n\n'):
        if para.startswith('[') and para.endswith(']'):
            lines.append(r'{\itshape\color{gray}'+tex(para)+'}\par')
        else:lines += [tex(para),'']
    md += [f'## Slide {index} — {title}','',f'**Thời gian: {timing}**','',body,'']
lines += [r'\end{document}']
(HERE/'talk-script.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(HERE/'talk-script.md').write_text('\n'.join(md),encoding='utf-8')
receipt={'main_slides':24,'backup_slides':4,'planned_seconds':elapsed,'spoken_whitespace_units':main_words,'timeline':timeline,'qualification':'Timing is planned, not an actual rehearsal. No model run or score changes.'}
(HERE/'talk-script-timing.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='timeline'},ensure_ascii=False))
