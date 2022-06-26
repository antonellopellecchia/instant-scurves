import sys
import array
import struct
import pathlib
from time import *
#sys.path.append("/home/gempro/cmsgemos/gemhardware/_build/_install/lib64/gem")
#sys.path.append("/home/gempro/cmsgemos-ge210/gemhardware/_build/_install/lib64/gem")
import gempy


NOISE_CHECK_SLEEP = 0.001
NInj = 200

fpga_prefix = {
    "ge21": "BEFE.GEM.OH.OH%i.FPGA.TRIG.CTRL.",
    "me0": "BEFE.GEM.OH_LINKS.OH%i."
}

def configureVfatForPulsing(vfatN, ohN, station,trimming=None):

        gempy.writeReg("BEFE.GEM.GEM_SYSTEM.CTRL.LINK_RESET", 1)

        sleep (0.1)

        gempy.writeReg("BEFE.GEM.GEM_SYSTEM.VFAT3.SC_ONLY_MODE", 1)

        if (int(gempy.readReg("BEFE.GEM.OH_LINKS.OH%i.VFAT%i.SYNC_ERR_CNT"%(ohN,vfatN))) > 0):
            print ("\tLink errors.. exiting")


           #Configure TTC generator on CTP7
        gempy.writeReg("BEFE.GEM.TTC.GENERATOR.RESET",  1)
        gempy.writeReg("BEFE.GEM.TTC.GENERATOR.ENABLE", 1)
        gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_CALPULSE_TO_L1A_GAP", 50)
        gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_L1A_GAP",  500)
        gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_L1A_COUNT",  NInj)

        gempy.writeReg("BEFE.GEM.TRIGGER.SBIT_MONITOR.OH_SELECT", ohN)

        gempy.writeReg((fpga_prefix[station]+"VFAT_MASK") % ohN, 0xffffff ^ (1 << (vfatN)))

        print ("Configure VFAT")

        for i in range(128):
                gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.CALPULSE_ENABLE"%(ohN,vfatN,i),0)
                gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.MASK"%(ohN,vfatN,i),1)
                if trimming is not None:
                    # set trim amplitude and polarity:
                    trim_amplitude, trim_polarity = abs(trimming), int(trimming<0)
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.ARM_TRIM_AMPLITUDE"%(ohN,vfatN,i),trim_amplitude) 
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.ARM_TRIM_POLARITY"%(ohN,vfatN,i),trim_polarity)

        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_THR_ARM_DAC"       % (ohN , vfatN) , 100) 
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_PULSE_STRETCH"       % (ohN , vfatN) , 7)
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_SEL_POL"             % (ohN , vfatN) , 0)
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_SEL_COMP_MODE"       % (ohN , vfatN) , 0) 
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_LATENCY"             % (ohN , vfatN) , 43)                                                   
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_SEL_POL"         % (ohN , vfatN) , 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_PHI"             % (ohN , vfatN) , 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_EXT"             % (ohN , vfatN) , 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_DAC"             % (ohN , vfatN) , 50)                                                   
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_MODE"            % (ohN , vfatN) , 1)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_FS"              % (ohN , vfatN) , 0)                                                    
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_DUR"             % (ohN , vfatN) , 250) 
        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_RUN"%(ohN,vfatN), 1)
        gempy.writeReg("BEFE.GEM.GEM_SYSTEM.VFAT3.SC_ONLY_MODE", 0)


def main():                                                                                                                                                
    
    import argparse
    parser = argparse.ArgumentParser("Scurve analysis")
    parser.add_argument("oh", type=int, nargs="+", help="OptoHybrid number(s)")
    parser.add_argument("chambername", type=str, help="Chamber label")
    parser.add_argument("--range", dest="vfatRange", type=int, nargs="+", default=None, help="VFAT range")
    parser.add_argument("--vfats", type=int, nargs="+", default=None, help="VFAT list")
    parser.add_argument("--exclude", type=int, nargs="+", default=None, help="Excluded VFAT list")
    parser.add_argument("--trimming", type=int, default=None, help="Trimming value")
    parser.add_argument("--me0", action="store_true", help="Run on ME0")
    args = parser.parse_args()


    print(args)
    if args.me0: station = "me0"
    else: station = "ge21"

    if args.trimming: print("Scurve with trimming value", args.trimming)
   
    ohList = args.oh
    chambername = args.chambername

    vfatRange = args.vfats
    if not vfatRange:
        vfatRange = list(range(args.vfatRange[0], args.vfatRange[1]+1))
    if args.exclude:
        for excludedVfat in args.exclude: vfatRange.remove(excludedVfat)

    vfatNMin, vfatNMax = vfatRange[0], vfatRange[-1]
    #if ohN > 11:
    #    printRed("The given OH index (%d) is out of range (must be 0-11)" % ohN)
    #    return
    if vfatNMin > 23:
        printRed("The given VFAT index (%d) is out of range (must be 0-23)" % vfatN)
        return
    if vfatNMax > 23:
        printRed("The given VFAT index (%d) is out of range (must be 0-23)" % vfatN)
        return
    
    verbose = 0
    if (vfatNMin == vfatNMax):
        verbose = 1
   
    print(vfatRange)
    
    ##################
    # hard reset
    ##################

    file=open('outputfile_scurve_%s_%i-%i.txt'%(chambername,vfatNMin,vfatNMax),'w+')                                                                                                   
    file.write("oh,vfatN,ch,charge,fired,events\n")


    gempy.writeReg('BEFE.GEM.SLOW_CONTROL.SCA.CTRL.MODULE_RESET', 0x1)
    #gempy.writeReg('BEFE.GEM.SLOW_CONTROL.SCA.MANUAL_CONTROL.LINK_ENABLE_MASK', 0x1<<ohN)
    gempy.writeReg('BEFE.GEM.TTC.GENERATOR.ENABLE', 0x1)
    gempy.writeReg('BEFE.GEM.SLOW_CONTROL.SCA.CTRL.TTC_HARD_RESET_EN', 0x0)

    gempy.writeReg('BEFE.GEM.TTC.GENERATOR.SINGLE_HARD_RESET', 0x1)
    sleep(0.15)
    
    print ("Configure VFATs\n")
    for ohN in ohList:
        for vfatN in vfatRange:
            print (ohN,vfatN)
            configureVfatForPulsing(vfatN, ohN, station, args.trimming)


    print ("Set up DAQ monitor\n")                                                                                                                        

    gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE",    1)
    #gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.OH_SELECT", ohN)
    gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_GLOBAL_OR", 0)
    
    for ch in range(128):
        for ohN in ohList:
            print("Enabling oh", ohN, "vfat", vfatN, "channel", ch)
            gempy.writeReg('BEFE.GEM.SLOW_CONTROL.SCA.MANUAL_CONTROL.LINK_ENABLE_MASK', 0x1<<ohN)
            for vfatN in vfatRange:
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.CALPULSE_ENABLE"%(ohN,vfatN,ch),1)
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.MASK"%(ohN,vfatN,ch),0)
            gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.OH_SELECT", ohN)
            gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.VFAT_CHANNEL_SELECT",ch)
            for charge in range(0,256,1):
                #print ("Charge: %i"%charge)
                for vfatN in vfatRange:
                        gempy.writeReg("BEFE.GEM.OH.OH%i.GEB.VFAT%i.CFG_CAL_DAC"             % (ohN , vfatN) , charge)
                gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.RESET",     1)
                gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE",    1)
                gempy.writeReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_START", 1)
                while gempy.readReg("BEFE.GEM.TTC.GENERATOR.CYCLIC_RUNNING"):
                      sleep(0.001)
                #sleep(0.02)
                gempy.writeReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.CTRL.ENABLE",    0)
                for vfatN in vfatRange:
                    goodEv = gempy.readReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%i.GOOD_EVENTS_COUNT"%vfatN)
                    fireEv = gempy.readReg("BEFE.GEM.GEM_TESTS.VFAT_DAQ_MONITOR.VFAT%i.CHANNEL_FIRE_COUNT"%vfatN)
                    file.write("%i,%i,%i,%i,%i,%i\n"%(ohN,vfatN,ch,charge,fireEv,goodEv))      
            for vfatN in vfatRange:
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.CALPULSE_ENABLE"%(ohN,vfatN,ch),0)
                    gempy.writeReg("BEFE.GEM.OH.OH%d.GEB.VFAT%d.VFAT_CHANNELS.CHANNEL%i.MASK"%(ohN,vfatN,ch),1)
    file.close()
    print("")
    print("bye now..")

if __name__ == "__main__":
    main()
