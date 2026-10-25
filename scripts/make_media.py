from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use('Agg');matplotlib.rcParams['svg.hashsalt']='aithos-c93decc-20261024'
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
R=Path(__file__).resolve().parents[1];A=R/'assets';bg='#0d141b';fg='#eff5f7';mut='#aabac5';blue='#6cafff';green='#51dec0'
fig=plt.figure(figsize=(12,6.75),facecolor=bg);ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,12),ylim=(0,6.75));ax.axis('off')
ax.text(.6,6.05,'Two physical cards. One execution graph.',color=fg,fontsize=24,fontweight='bold');ax.text(.6,5.6,'The memory and transport are still separate.',color=green,fontsize=16)
def box(x,y,w,h,title,sub,color):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.1,rounding_size=.12',facecolor='#15202b',edgecolor=color,lw=1.3));ax.text(x+.2,y+h-.38,title,color=color,fontsize=17,fontweight='bold');ax.text(x+.2,y+.28,sub,color=mut,fontsize=11,linespacing=1.5,va='bottom')
box(.7,2.1,4.2,1.6,'Intel Arc Pro B70','32 GiB nominal VRAM\nInternal adapter; exact link cost not isolated',green)
box(7.1,2.1,4.2,1.6,'NVIDIA RTX 3090','24 GiB nominal VRAM\nOCuLink (operator-reported)\nObserved PCIe Gen3 ×4',blue)
box(3.75,4.15,4.5,.72,'Windows host / system memory','',fg)
for x,col in [(2.8,green),(9.1,blue)]:ax.add_patch(FancyArrowPatch((6,4.1),(x,3.7),arrowstyle='<->',mutation_scale=18,color=col,lw=2,connectionstyle='arc3,rad=0.08'))
ax.text(5.95,3.25,'Generic synchronization\nand inter-device copies',ha='center',color=fg,fontsize=11,linespacing=1.6)
ax.text(.7,1.53,'Layer: whole layers move between devices.',color=fg,fontsize=13);ax.text(.7,1.08,'Tensor: split partial work is combined repeatedly.',color=fg,fontsize=13)
ax.text(.7,.59,'56 GiB nominal physical memory ≠ a measured shared pool. No link-width A/B or bandwidth attribution.',color=mut,fontsize=10)
fig.savefig(A/'topology.png',dpi=160,facecolor=bg,metadata={'Software':'Aithos Tech Lab / matplotlib3.10.7'});fig.savefig(A/'topology.svg',facecolor=bg,metadata={'Date':'2026-10-24T00:00:00Z','Creator':'Aithos Tech Lab'});plt.close(fig)
frames=[]
for name in ('comparison','numerical','memory'):
 im=Image.open(A/(name+'.png')).convert('RGB');im.thumbnail((1280,720));frames.append(im)
frames[0].save(A/'measured-figure-deck.gif',save_all=True,append_images=frames[1:],duration=[5000]*3,loop=0,optimize=True)
(A/'MEDIA.md').write_text('''# Local publication media

comparison.png/SVG: pp512 atub512 andtg64 atub32, every sample with processmedian/range,1920×1080PNG. PrimaryX/GitHuboverview.

numerical.png/SVG: all32centeredNMSErows, explicitlylog-scaled,1600×900. memory.png/SVG: WDDMdevice-wideobservedpeaks,1600×900. topology.png/SVG: conceptualconnectiondiagram,1920×1080, noactualbandwidthclaim. Workload-specificPNGs/SVGs showeverymeasuredsample andscope.

measured-figure-deck.gif: threeactualstoredmeasurementfigures,1280×720,5secondsperframe. It is an animatedfiguredeck, NOTa screenrecording or real-timeinferencedemonstration. No simulated/interpolatedtimings. All sourcefigures and Pythonrenderers retained. No publication has occurred.
''')
print('Created topology PNG/SVG and actual-figure GIF')
