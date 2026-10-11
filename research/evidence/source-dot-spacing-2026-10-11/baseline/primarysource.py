"""Strict primary-layer literal expression lowering; not a Swift compiler."""
from fractions import Fraction
import re
import subprocess
from reloop.core import ROOT,PROJECT_ROOT,Controller,load,atomic,digest
from reloop.portable import TOOLCHAIN
from reloop.portablelayers import RUN,ANCHOR
from reloop.primarylayers import CASES,EXTRA_CASES
from reloop.viewsource import stable_ir
from reloop.wasmkit import parse_result
from reloop.verification import bytes_equal

COLOR=r'Color\s*\(\s*\.sRGB\s*,\s*red\s*:\s*([01])\s*,\s*green\s*:\s*([01])\s*,\s*blue\s*:\s*([01])\s*,\s*opacity\s*:\s*(0(?:\.[0-9]{1,3})?|1(?:\.0{1,3})?)\s*\)'
SEPARATOR=r'(?:[ \t\r]*;[ \t\r\n]*|[ \t]*\r?\n[ \t\r\n]*)'
GRAMMAR=re.compile(r'\s*ZStack\s*\{\s*'+COLOR+SEPARATOR+COLOR+SEPARATOR+COLOR+r'\s*;?\s*\}\s*\.\s*frame\s*\(\s*width\s*:\s*([0-9]{1,2})\s*,\s*height\s*:\s*([0-9]{1,2})\s*\)\s*',re.ASCII)


def parse(source):
    if type(source) is not str or len(source)>4096 or not source.isascii():raise ValueError('Bounded ASCII primary-layer expression required')
    match=GRAMMAR.fullmatch(source)
    if not match:raise ValueError('Unsupported expression outside primary-layer ZStack.frame contract')
    fields=match.groups();order=[];alphas=[0]*3
    for i in range(3):
        channels=list(map(int,fields[i*4:i*4+3]))
        if sum(channels)!=1:raise ValueError('Only explicit sRGB primaries accepted')
        channel=channels.index(1);order.append(channel);alpha=Fraction(fields[i*4+3])*8
        if alpha.denominator!=1:raise ValueError('Only alpha eighths accepted')
        alphas[channel]=int(alpha)
    if order not in ([2,0,1],[1,0,2]):raise ValueError('Supported layer orders blue/red/green or green/red/blue')
    width,height=map(int,fields[12:]);config={'width':width,'height':height,'alphas':alphas,'reverse':int(order==[1,0,2])}
    validate(config);return config


def validate(config):
    if type(config) is not dict or set(config)!={'width','height','alphas','reverse'}:raise ValueError('Invalid primary-layer configuration')
    if any(type(config[k]) is not int for k in ('width','height','reverse')) or not(1<=config['width']<=64 and 1<=config['height']<=64 and config['reverse'] in (0,1)):raise ValueError('Invalid primary-layer geometry/order')
    if type(config['alphas']) is not list or len(config['alphas'])!=3 or any(type(a) is not int or not 0<=a<=8 for a in config['alphas']):raise ValueError('Invalid primary-layer alpha values')


def lower(config):
    validate(config)
    source=(ROOT/'tools/re/fixtures/portable_layers.c').read_text()
    if source.count('unsigned render(')!=1:raise ValueError('Trusted layer kernel signature changed')
    source=source.replace('unsigned render(','static unsigned render_layers(')
    return source+'\nunsigned render(unsigned stride) { return render_layers(%d,%d,stride,%d,%d,%d,%d); }\n'%(*[config[k] for k in ('width','height')],*config['alphas'],config['reverse'])


def expression(case,reverse=0,width=17,height=9):
    alphas=(CASES+EXTRA_CASES)[case];order=(1,0,2) if reverse else (2,0,1);layers=[]
    for channel in order:
        values=[int(i==channel) for i in range(3)];alpha=str(float(Fraction(alphas[channel],8)))
        layers.append('Color(.sRGB, red: %d, green: %d, blue: %d, opacity: %s)'%(*values,alpha))
    return 'ZStack {\n'+'\n'.join(layers)+'\n}.frame(width: %d, height: %d)\n'%(width,height)


def expected(config,stride):
    validate(config)
    if type(stride) is not int or not config['width']*4<=stride<=256:raise ValueError('Unsupported source target stride')
    # Fraction oracle separate from the integer kernel and generated constants.
    values=[Fraction(0)]*4
    for channel in ((1,0,2) if config['reverse'] else (2,0,1)):
        alpha=Fraction((config['alphas'][channel]*255+4)//8,255)
        for c in range(4):
            total=(alpha if c in (channel,3) else 0)+values[c]*(1-alpha)
            values[c]=Fraction((2*(total*255).numerator+(total*255).denominator)//(2*(total*255).denominator),255)
    pixel=bytes(int(v*255) for v in values);raw=(pixel*config['width']+bytes([165])*(stride-config['width']*4))*config['height']
    return raw+bytes([195])*(16384-len(raw))


def rejected_sources():
    base=expression(4)
    return ['Text("bad")',base+';system("bad")',base.replace('ZStack','HStack'),base.replace('\n',''),base.replace('\n',' '),base.replace('\n','\t'),base.replace('17, height','65, height'),base.replace('17, height','0, height'),base.replace('17, height','width, height'),base.replace('17, height','17.0, height'),base.replace('0.5','0.1'),base.replace('0.5','value'),base.replace('0.5','-0.5'),base.replace('red: 1','red: 2'),base.replace('green: 0','green: 1'),base+'.opacity(0.5)',base.replace('17','１７'),base.replace('Color(.sRGB','Color(.displayP3'),base.replace('ZStack','ZStack(alignment: .top)'),base.replace('blue: 1','blue: 0'),base+'\x00',base.replace('Color(.sRGB','/* comment */ Color(.sRGB')]


def corpus(out):
    controller=Controller(root=PROJECT_ROOT);v=controller.verify(RUN,ANCHOR)
    if not v.get('valid') or not v.get('external_anchor_matches'):raise ValueError('Primary source native anchor changed')
    atomic(out/'native-anchor.json',v);texts=[expression(c,r) for c in (4,8,12,16,18,19) for r in (0,1)]
    texts += [texts[0],texts[0].replace('Color(', 'Color (').replace('width:', 'width :'),expression(12,0,1,1),expression(19,1,64,64)]
    rejected=[]
    for text in rejected_sources():
        try:parse(text)
        except ValueError as error:rejected.append({'source':text,'error':str(error)})
        else:raise ValueError('Unsupported primary source accepted')
    atomic(out/'diagnostics.json',rejected)
    def command(args,name):
        with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:subprocess.run([str(a) for a in args],stdout=stdout,stderr=stderr,check=True,timeout=30)
    flags=['--target=wasm32','-O2','-nostdlib','-fno-builtin','-fuse-ld='+str(TOOLCHAIN/'wasm-ld'),'-Wl,--no-entry','-Wl,--strip-all','-Wl,--initial-memory=131072','-Wl,--max-memory=131072']
    jobs=[]
    for index,text in enumerate(texts):
        config=parse(text);c=out/('source-%d.c'%index);ir=out/('source-%d.ll'%index);module=out/('source-%d.wasm'%index)
        (out/('source-%d.swift'%index)).write_text(text);c.write_text(lower(config))
        command([TOOLCHAIN/'clang','--target=wasm32','-O2','-nostdlib','-fno-builtin','-emit-llvm','-S',c,'-o',ir],'emit-%d'%index)
        raw=ir.read_text();(out/('source-%d.raw.ll'%index)).write_text(raw);ir.write_text(stable_ir(raw))
        command([TOOLCHAIN/'clang',*flags,ir,'-Wl,--export=render','-Wl,--export=pixels','-Wl,--export=capacity','-o',module],'link-%d'%index)
        strides=[config['width']*4,min(256,config['width']*4+12)]
        jobs.append({'index':index,'config':config,'strides':strides,'module':str(module),'module_sha256':digest(module),'ir_sha256':digest(ir)})
        for s,stride in enumerate(strides):
            prediction=expected(config,stride);(out/('expected-%d-%d.raw'%(index,s))).write_bytes(prediction)
    atomic(out/'jobs.json',jobs);command(['node',ROOT/'tools/re/reloop/primary_source_runner.js',out],'v8')
    execution=load(out/'execution.json');comparisons=[];native=[]
    for row in execution['rows']:
        i,s,repeat=row['job'],row['stride_index'],row['repeat'];path=out/('frame-%d-%d-%d.raw'%(i,s,repeat));comparisons.append(bytes_equal(out/('expected-%d-%d.raw'%(i,s)),path))
        cfg=jobs[i]['config'];stride=jobs[i]['strides'][s]
        if (cfg['width'],cfg['height'],stride)==(17,9,80):
            case=(CASES+EXTRA_CASES).index(tuple(cfg['alphas']));order='reverse' if cfg['reverse'] else 'forward'
            raw=(controller.runs/RUN/'output'/('layers-%d-%s-0.0.raw'%(case,order))).read_bytes()
            target=out/('native-%d-%d-%d.raw'%(i,s,repeat));target.write_bytes(raw+bytes([195])*(16384-720));native.append(bytes_equal(target,path))
    invalid=[bytes_equal(out/('expected-%d-0.raw'%i),out/('invalid-%d-%d.raw'%(i,k))) for i in range(16) for k in range(4)]
    # Checker arrays are frozen full expectations, with native prefix where measured.
    rows=[]
    for job in jobs:
        i=job['index'];arrays=[]
        for s in range(2):
            path=out/('native-%d-%d-0.raw'%(i,s));arrays.append(path.read_bytes() if path.exists() else (out/('expected-%d-%d.raw'%(i,s))).read_bytes())
        (out/('source_expected_%d.h'%i)).write_text('static const unsigned char expected_pixels[2][16384]={'+','.join('{'+','.join(map(str,raw))+'}' for raw in arrays)+'};\n')
        checker_source=out/('checker-%d.c'%i);checker_source.write_text('#include "source_expected_%d.h"\n'%i+'''extern unsigned char *pixels(void); extern unsigned capacity(void); extern unsigned render(unsigned);
unsigned verify(unsigned s,unsigned mutation) {
 if(s>1 || mutation>4 || capacity()!=16384) return 0xffffffff;
 unsigned strides[2]={%d,%d}; unsigned char *p=pixels();for(unsigned i=0;i<16384;i++)p[i]=0xc3;
 if(render(strides[s])!=strides[s]*%d) return 0xffffffff;
 if(mutation)p[mutation==1?0:mutation==2?3:mutation==3?%d:16383]^=1;
 unsigned count=0;for(unsigned i=0;i<16384;i++)count+=p[i]!=expected_pixels[s][i];return count;
}
unsigned verify_all(void){unsigned sum=0;for(unsigned s=0;s<2;s++)for(unsigned m=0;m<5;m++){unsigned n=verify(s,m);if(n!=(m?1:0))return 0xffffffff;sum+=n;}return sum;}
'''%(*job['strides'],job['config']['height'],min(job['config']['width']*4,16383)))
        checker=out/('checker-%d.wasm'%i);command([TOOLCHAIN/'clang',*flags,out/('source-%d.ll'%i),checker_source,'-I',out,'-Wl,--export=verify','-Wl,--export=verify_all','-o',checker],'checker-link-%d'%i)
        command(['node',ROOT/'tools/re/reloop/primary_source_runner.js',out,'checker',str(i)],'checker-v8-%d'%i)
        command([TOOLCHAIN/'wasmkit','run',checker,'verify_all'],'wasmkit-%d'%i);count=parse_result((out/('wasmkit-%d.stdout'%i)).read_text());rows.append({'job':i,'count':count,'passed':count==8,'module_sha256':digest(checker)})
    atomic(out/'comparisons.json',{'independent':comparisons,'native':native,'invalid':invalid});atomic(out/'wasmkit.json',rows)
    return {'source_modules':16,'frames':len(comparisons),'allocation_bytes':len(comparisons)*16384,'all_allocations_equal':all(p['passed'] for p in comparisons),'native_frames':len(native),'native_target_bytes':len(native)*720,'all_native_equal':all(p['passed'] for p in native),'invalid_requests':len(invalid),'all_invalid_unchanged':all(p['passed'] for p in invalid),'diagnostic_holdouts':len(rejected),'imports':execution['imports'],'repeat_ir_equal':jobs[0]['ir_sha256']==jobs[12]['ir_sha256']==jobs[13]['ir_sha256'],'repeat_module_equal':jobs[0]['module_sha256']==jobs[12]['module_sha256']==jobs[13]['module_sha256'],'second_runtime_cases':160,'second_runtime_passed':all(r['passed'] for r in rows),'scope':'Strict ASCII primary-layer ZStack.frame expression subset lowered through C and saved LLVM IR to WASM; explicit premultiplied callback-target contract, V8/WasmKit macOS. Native getter/PNG differs. No Swift compiler, arbitrary SwiftUI, Linux source-module execution, browser or Canvas transport claim.'}


def syntax(out):
    valid=expression(4);inputs=[valid,valid.replace('\n',''),valid.replace('\n',' '),valid.replace('\n','\t')];rows=[]
    for index,text in enumerate(inputs):
        path=out/('syntax-%d.swift'%index);path.write_text('import SwiftUI\nlet ownedView = '+text)
        result=subprocess.run(['xcrun','swiftc','-frontend','-parse',str(path)],capture_output=True,timeout=10)
        (out/('syntax-%d.stderr'%index)).write_bytes(result.stderr)
        try:parse(text);accepted=True
        except ValueError:accepted=False
        rows.append({'index':index,'native_parse_exit':result.returncode,'subset_accepted':accepted,'agreement':accepted==(result.returncode==0)})
    atomic(out/'syntax.json',rows)
    return {'native_valid_controls':sum(r['native_parse_exit']==0 for r in rows),'native_invalid_controls':sum(r['native_parse_exit']!=0 for r in rows),'all_syntax_agree':all(r['agreement'] for r in rows),'subset_invalid_rejected':sum(not r['subset_accepted'] for r in rows[1:]),'scope':'Owned Swift frontend parse-only separator controls versus strict expression parser; no typechecking, LLVM execution or native Canvas evidence.'}
