import os, sys, pathlib

import time
import datetime
import threading

import pandas as pd
import copy
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# status flags:
running = False
saving = False
stopping = False

daq_threads = list()

OUTPUT_DIR = pathlib.Path("scurve/static/results/")
NOISE_CHECK_SLEEP = 0.001
NInj = 200

fpga_prefix = {
    "ge21": "BEFE.GEM.OH.OH{}.FPGA.TRIG.CTRL.",
    "me0": "BEFE.GEM.OH_LINKS.OH{}."
}
lib_paths = {
    "ge21": "/home/gempro/testbeam/july2022/install-dev/ge21/lib64/",
    "me0": "/home/gempro/testbeam/july2022/install-dev/me0/lib64/"
}

scurve_output = list()

def stop():
    global running, saving, stopping

    stopping = True
    running = False
    time.sleep(1)
    saving = False

    for t in daq_threads: t.join()
    print("All threads stopped")
    stopping = False

def launch_scurve(block, oh, vfats):
    global running

    running = True
    scurve_output.clear()
   
    scurve_lock = threading.Lock()

    # start scan in separate thread
    scurve_thread = threading.Thread(target=run_scurve, args=[block, oh, vfats, scurve_lock])
    daq_threads.append(scurve_thread)
    scurve_thread.start()

    # start analysis in separate thread
    analysis_thread = threading.Thread(target=analyze_scurve, args=[oh, scurve_lock])
    daq_threads.append(analysis_thread)
    analysis_thread.start()

def run_scurve(block, oh, vfats, lock, dry=False):

    global running, stopping
   
    print(f"Starting scurve. Running is {running}")

    #file=open("outputfile_scurve_%s_%i-%i.txt"%(chambername,vfatMin,vfatMax),"w+")                                                                                                   
    #file.write("oh,vfat,ch,charge,fired,events\n")
   
    # import libraries for correct block
    sys.path.append(lib_paths[block])
    import gempy

    if dry:
        # test run, generate random pulses
        threshold = 100
        for ch in range(128):
            #print("Emulating channel", ch)
            for charge in range(0, 256, 1):
                for vfat in vfats:
                    fireEv = 100
                    responseAnalog = np.random.normal(255 - charge, 2, fireEv) + np.random.normal(0, 5, fireEv)
                    responseDigital = responseAnalog > threshold
                    goodEv = responseDigital.sum() # count only events with value 1
                    with lock:
                        scurve_output.append( (oh, vfat, ch, charge, fireEv, goodEv) )
                    time.sleep(2e-6)
                    if stopping:
                        print("Stopping scurve scan.")
                        return
            time.sleep(10e-3)
        print(f"Finished scurve. Running is {running}")
        running = False
        print(f"And now it is {running}")
        return


    # prepare TTC generator
    gempy.writeReg("BEFE.GEM.SLOW_CONTROL.SCA.CTRL.MODULE_RESET", 0x1)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.ENABLE", 0x1)
    gempy.writeReg("BEFE.GEM.SLOW_CONTROL.SCA.CTRL.TTC_HARD_RESET_EN", 0x0)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.SINGLE_HARD_RESET", 0x1)
    time.sleep(0.15)

    # reset all VFATs
    gempy.writeReg("BEFE.GEM.GEM_SYSTEM.CTRL.LINK_RESET", 1)
    time.sleep (0.1)
    gempy.writeReg("BEFE.GEM.GEM_SYSTEM.VFAT3.SC_ONLY_MODE", 1)

    # configure and enable TTC generator
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.RESET",  1)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.ENABLE", 1)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP", 50)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_L1A_GAP",  500)
    gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_L1A_COUNT",  NInj)

    gempy.writeReg("BEFE.GEM.TRIGGER.SBIT_MONITOR.OH_SELECT", oh)
  
    # configure VFATs for pulsing
    for vfat in vfats:
        sync_errors = gempy.readReg("BEFE.GEM.OH_LINKS.OH{}.VFAT{}.SYNC_ERR_CNT".format(oh, vfat))
        if sync_errors > 0:
            print ("Link errors.. exiting")
            raise ValueError("{} sync errors in OH {}, VFAT {}".format(sync_errors, oh, vfat))
        
        gempy.writeReg((fpga_prefix[station]+"VFAT_MASK").format(oh, 0xffffff ^ (1 << vfat) ))

        for i in range(128):
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.CALPULSE_ENABLE".format(oh,vfat,i), 0)
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.MASK".format(oh,vfat,i), 1)

        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_THR_ARM_DAC".format(oh, vfat), 100) 
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_PULSE_STRETCH".format(oh, vfat), 7)
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_SEL_POL".format(oh, vfat), 0)
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_SEL_COMP_MODE".format(oh, vfat), 0) 
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_LATENCY".format(oh, vfat), 43)                                                   
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_SEL_POL".format(oh, vfat), 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_PHI".format(oh, vfat), 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_EXT".format(oh, vfat), 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_DAC".format(oh, vfat), 50)                                                   
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_MODE".format(oh, vfat), 1)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_FS".format(oh, vfat), 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_DUR".format(oh, vfat), 250) 
        gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_RUN".format(oh, vfat), 1)
        gempy.writeReg("BEFE.GEM.GEM_SYSTEM.VFAT3.SC_ONLY_MODE", 0)


    # set up monitor
    gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE", 1)
    gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_GLOBAL_OR", 0)
    
    # start scan 
    for ch in range(128):
        print("Enabling oh", oh, "vfat", vfat, "channel", ch)
        
        # enable channel and select for calpulse:
        gempy.writeReg("BEFE.GEM.SLOW_CONTROL.SCA.MANUAL_CONTROL.LINK_ENABLE_MASK", 0x1<<oh)
        for vfat in vfats:
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.CALPULSE_ENABLE".format(oh,vfat,ch), 1)
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.MASK".format(oh,vfat,ch), 0)
        gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.OH_SELECT", oh)
        gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_SELECT", ch)

        # inject calibration pulse
        for charge in range(0, 256, 1):
            for vfat in vfats:
                gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.CFG_CAL_DAC".format(oh, vfat), charge)
            gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.RESET", 1)
            gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE", 1)
            gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_START", 1)
            while gempy.readReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_RUNNING"): time.sleep(0.001)
            gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE", 0)
            for vfat in vfats:
                if stopping:
                    print("Stopping scurve scan.")
                    return
                goodEv = gempy.readReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT{}.GOOD_EVENTS_COUNT".format(vfat))
                fireEv = gempy.readReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT{}.CHANNEL_FIRE_COUNT".format(vfat))
                with lock: scurve_output.append( (oh, vfat, ch, charge, fireEv, goodEv) ) 
        
        # disable calpulse
        for vfat in vfats:
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.CALPULSE_ENABLE".format(oh,vfat,ch), 0)
            gempy.writeReg("BEFE.GEM.OH.OH{}.GEB.VFAT{}.VFAT_CHANNELS.CHANNEL{}.MASK".format(oh,vfat,ch), 1)

    running = False

def analyze_scurve(oh, lock):

    global saving, stopping

    last_iteration = False
    print(f"Starting continuous analysis. running is {running}")
    while running or not last_iteration:

        if not running: last_iteration = True

        df_database = pd.read_csv("/home/gempro/all_vfats.csv", sep=";")
        df_mapping = pd.read_csv("/home/gempro/vfat_mapping.csv", sep=";")
        df_calibration = df_mapping.join(df_database.set_index("chip-id"), on="chip-id")

        df_calibration = df_calibration[["oh","vfat","cal-dac-m","cal-dac-b"]].copy().rename(columns={"oh":"oh","vfat":"vfat","cal-dac-m":"slope","cal-dac-b":"intercept"}).reset_index(drop=True)
        df_calibration.set_index("vfat", inplace=True, drop=False)#, verify_integrity=True)

        nrows, ncols = 3, 4
        summary_fig, summary_axs = plt.subplots(nrows, ncols, figsize=(9*ncols, 9*nrows))
        summary_axs = summary_axs.flat

        plt.figure(figsize=(9,9))
        cmap_new = mpl.cm.get_cmap("viridis")
        cmap_new.set_under("w")
        #cmap_new = mpl.cm.get_cmap("viridis")
        my_norm = mpl.colors.Normalize(vmin=.25, vmax=100, clip=False)

        def plot_scurve(vfat_df):
            vfat = vfat_df["vfat"].iloc[0]
            vfat_df = scurve_df[scurve_df["vfat"]==vfat]
            #df_sel=df[sel].copy()

            # calibrate charge in fC
            vfat_calibration = df_calibration[df_calibration.vfat==vfat]
            slope = vfat_calibration["slope"].iloc[0]
            intercept = vfat_calibration["intercept"].iloc[0]
            vfat_df["fC"] = vfat_df["charge"] * slope + intercept
            
            plt.clf()
            summary_img = summary_axs[vfat].scatter(
                vfat_df["ch"], vfat_df["fC"],
                c=vfat_df["fired"], cmap=cmap_new, norm=my_norm, s=2
            )
            #charge, fired = vfat_df[vfat_df["ch"]==0]["fC"], vfat_df[vfat_df["ch"]==0]["fired"]
            ##summary_axs[vfat].plot(charge, fired)
            summary_axs[vfat].set_title(f"OH {oh}, VFAT {vfat}", fontsize=20)
            summary_axs[vfat].set_xlabel("VFAT channel", fontsize=20)
            summary_axs[vfat].set_ylabel("Calibration charge (fC)", fontsize=20)
           
        with lock: scurve_df = pd.DataFrame(scurve_output, columns="oh,vfat,ch,charge,events,fired".split(","))
        scurve_df.groupby("vfat").apply(plot_scurve)
       
        saving = True
        output_file = OUTPUT_DIR / f"summary.png"
        print(f"Saving to {output_file}, running is {running}")
        scurve_df.to_csv(OUTPUT_DIR / f"scurve.csv")
        summary_fig.tight_layout()
        summary_fig.savefig(output_file)
        saving = False

        if stopping:
            print("Stopping scurve analysis.")
            return

        if last_iteration: # move output files away
            write_time = datetime.datetime.now()
            write_timestamp = write_time.strftime("%Y%m%d_%H%M")
            os.rename(OUTPUT_DIR / f"scurve.csv", OUTPUT_DIR / f"scurve_{write_timestamp}.csv")
            output_file_final = OUTPUT_DIR / f"Summary_{write_timestamp}.png"
            os.rename(output_file, output_file_final)
            print(f"Moved {output_file} to {output_file_final}.")

        time.sleep(1)

if __name__ == "__main__":
    main()
