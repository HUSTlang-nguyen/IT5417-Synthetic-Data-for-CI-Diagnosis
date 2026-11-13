import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {registerHooks,createRequire} from 'node:module';
import {inflateSync} from 'node:zlib';

const root=process.cwd();
const runtime=process.env.RUNTIME_NODE_MODULES;
if(!runtime)throw new Error('Set RUNTIME_NODE_MODULES to the supplied bundled runtime');
process.on('uncaughtException',e=>{console.error(e.stack);process.exit(1);});
// Adapt bundled font metrics in the private build directory; never alter the bundled runtime.
const fontDir=path.join(root,'.cache/midterm/font-compat');await fs.mkdir(fontDir,{recursive:true});
for(const name of ['Courier','Courier-Bold','Courier-BoldOblique','Courier-Oblique','Helvetica','Helvetica-Bold','Helvetica-BoldOblique','Helvetica-Oblique','Symbol','Times-Bold','Times-BoldItalic','Times-Italic','Times-Roman','ZapfDingbats']){
 const compressed=JSON.parse(await fs.readFile(path.join(runtime,'@pdf-lib/standard-fonts/lib',name+'.compressed.json'),'utf8'));
 const f=JSON.parse(inflateSync(Buffer.from(compressed,'base64')).toString());
 const glyphs=f.CharMetrics.map(g=>g.N);const groups=new Map();
 for(const [a,b,amount] of f.KernPairs){const index=glyphs.indexOf(a)*glyphs.length+glyphs.indexOf(b);if(index<0)continue;const values=groups.get(amount)||[];values.push(index);groups.set(amount,values);}
 const kern=[];for(const [amount,indices] of groups){indices.sort((a,b)=>a-b);let previous=0;kern.push(amount,indices.map(v=>{const delta=v-previous;previous=v;return delta;}));}
 await fs.writeFile(path.join(fontDir,name.replaceAll('-','')+'.json'),JSON.stringify({name:f.FontName,bbox:f.FontBBox,ascender:f.Ascender||0,descender:f.Descender||0,xHeight:f.XHeight||0,capHeight:f.CapHeight||0,glyphNames:glyphs.join(' '),glyphWidths:f.CharMetrics.map(g=>g.WX),kernPairs:kern}));
}
registerHooks({resolve(specifier,context,nextResolve){
 if(specifier.startsWith('#standard-fonts/'))return nextResolve(path.join(fontDir,specifier.slice(16)+'.json'),context);
 return nextResolve(specifier,context);
}});
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {PDFDocument}=createRequire(path.join(runtime,'__runtime__.cjs'))('pdf-lib');
const source=process.env.HUST_TEMPLATE || 'C:/Users/neikh/Downloads/HUST PPT Template 2021 ( Red 3X4).pptx';
const skill='C:/Users/neikh/.codex/plugins/cache/openai-primary-runtime/presentations/26.1111.10930/skills/presentations';
const tmp=path.join(root,'.cache/midterm');const out=path.join(root,'output/midterm');
await fs.mkdir(tmp,{recursive:true});await fs.mkdir(out,{recursive:true});
const facts=JSON.parse(await fs.readFile('docs/midterm/facts.json','utf8'));
const content=JSON.parse(await fs.readFile('docs/midterm/slides.json','utf8'));
if(content.length!==28 || content.slice(0,24).reduce((a,s)=>a+s.seconds,0)!==1200)throw new Error('Slide/time contract');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const cover=p.slides.items[2].copy();const body=p.slides.items[3].copy();
p.slides.keep([]);
let serial=0;
const text=(s,value,x,y,w,h,size=27,bold=false,color='#222222',align='left')=>{
 const q=s.shapes.add({name:'content-'+(++serial),geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=value;q.text.style={typeface:'Calibri',fontSize:size,bold,color,alignment:align,verticalAlignment:'top',wrap:'square',autoFit:'none',insets:0};return q;
};
const para=(s,items,y=130,size=29,gap=102)=>items.forEach((v,i)=>{text(s,String(i+1)+'.',43,y+i*gap,34,45,size,true,'#BE1E32');text(s,v,89,y+i*gap,805,gap-12,size);});
const table=(s,values,{y=150,widths,fsz=23,h=60}={})=>{
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:40,top:y,width:880,height:h*values.length,columnWidths:widths,values});
 t.borders.assign({fill:'#C7C7C7',width:.7,style:'solid'});
 for(let r=0;r<values.length;r++){
  t.rows[r].height=h;
  for(let c=0;c<values[0].length;c++){
   const cell=t.getCell(r,c);cell.fill=r===0?'#BE1E32':'#FFFFFF';
   cell.text.style={typeface:'Calibri',fontSize:fsz,bold:r===0,color:r===0?'#FFFFFF':'#222222',verticalAlignment:'middle',alignment:c===0?'left':'center',insets:7,wrap:'square',autoFit:'none'};
  }
 }
 return t;
};
const foot=(s,value,y=560)=>text(s,value,42,y,870,72,23,false,'#444444');
const code=(s,value,x,y,w,h,size=23)=>text(s,value,x,y,w,h,size,false,'#222222');
const box=(s,label,x,y,w=205,h=68)=>{
 const q=s.shapes.add({name:'architecture-'+(++serial),geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:'#FFFFFF',line:{fill:'#555555',width:1.3}});
 q.text=label;q.text.style={typeface:'Calibri',fontSize:24,alignment:'center',verticalAlignment:'middle',insets:5,color:'#222222'};return q;
};
const connect=(s,a,b,extra={})=>s.shapes.connect(a,b,{kind:'elbow',fromSide:'right',toSide:'left',line:{fill:'#555555',width:1.5},tail:{type:'triangle',width:'sm',length:'sm'},...extra});
const metricRows=(scores,n)=>[['Model','Acc. %','Macro-F1','File T1','Hàm T1','Joint','Invalid'],...Object.entries(scores).map(([name,m])=>[name,(100*m.classification_accuracy).toFixed(2),m.macro_f1.toFixed(4),...['file_top1_correct','function_top1_correct','joint_top1_correct','invalid_output'].map(k=>name==='M0'?'—':`${m.counts[k]}/${n}`)])];
for(let i=0;i<content.length;i++){
 const d=content[i];const s=p.slides.addCopy(i===0?cover:body);
 if(i===0){
  const labels=s.shapes.items.filter(q=>q.text?.toString?.().includes('PRESENTATION TITLE')||q.text?.toString?.().includes('SUBTITLE'));
  for(const q of labels)q.text='';
  text(s,d.title,49,218,740,125,44,true,'#C00000');
  text(s,'Đồ án IT5417 — Bảo vệ giữa kỳ\nCập nhật 13/11/2026',50,369,650,80,28,false,'#C00000');
  text(s,'Họ tên: _______________________\nMSSV: ________________________\nGVHD: Vũ Thị Hương Giang',50,492,670,112,25);
 }else{
  for(const q of [...s.shapes.items]){
   if(/Number/.test(q.name||'')){q.text=String(i+1);q.position={left:869,top:689,width:61,height:23};q.text.style={typeface:'Lato',fontSize:16,bold:true,color:'#C00000',alignment:'right'};}
   else if(/Title/.test(q.name||'')){q.text=d.title;q.text.style={typeface:'Lato',fontSize:35,bold:true,color:'#FFFFFF',insets:0,verticalAlignment:'middle',wrap:'none',autoFit:'none'};}
   else if(/Content Placeholder/.test(q.name||''))q.text='';
  }
  if(d.type==='bullets')para(s,d.items);
  if(d.type==='io'){
   text(s,'INPUT',50,123,400,35,30,true,'#BE1E32');text(s,'TARGET / OUTPUT',502,123,415,35,30,true,'#BE1E32');
   para(s,['Log của phiên bản đang lỗi','Code liên quan qua retrieval'],185,28,95);
   // Override the left-column text widths rather than shrinking body type.
   for(const q of s.shapes.items)if((q.position.left===89)&&(q.position.top>=185))q.position={...q.position,width:340};
   code(s,'{\n  "cause_type": "…",\n  "locations": [{\n    "file": "…",\n    "function": "…"\n  }],\n  "explanation": "…"\n}',505,181,398,322,27);
   foot(s,'Không đưa repair patch, reference, assessment hoặc edit-site vào input.\nJSON trên chỉ minh họa cấu trúc.',552);
  }
  if(d.type==='architecture'){
   const nodes=[];
   for(let r=0;r<3;r++){nodes[r]=[];for(let c=0;c<4;c++){nodes[r][c]=box(s,facts.architecture[r][c],40+c*225,142+r*133);if(c)connect(s,nodes[r][c-1],nodes[r][c]);}}
   connect(s,nodes[0][3],nodes[1][0],{fromSide:'bottom',toSide:'top',line:{fill:'#777777',width:1.2,style:'dashed'}});
   connect(s,nodes[1][3],nodes[2][0],{fromSide:'bottom',toSide:'top',line:{fill:'#777777',width:1.2,style:'dashed'}});
   foot(s,'Synthetic chỉ từ train seed và chỉ vào train.\nAIDev thuộc các đợt development trước pilot SFT.',582);
  }
  if(d.type==='sources'){
   table(s,[['Nguồn','Có sẵn','Vai trò hiện tại'],['AIDev','PR / repo / provenance','W1 và development'],['SWE-bench','Revision, repair/test patch,\nF2P / P2P','250 real của pilot']],{widths:[160,390,330],h:96,fsz:26});
   foot(s,'Taxonomy, causal file/hàm và explanation cần phân tích evidence.\nKhông suy ai gây lỗi từ actor của PR.',507);
  }
  if(d.type==='reproduction'){
   table(s,[['Phiên bản','Test patch','Điều kiện'],['Base','Cùng test patch đã ghim','F2P fail'],['Base + repair','Cùng test patch đã ghim','F2P pass; P2P giữ pass']],{widths:[205,375,300],h:85,fsz:25});
   foot(s,'Giữ source/test/image hashes. Tách lỗi harness khỏi lỗi ứng dụng.\nCác log là tái hiện local, không phải log CI lịch sử.',507);
  }
  if(d.type==='dataset'){
   table(s,[['Tập','Real','Synthetic','Sử dụng'],['Train M2','175','0','SFT'],['Train M5','175','101','SFT'],['Validation','37','0','Chọn checkpoint'],['Test','38','0','Đánh giá cuối']],{widths:[220,145,180,335],h:63,fsz:25});
   foot(s,'Chia theo repo/group. Synthetic chỉ ở train; nhãn silver.\nMục tiêu 175 synthetic của v1.0 còn thiếu 74.',515);
  }
  if(d.type==='verification'){
   const labels=['Baseline\nPASS','Candidate\nFAIL × 3','Restoration\nPASS'];const ns=labels.map((v,j)=>box(s,v,64+j*300,200,230,110));
   connect(s,ns[0],ns[1]);connect(s,ns[1],ns[2]);
   text(s,'Sau runner: rà nhãn, vị trí, hợp lý và trùng lặp',58,380,845,58,30,true);
   foot(s,'Docker không mạng, không đặc quyền; có timeout và giới hạn tài nguyên.\nCandidate không chạy trên host.',499);
  }
  if(d.type==='labels'){
   table(s,[['Loại nguyên nhân','Mô tả'],['syntax','Ngữ pháp Python không hợp lệ'],['dependency/configuration','Dependency hoặc cấu hình runtime'],['API/type','Sai kiểu, lời gọi hoặc giao diện'],['logic/value','Sai tính toán, điều khiển hoặc biểu diễn']],{widths:[330,550],h:64,fsz:25});
   foot(s,'Silver: nhãn có phân tích evidence, chưa phải expert gold.\nUnknown khi thiếu bằng chứng; exception không tự quyết định nhãn.',522);
  }
  if(d.type==='real_example'){
   text(s,'Input: trích code và assertion',45,119,420,42,27,true,'#BE1E32');
   code(s,'Field.__init__  [hai dòng trích]\n\n**metadata\n\nself.metadata = metadata',45,179,413,194,25);
   code(s,'Kỳ vọng:\n{"description": "foo",\n "widget": "select"}\n\nQuan sát: thêm một cấp\n{"metadata": {...}}',45,386,425,216,24);
   text(s,'Hai trường của target silver',502,119,412,42,27,true,'#BE1E32');
   code(s,'{\n "cause_type": "API/type",\n "locations": [{\n   "file":\n   "src/marshmallow/fields.py",\n   "function": "Field.__init__"\n }]\n}',502,178,414,314,23);
   text(s,'Keyword metadata bị bọc thêm một cấp.\nExplanation đầy đủ trong ghi chú/snapshot.',502,515,407,93,24);
  }
  if(d.type==='synthetic_example'){
   text(s,'PVSystem._validate_per_array',45,123,865,42,30,true);
   text(s,'Seed pass',45,192,190,36,27,true,'#BE1E32');
   code(s,'if system_wide and not isinstance(values, tuple):\n    return (values,) * self.num_arrays',45,241,865,82,26);
   text(s,'Candidate: 7B bỏ not',45,350,865,36,27,true,'#BE1E32');
   code(s,'if system_wide and isinstance(values, tuple):\n    return (values,) * self.num_arrays',45,399,865,82,26);
   foot(s,'Scalar không broadcast; log báo ValueError: Length mismatch…\nSilver: logic/value, pvlib/pvsystem.py, đúng hàm trên. Diff chỉ để giải thích.',535);
  }
  if(d.type==='models'){
   table(s,[['Model','Phương pháp / dữ liệu','Trạng thái'],['M0','TF-IDF + Logistic Regression','Đã chạy; chỉ class'],['M1 / P2','3B prompt-only; P2 prompt mới','Đã chạy'],['M2','3B QLoRA, 175 real','Đã chạy'],['M3','Đối chứng mất cân bằng','Chưa chạy'],['M4','Synthetic chưa rà/lọc đầy đủ','Chưa chạy'],['M5','3B QLoRA, 175 real + 101 synthetic','Đã chạy']],{widths:[140,515,225],h:60,fsz:24});
   foot(s,'M2 và M5 là hai adapter độc lập từ cùng base, không học tiếp nhau.',592);
  }
  if(d.type==='training'){
   table(s,[['Thành phần','Cấu hình pilot'],['Base / tính toán','Qwen2.5-Coder-3B-Instruct; NF4 / BF16'],['LoRA','rank 16; alpha 32; dropout 0,05'],['Batch / seed','1 × accumulation 8; seed 5417'],['Context / output','2.048 / 384 token'],['Loss','Chỉ token câu trả lời target']],{widths:[250,630],h:64,fsz:25});
   foot(s,'Parent LR 1e-4; continuation bắt đầu 2e-5 rồi giảm về 0.\nCùng epoch không đồng nghĩa cùng updates/token/compute.',558);
  }
  if(d.type==='continuation'){
   table(s,[['Mốc','M2','M5'],['Parent','104 updates ≈ 4,73 epoch','104 updates ≈ 2,99 epoch'],['Đích tổng','220 updates = 10 epoch','350 updates = 10 epoch'],['Học thêm','116 updates','246 updates'],['Checkpoint được chọn','Parent 104','Parent 104']],{widths:[270,305,305],h:70,fsz:25});
   foot(s,'Chọn theo joint validation; hòa chọn checkpoint sớm.\nĐã học đủ 10 epoch nhưng không test adapter cuối epoch 10.',548);
  }
  if(d.type==='milestones'){
   table(s,[['Chặng','Kết quả đã có'],['W1 / development','Properr: 2/3; expansion: 17 case / 10 repo'],['Thu thập và curation','250 real + 101 synthetic khóa cho pilot'],['Huấn luyện','M0/M1; hai SFT và hai continuation hoàn tất'],['Đánh giá','Validation, một final test; phân tích lỗi/chi phí']],{widths:[280,600],h:77,fsz:25});
   foot(s,'132 kiểm thử phần mềm: 131 pass, 1 skip.\nSố liệu development không cộng vào dataset SFT.',562);
  }
  if(d.type==='metrics'){
   table(s,[['Metric','Ý nghĩa'],['Accuracy','Tỷ lệ đúng loại lỗi'],['Macro-F1','Trung bình F1 bốn lớp cố định'],['File Top-1','File đầu tiên khớp reference'],['Hàm Top-1','Cặp file/hàm đầu tiên khớp reference'],['Đúng loại + hàm','Hai điều kiện cùng đúng trên một mẫu']],{widths:[260,620],h:65,fsz:25});
   foot(s,'Top-5 xét 5 vị trí đầu. Invalid vẫn trong mẫu số.\nScorer giữ cổng retrieval visibility; reference hàm hiện có ở 12/38 test.',562);
  }
  if(d.type==='validation'||d.type==='test'){
   const n=d.type==='validation'?37:38;
   table(s,metricRows(d.type==='validation'?facts.validation.scores:facts.evaluation.test_metrics,n),{widths:[130,120,150,120,120,120,120],y:169,h:70,fsz:23});
   foot(s,'M1-P2: prompt mới. M2/M5: prompt cũ, checkpoint parent104.\nNhãn silver; M0 chỉ phân loại. T1 = Top-1.',557);
   text(s,'File / Hàm / Joint / Invalid hiển thị số mẫu; Acc. là %, F1 trong [0,1].',43,113,870,40,24);
  }
  if(d.type==='comparison'){
   table(s,[['Tiêu chí theo từng mẫu','Chỉ M2 đúng','Chỉ M5 đúng'],['Phân loại','2','4'],['Hàm Top-1','1','2'],['Joint','1','1']],{widths:[440,220,220],h:70,fsz:27});
   foot(s,'Joint tổng cùng 4/38. M5 tăng nhẹ class, file Top-1 lại giảm.\nReference hàm vắng ở 26/38; train thiếu hai lớp. Một seed, chưa M3/M4.',514);
  }
  if(d.type==='m1_history'){
   table(s,[['Lượt','Validation invalid','Test invalid'],['M1 cũ','37/37','Không dùng'],['M1-P2 (prompt mới)','1/37','8/38']],{widths:[390,245,245],h:84,fsz:27});
   foot(s,'Strict JSON giữ nguyên, không bỏ Markdown fences.\nUser code/log giữ nguyên; chỉ đổi hai đoạn system prompt.',486);
  }
  if(d.type==='per_class'){
   table(s,[['Nhãn silver test','Support','M2 đúng','M5 đúng'],['logic/value','21','15','18'],['API/type','9','7','6'],['dependency/configuration','8','0','0'],['syntax','0','—','—']],{widths:[390,140,175,175],h:66,fsz:25});
   foot(s,'Pylint class: 10/19 lên 12/19; Flask cùng 2/3; Pytest cùng 10/16.\nTrain chỉ có logic/value và API/type, lệch mạnh về SymPy.',540);
  }
  if(d.type==='costs'){
   table(s,[['Wall time (giây)','M2','M5'],['Parent','2.217','2.106'],['Continuation','2.170','4.218'],['Tổng','4.387','6.324']],{widths:[440,220,220],h:76,fsz:28});
   foot(s,'Tính cả học tiếp dù vẫn chọn parent104; không cộng trùng validation.\n151 request mới, không gọi trùng. Wall time không phải GPU compute.',534);
  }
 }
 s.hidden=i>=24;
 const timing=i<24?`Thời lượng dự kiến: ${d.seconds} giây.\n`: 'Slide dự phòng, ngoài 20 phút chính.\n';
 const example=i===13?facts.examples.real:i===14?facts.examples.synthetic:null;
 s.speakerNotes.text=timing+d.notes+(example?'\nTarget explanation nguyên văn: '+example.reference.explanation:'');
 await fs.writeFile(path.join(tmp,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await (await s.export({format:'png',scale:1})).arrayBuffer()));
 await fs.writeFile(path.join(tmp,`slide-${String(i+1).padStart(2,'0')}.json`),await (await s.export({format:'layout'})).text());
 console.log('Rendered slide',i+1,d.title);
}
await (await PresentationFile.exportPptx(p)).save(path.join(tmp,'draft.pptx'));
// shortcut: native-size PDF pages avoid renderer footer/spacing bugs; use vector PDF when upstream fixes them.
const pdf=await PDFDocument.create();
for(let i=0;i<28;i++){
 const img=await pdf.embedPng(await fs.readFile(path.join(tmp,`slide-${String(i+1).padStart(2,'0')}.png`)));
 pdf.addPage([720,540]).drawImage(img,{x:0,y:0,width:720,height:540});
}
await fs.writeFile(path.join(tmp,'slides.pdf'),await pdf.save());
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const crypto=await import('node:crypto');
const sha=crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex');
await finalizePresentation({workspaceDir:root,candidatePath:path.join(tmp,'draft.pptx'),finalPath:path.join(out,'hust-midterm.pptx'),
 pythonExecutable:'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1111-570-0_26.1111.570.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','9144000,6858000','--validate-heading-fit',...[6,8,10,13,16,17,18,19,20,21,22,23,25,26,27,28].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:28, requiredNativeTableOwnerSlides:[6,8,10,13,16,17,18,19,20,21,22,23,25,26,27,28],
 sourceTemplatePath:source,expectedSlideSizeEmu:'9144000,6858000',
 fontPolicy:{basis:'design',families:['Lato','Calibri']},
 verifyArtifactToolImport:true,receiptPath:path.join(tmp,'slides-validation.json')});
await fs.copyFile(path.join(tmp,'slides.pdf'),path.join(out,'hust-midterm.pdf'));
await fs.writeFile('docs/midterm/speaker-notes.md','# Ghi chú thuyết trình — 20 phút\n\n'+content.map((d,i)=>`## ${i+1}. ${d.title.replaceAll('\n',' ')}${i>=24?' (dự phòng)':''}\n\n${i<24?d.seconds+' giây. ':''}${d.notes}\n`).join('\n'));
console.log('Exported editable PPTX and PDF, with 24 main + 4 hidden backup slides');
