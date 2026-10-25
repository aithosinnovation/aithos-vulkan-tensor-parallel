"""Standalone figures from stored measurements only. Run with locked project venv."""
import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
R=Path(__file__).resolve().parents[1];D=json.loads((R/'data/summary.json').read_text());A=R/'assets';A.mkdir(exist_ok=True)
BG='#0d141b';FG='#eff5f7';MUT='#aabac5';GRID='#344450';COL={'rtx':'#6cafff','b70':'#51dec0','layer':'#ffd178','tensor':'#ef8cb3'};NAMES={'rtx':'RTX 3090','b70':'Arc Pro B70','layer':'Layer split','tensor':'Tensor split'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':FG,'axes.labelcolor':MUT,'xtick.color':MUT,'ytick.color':FG,'axes.facecolor':BG,'figure.facecolor':BG,'axes.edgecolor':GRID,'savefig.facecolor':BG,'svg.fonttype':'none','svg.hashsalt':'aithos-c93decc-20261024'})
def finish(fig,name):
 fig.savefig(A/(name+'.png'),dpi=160,metadata={'Software':'Aithos Tech Lab / matplotlib3.10.7'});fig.savefig(A/(name+'.svg'),metadata={'Date':'2026-10-24T00:00:00Z','Creator':'Aithos Tech Lab'});plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,6.75));fig.subplots_adjust(top=.73,bottom=.22,wspace=.42,left=.14,right=.97)
fig.text(.06,.91,'Two vendors. One model.',fontsize=26,fontweight='bold');fig.text(.06,.84,'For this 7B model, the RTX 3090 alone beats the mixed pair.',fontsize=16,color=COL['b70'])
for ax,test,title in zip(axes,['pp512-d0-b512','tg64-d0'],['Prompt processing · pp512 · ub512','Generation · tg64 · ub32']):
 group=[x for x in D['records'] if x['test']==test];assert group
 for i,mode in enumerate(NAMES):
  rows=[x for x in group if x['mode']==mode]
  for j,row in enumerate(rows):
   y=3-i+(j-(len(rows)-1)/2)*.24;ax.hlines(y,row['min'],row['max'],color=COL[mode],lw=2,alpha=.65);ax.plot(row['median'],y,'|',color=COL[mode],markersize=18,markeredgewidth=3)
   ax.scatter(row['samples_ts'],[y+(k-2)*.014 for k in range(5)],s=26,marker='o' if row['block'] in ('A','D') else '^',color=COL[mode],zorder=3)
 ax.set_yticks(range(4),[NAMES[m] for m in reversed(NAMES)]);ax.set_ylim(-.5,3.5);ax.set_xlim(left=0);ax.set_title(title,loc='left',fontsize=14,pad=20);ax.set_xlabel('tokens / second');ax.grid(axis='x',color=GRID,alpha=.7);ax.set_axisbelow(True);ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
fig.text(.06,.125,'Every dot is a timing. Tall marks = process medians. Lines = process ranges. Circle: first order A/D; triangle: reverse B/E.',fontsize=9,color=MUT)
fig.text(.06,.082,'Exploratory · DeepSeek R1 Distill Qwen 7B Q4_K_M · Windows Vulkan c93decc · batch setting shown per panel · CPU optional ISA OFF',fontsize=9,color=MUT)
fig.text(.06,.04,'AITHOS TECH LAB   /   Matching 32 top tokens is not numerical equivalence. No hardware-ranking or energy claim.',fontsize=9,color=MUT)
finish(fig,'comparison')
# Detailed all-test plots.
for test in D['tests']:
 rows=[r for r in D['records'] if r['test']==test['id']];fig,ax=plt.subplots(figsize=(10,5.625));fig.subplots_adjust(left=.18,right=.96,top=.79,bottom=.23)
 for i,mode in enumerate(NAMES):
  rr=[r for r in rows if r['mode']==mode]
  for j,r in enumerate(rr):
   y=3-i+(j-(len(rr)-1)/2)*.24;ax.hlines(y,r['min'],r['max'],color=COL[mode],lw=2);ax.plot(r['median'],y,'|',color=COL[mode],markersize=17,markeredgewidth=3);ax.scatter(r['samples_ts'],[y+(k-2)*.013 for k in range(5)],color=COL[mode],marker='^' if r['block'] in ('B','E') else 'o',s=25)
 ax.set_yticks(range(4),[NAMES[m] for m in reversed(NAMES)]);ax.set_ylim(-.5,3.5);ax.set_xlim(left=0);ax.grid(axis='x',color=GRID);ax.set_axisbelow(True);ax.set_xlabel('tokens / second');ax.spines[['top','right','left']].set_visible(False)
 fig.text(.05,.91,test['label'],fontsize=17,fontweight='bold');fig.text(.05,.085,'All timed samples + process medians/ranges · '+('2 counterbalanced process blocks' if test['depth']==0 else '1 process block; no process-level replication'),fontsize=9,color=MUT);fig.text(.05,.04,'Exploratory as-built comparison · DeepSeek7B Q4_K_M · c93decc · ub32 · CPU optional ISA OFF',fontsize=9,color=MUT);finish(fig,test['id'])
# Numerical trace, read immutable full-vocabulary comparison evidence.
old=json.loads((R/'data/correctness.json').read_text());layer=old['layer']
fig,ax=plt.subplots(figsize=(10,5.625));fig.subplots_adjust(top=.79,bottom=.24,left=.12,right=.97)
for name,vals,col in [('B70',[x['centered_nmse'] for x in old['rows']['reference__b70']],COL['b70']),('Tensor',[x['centered_nmse'] for x in old['rows']['reference__mixed']],COL['tensor']),('Layer',[x['centered_nmse'] for x in layer['rows']],COL['layer'])]:ax.plot(range(32),vals,'o-',markersize=3,lw=1.3,label=name,color=col)
ax.set_yscale('log');ax.set_xlabel('Prediction row (0 = after prompt; 1 = first single-token decode)');ax.set_ylabel('Centered NMSE vs RTX');ax.grid(color=GRID,alpha=.5);ax.legend(facecolor=BG,edgecolor=GRID,labelcolor=FG,loc='upper right');ax.annotate('Row 1: also present in layer mode\nAll-reduce is not required for this excess.',xy=(1,layer['rows'][1]['centered_nmse']),xytext=(7,.004),fontsize=10,color=FG,arrowprops={'arrowstyle':'->','color':MUT})
fig.text(.06,.91,'Same top tokens. Different numerical paths.',fontsize=20,fontweight='bold');fig.text(.06,.095,'32 saved reference prefixes · ctx512 · centered error norm / centered reference norm · log axis explicitly shown',fontsize=9,color=MUT);fig.text(.06,.045,'Mixed tensor capture repeated bit-identically; layer tested once. No all-reduce defect or general correctness claim.',fontsize=9,color=MUT);finish(fig,'numerical')
# Coarse device-wide memory, same WDDM provider for both.
fig,ax=plt.subplots(figsize=(10,5.625));fig.subplots_adjust(top=.8,bottom=.25,left=.12,right=.97)
for i,m in enumerate(NAMES):
 rows=[x for x in D['memory'] if x['mode']==m and x['depth']==0]
 for j,(key,col,label) in enumerate([('b70_peak_mib',COL['b70'],'B70'),('nvidia_peak_mib',COL['rtx'],'RTX3090')]):
  v=[x[key]/1024 for x in rows if x[key] is not None]
  if v:ax.bar(i+(j-.5)*.32,max(v),width=.29,color=col,label=label if i==0 else None)
ax.set_xticks(range(4),NAMES.values());ax.set_ylabel('Observed device-wide dedicated memory (GiB)');ax.set_ylim(bottom=0);ax.grid(axis='y',color=GRID);ax.set_axisbelow(True);ax.legend(facecolor=BG,edgecolor=GRID,labelcolor=FG);fig.text(.06,.91,'Memory is distributed, not pooled.',fontsize=22,fontweight='bold');fig.text(.06,.11,'Max WDDM dedicated-memory snapshot across depth-0 processes; observed maxima come from ub512 blocks.',fontsize=9,color=MUT);fig.text(.06,.055,'Includes loading and both pp512/tg64 tests; device-wide background usage. No Intel power data.',fontsize=9,color=MUT);finish(fig,'memory')
print('Wrote',len(list(A.glob('*.png'))),'PNG figures and matching SVG source figures')
