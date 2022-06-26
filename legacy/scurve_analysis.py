#!/usr/bin/env python
# coding: utf-8

# In[1]:

import argparse
import pathlib


import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import iqr
from scipy.stats import binned_statistic, binned_statistic_2d
from scipy.stats import norm
from scipy.special import erf
#from root_pandas import read_root
from copy import copy
from math import sqrt
from math import isnan
import seaborn as sns
import glob
import os,sys
#get_ipython().run_line_magic('matplotlib', 'inline')
mpl.use('Agg')

import mplhep
plt.style.use(mplhep.style.CMS)
# In[29]:

parser = argparse.ArgumentParser("Scurve analysis")
parser.add_argument("ifile", type=pathlib.Path, help="Scurve input file")
parser.add_argument("odir", type=pathlib.Path, help="Scurve output directory")
parser.add_argument("--db", type=pathlib.Path, help="VFAT database file")
parser.add_argument("--mapping", type=pathlib.Path, help="VFAT mapping file")
parser.add_argument("--thresholds", type=pathlib.Path, help="VFAT thresholds from s-bits")
args = parser.parse_args()

db_df = pd.read_csv(args.db, sep=";")
mapping_df = pd.read_csv(args.mapping, sep=";")
df_calDAC = mapping_df.join(db_df.set_index("chip-id"), on="chip-id")

#df_calDAC = pd.read_csv("testbeam.cfg", header=0,delimiter=";")

scurve_file = args.ifile

#if len(sys.argv) < 4:
#	print("Usage: scurves.py [input_file] [oh_number] [output_directory]")

output_dir = args.odir
os.makedirs(output_dir, exist_ok=True)

import time

i=0
while i==0:
    df=pd.read_csv(scurve_file, header=0)
    #df2['oh'] = args.oh
    #df=pd.concat([df2])


    # In[31]:


    df.head(2)


    # In[32]:


    def plot_summary(df,oh,df_calDAC):
        
        nvfats = len(df.vfatN.unique())
        nrows = 3
        ncols = int(np.ceil(nvfats/nrows))
        summary_fig, summary_axs = plt.subplots(nrows, ncols, figsize=(9*ncols, 9*nrows))
        summary_axs = summary_axs.flat

        plt.figure(figsize=(9,9))
        cmap_new = copy(mpl.cm.get_cmap('viridis'))
        cmap_new.set_under('w')
        my_norm = mpl.colors.Normalize(vmin=.25, vmax=200, clip=False)

        plt.xlabel('vfat channel',fontsize=20)
        plt.xticks(fontsize=16)
        plt.ylabel('charge [fC]', fontsize=20)
        plt.yticks(fontsize=16)
        #print(df_cal)
        for ivfat,vfatN in enumerate(df.vfatN.unique()):
            sel=(df.vfatN==vfatN)&(df.oh==oh)
            df_sel=df[sel].copy()

            #idx = df_sel[df_sel['vfatN'] == int(vfatN)].index.tolist()[0]
            #df_sel.loc[:,'fC']=df_sel['charge']*df_cal.slope[idx]+df_cal.intercept[idx]
            sel_cal=(df_cal.vfat==int(vfatN))&(df_cal.oh==oh)
            slope = list(df_cal[sel_cal]['slope'])[0]
            intercept = list(df_cal[sel_cal]['intercept'])[0]
            df_sel.loc[:,'fC']=df_sel['charge']*slope+intercept
            #plt.scatter(df_sel['ch'],df_sel['fC'],c=df_sel['fired'],cmap=cmap_new, norm=my_norm, s=2)
            #plt.title('OH %i, VFAT %i'%(oh,vfatN), fontsize=20)
            #cbar=plt.colorbar()
            #cbar.ax.tick_params(labelsize=16) 
            #cbar.ax.set_ylabel('# of hits', rotation=270, fontsize=20,labelpad=10)
            #plt.tight_layout()
            #plt.savefig(output_dir / f'Summary_OH{oh}_VFAT{vfatN}.png')
            #plt.show()
            
            #print('Saving to Summary_OH%i_VFAT%i.png'%(oh,vfatN))
            plt.clf()
            summary_img = summary_axs[ivfat].scatter(df_sel['ch'],df_sel['fC'],c=df_sel['fired'],cmap=cmap_new, norm=my_norm, s=2)
            summary_axs[ivfat].set_title('OH %i, VFAT %i'%(oh,vfatN), fontsize=20)
            summary_axs[ivfat].set_xlabel('vfat channel',fontsize=20)
            summary_axs[ivfat].set_ylabel('charge [fC]', fontsize=20)
        summary_fig.tight_layout()
        print('Saving to Summary_OH%i.png'%(oh))
        summary_fig.savefig(output_dir / f'Summary_OH{oh}.png')


# In[33]:


    from multiprocessing import Process
    from multiprocessing import Queue
    #import psutil
    dfs=[]
    #q = Queue()
    for oh in df.oh.unique():
        print ("OH",oh)
        sel=df.oh==oh
        df_sel=df[sel].copy()
        sel2=df_calDAC.oh==oh

        df_cal=df_calDAC[sel2][["oh","vfat","cal-dac-m","cal-dac-b"]].copy().rename(columns={"oh":"oh","vfat":"vfat","cal-dac-m":"slope","cal-dac-b":"intercept"}).reset_index(drop=True)
        #p=Process(target=plot_summary,args=(df_sel,oh,df_cal,q))
        df_cal.set_index("vfat", inplace=True, drop=False)#, verify_integrity=True)
        print(df_cal)
        plot_summary(df_sel,oh,df_cal)
        #p.start()

    i += 1
    #print('Sleeping 5 s...')
    #time.sleep(5)


# In[7]:


def sigmoid(x, x0, sigma, b):
    y=b*erf(-(x-x0)/(sqrt(2)*sigma))+b
    return (y)


# In[8]:


def gauss_function(x, a, x0, sigma):
    return a*np.exp(-(x-x0)**2/(2*sigma**2))


# In[9]:


def fit_all(df,oh):
    df_summary=pd.DataFrame(columns=['oh','vfatN','vfatCH','mean','sigma','norm'])
    for j in df.vfatN.unique():
        print ("Noise fitting VFAT %i"%(j))
        sel=df.vfatN==j
        df_vfat=df[sel]
        for i in range(0,128):
            sel=df_vfat.ch==i
            df_sel=df_vfat[sel].copy()
            xdata=df_sel.charge
            ydata=df_sel.fired*1.0
            sel_med=abs(df_sel['fired']-500)<400  
            x0_init=df_sel[sel_med].charge.median()
            if(isnan(x0_init)):
                df_summary.loc[len(df_summary)]=[oh,j, i,0.0,-1.0,0.0]
                continue
            p0 = [x0_init,3.0,0.5*max(ydata)]
            try: 
                popt, pcov = curve_fit(sigmoid, xdata, ydata ,p0,xtol=0.0001, ftol=0.0001)
            except:
                popt=[0.0,-1.0,0.0]
            df_summary.loc[len(df_summary)]=[oh,j,i, popt[0], popt[1], popt[2]]
            #print("oh {} vfat {} channel {} noise {}".format(oh, j, i, popt[1]))
    return df_summary


# In[10]:


df_summary_all=[]
for oh in df.oh.unique():
    sel=df.oh==oh
    df_sel=df[sel].copy()
    df_new=fit_all(df_sel,oh)
    df_summary_all.append(df_new)
    df_summary=pd.concat(df_summary_all)



# In[11]:

plt.figure(figsize=(8,6))
sel=df_summary['mean']>0
df=df_summary[sel]
def calculate_fC(val,vfatN,df_calDAC):
    return val*df_calDAC.slope[vfatN]+df_calDAC.intercept[vfatN]
for oh in df_summary.oh.unique():
    sel=df_summary.oh==oh
    df_sel=df_summary[sel].copy()
    if df_sel.size<1:
        continue
    sel2=df_calDAC.oh==oh
    df_cal=df_calDAC[sel2][["vfat","cal-dac-m","cal-dac-b"]].copy().rename(columns={"vfat":"vfat","cal-dac-m":"slope","cal-dac-b":"intercept"}).reset_index(drop=True)
    dfs_vfatsel=[]
    for vfatN in df_sel.vfatN.unique():
        sel=df_sel.vfatN==vfatN
        df_vfatsel=df_sel[sel].copy()

        print( df_cal[df_cal['vfat'] == int(vfatN) ]['slope'] )
        idx = df_cal[df_cal['vfat'] == int(vfatN)].index.tolist()[0]
        df_vfatsel.loc[:,'meanfC']=df_sel['mean']*df_cal.slope[idx]+df_cal.intercept[idx]
        df_vfatsel.loc[:,'sigmafC']=df_sel['sigma']*abs(df_cal.slope[idx])
        dfs_vfatsel.append(df_vfatsel)
        #print(f"VFAT {int(vfatN)} noise {df_vfatsel['sigma'].mean():1.2f} DAC units or {df_vfatsel['sigmafC'].mean():1.2f} fC, THR_ARM_DAC {int(20*df_vfatsel['sigma'].mean())}, Mean DAC, {df_vfatsel['mean'].mean()}, Mean fC, {df_vfatsel['meanfC'].mean()}")
        sel2=df_vfatsel['sigmafC']>2
        df_noisy=df_vfatsel[sel2]
        print ("VFAT {int(vfatN)}")
        print(df_noisy)
    df_sel=pd.concat(dfs_vfatsel)
    sns.boxplot(df_sel['vfatN'].astype(int),df_sel['sigmafC'], color='yellow')

    plt.xlabel('vfat Number',fontsize=20)
    plt.xticks(fontsize=16)
    plt.ylabel('Noise [fC]', fontsize=20)
    plt.ylim(0,2)
    plt.yticks(fontsize=16)
    plt.savefig(output_dir / f"Noise_OH{oh}.png")
    plt.clf()

    if args.thresholds:
        myplot ={"x":[],"y":[]}
        df_thresholds = pd.read_csv(args.thresholds, sep=";")
        # print("Noise\n", df_sel)

        for oh in df.oh.unique():
            for vf in df[df["oh"]==oh]["vfatN"].unique():
                ENC = df[(df["oh"]==oh) & (df["vfatN"]==vf)]["sigma"].mean()
                THR = df_thresholds[ (df_thresholds["oh"]==oh) & (df_thresholds["vfat"]==vf)]["threshold"].iloc[0]
                
                if int(THR)!=0:
                    myplot["x"].append(ENC)
                    myplot["y"].append(THR)

        fig, ax = plt.subplots(1, 1)
        print(myplot["x"],myplot["y"])
        ax.plot(myplot["x"],myplot["y"])
        ax.set_xlabel("SCurve ENC (fC)")
        ax.set_ylabel("SBitTHR (DAC)")
        fig.savefig(output_dir/ f"THR_Extrapolation_{oh}.png")


#sns.boxplot(df_sel['vfatN'].astype(int),df_sel['meanfC'], color='yellow')
#plt.ylabel('Threshold [fC]', fontsize=20)
#plt.savefig("Threshold_OH%i.png"%(oh))
#plt.clf()

