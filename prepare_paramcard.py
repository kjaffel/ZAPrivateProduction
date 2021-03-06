#!/bin/env python
import os
import math
import json
import shutil
import stat
import argparse, optparse
from cp3_llbb.Calculators42HDM.Calc2HDM import *

import logging
LOG_LEVEL = logging.DEBUG
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
logger = logging.getLogger("run2UL param_card for HToZATo2L2B")
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)
try:
    import colorlog
    from colorlog import ColoredFormatter
    LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    formatter = ColoredFormatter(LOGFORMAT)
    stream.setFormatter(formatter)
except ImportError:
    pass

if "CMSSW_BASE" not in os.environ:
    raise RuntimeError("This script needs to be run in a CMSSW environment, with cp3_llbb/Calculators42HDM set up")
CMSSW_Calculators42HDM = os.path.join(os.environ["CMSSW_BASE"], "src", "cp3_llbb", "Calculators42HDM")

def mass_to_string(m):
    r = '{:.2f}'.format(m)
    r = r.replace('.', 'p')
    return r

def call_Calculators42HDM(mH=None, mA=None, mh=None, mhc=None, tb=None):
    type = 2
    sqrts = 13000
    cba = 0.01  
    alpha=math.atan(tb)-math.acos(cba)
    sinbma = math.sin(math.atan(tb)-alpha)
    m12 = math.sqrt(pow(mhc, 2) * tb / (1 + pow(tb, 2)))
    BRdict = {
            'BRhtoss': [],
            'BRhtocc': [],
            'BRhtobb': [],
            'BRhtoee': [],
            'BRhtomumu': [],
            'BRhtotautau': [],
            'BRhtogg': [],
            'BRhtoZZ': [],
            'BRhtoWW': [],
            'BRhtoZga': [],
            'BRhtogluglu': [],}

    outputFile = 'out_param_card_{}_{}_{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string( tb))
    cwd = os.getcwd()
    #os.chdir(os.path.join(CMSSW_Calculators42HDM, 'out'))
    os.chdir(CMSSW_Calculators42HDM)
    
    if mA > mH:
        logger.info("MA_{} > MH_{} switching to A->ZH mode!".format(mA, mH))
        mode = 'A'
    elif mH >= mA and mH> 125.:
        logger.info("MA_{} =< MH_{} switching to H->ZA mode!".format(mA, mH))
        mode = 'H'
    elif mH >= mA and mH <= 125.:
        logger.info("MA_{} >= MH_{} && H <= 125. GeV switching to h->ZH mode!".format(mA, mH))
        mode ='h'

    res = Calc2HDM(mode = mode, sqrts = sqrts, type = type,
                               tb = tb, m12 = m12, mh = mh, mH = mH, mA = mA, mhc = mhc, sba = sinbma,
                                                  outputFile = outputFile, muR = 9.118800e+01, muF = 9.118800e+01)
    res.setpdf('NNPDF31_nnlo_as_0118_nf_4_mc_hessian')
    res.computeBR()
    if mH == 466.187600 and mA==375.000000 and tb ==20. :
        xsec_ggH, err_integration_ggH, err_muRm_ggH, err_muRp_ggH, xsec_bbH, err_integration_bbH =  res.getXsecFromSusHi() 

    l2 = float(res.lambda_2)
    l3 = float(res.lambda_3)
    lR7 = float(res.lambda_7)
    wh3tobb = res.wh3tobb
    wh3tot = float(res.Awidth)
    
    BRdict['BRhtoss'].append(res.htossBR)
    BRdict['BRhtocc'].append(res.htoccBR)
    BRdict['BRhtobb'].append(res.htobbBR)
    BRdict['BRhtoee'].append(res.htoeeBR)
    BRdict['BRhtomumu'].append(res.htomumuBR)
    BRdict['BRhtotautau'].append(res.htotautauBR)
    BRdict['BRhtogg'].append(res.htoggBR) # gamma-gamma
    BRdict['BRhtoZZ'].append(res.htoZZBR)
    BRdict['BRhtoWW'].append(res.htoWWBR)
    BRdict['BRhtoZga'].append(res.htoZgaBR)
    BRdict['BRhtogluglu'].append(res.htoglugluBR)

    os.chdir(cwd) 
    # mv these file in the end , otherwise Calc2HDM won't run properly 
    shutil.move(os.path.join(CMSSW_Calculators42HDM, outputFile), os.path.join('./widths_crosschecks/run_2hdmc180/', outputFile))
    shutil.move(os.path.join(CMSSW_Calculators42HDM, outputFile.replace('.dat', '.log')), os.path.join('./widths_crosschecks/run_2hdmc180/', outputFile.replace('.dat', '.log')))
    return l2, l3, lR7, wh3tot, wh3tobb, sinbma, BRdict

def call_BottomYukawacoupling(mh3=None, tanbeta=None, wh3tobb=None):
    id = 36
    MB = 4.75 # mb pole mass
    aEWM1= 127.9
    aEW = 1./aEWM1
    Gf = 1.166390e-05

    MZ= 9.118760e+01
    MW= math.sqrt(MZ**2/2. + math.sqrt(MZ**4/4. - (aEW*math.pi*MZ**2)/(Gf*math.sqrt(2))))

    ee = 2*math.sqrt(aEW)*math.sqrt(math.pi)
    sw2 = 1 - MW**2/MZ**2
    sw = math.sqrt(sw2)

    vev = (2*MW*sw)/ee
    TH3x3 = 1.
    const2 = (8.*math.pi*vev**2*abs(mh3)**3)
    const1 = (3*mh3**2*tanbeta**2*TH3x3**2*math.sqrt(-4*MB**2*mh3**2 + mh3**4))

    ymb = math.sqrt((const2 * wh3tobb)/const1)
    yb = ((ymb*math.sqrt(2))/vev)
    
    recalculated_width= (MB**2 *const1)/const2
    width_in_the_banner = wh3tobb
    relative_diff=abs(recalculated_width-width_in_the_banner)/recalculated_width
    if (relative_diff > 0.05):
        logger.warning('The LO estimate for the width of particle %s ' % id)
        logger.warning('will differs from the one in the banner by %d percent ' % (relative_diff*100))
    return ymb

def prepare_param_cards(mH=None, mA=None, mh=None, mhc=None, MB=None, l2=None, l3=None, lR7=None, sinbma=None, tb=None, ymb=None, carddir=None, template=None, cardname=None, pass_ymbandmb_toparamcards=False):
    
    if carddir==None:
        carddir = './widths_crosschecks/{}/inputs'.format('run_afterYukawaFix' if pass_ymbandmb_toparamcards else('run_beforeYukawaFix') )
    if cardname==None:
        cardname= "in_param_card_{}_{}_{}.dat".format(mass_to_string(mH), mass_to_string(mA), mass_to_string(tb))
    if template==None:
        template= os.path.join('widths_crosschecks', 'template_param_card.dat')
    
    if not os.path.exists(carddir):
        os.makedirs(carddir)
        
    with open(template, 'r') as inf:
        with open(os.path.join(carddir, cardname), 'w+') as outf:
            for line in inf:
                # BLOCK MASS #
                if " MB " in line and pass_ymbandmb_toparamcards:
                    outf.write('    5 {}   # MB\n'.format(MB))
                elif "mhc" in line and pass_ymbandmb_toparamcards:
                    outf.write('   37 {:.6f}   # mhc\n'.format(mhc))
                # BLOCK YUKAWA # 
                elif "ymb" in line and pass_ymbandmb_toparamcards:
                    outf.write('    5 {:.8f}   # ymb\n'.format(ymb))
                # BLOCK FRBLOCK # 
                elif "tanbeta" in line:
                    outf.write('    1 {:.6f}   # tanbeta\n'.format(tb))
                elif "sinbma" in line:
                    outf.write('    2 {:.8f}   # sinbma\n'.format(sinbma))
                # BLOCK HIGGS # 
                elif "l2" in line:
                    outf.write('    1 {:.6f}   # l2\n'.format(l2))
                elif "l3" in line:
                    outf.write('    2 {:.6f}   # l3\n'.format(l3))
                elif "lR7" in line:
                    outf.write('    3 {:.6f}   # lR7\n'.format(lR7))
                # BLOCK MASS #
                elif "mh1" in line:
                    outf.write('   25 {:.6f}   # mh1\n'.format(mh))
                elif "mh2" in line:
                    outf.write('   35 {:.6f}   # mh2\n'.format(mH))
                elif "mh3" in line:
                    outf.write('   36 {:.6f}   # mh3\n'.format(mA))
                else:
                    outf.write(line)
    return

def prepare_computewidths_script(run_beforeYukawaFix=False, run_afterYukawaFix=False):
    with open('run_madwidths.sh', 'w+') as outf:
        outf.write('import model 2HDMtII_NLO\n')
        
        mh3=125.
        mh=125.
        MZ= 9.118760e+01
        MB= 4.75
        while mh3 < 1500.:
            mH= mh3+MZ
            mA= mh3
            mhc=max(mH, mA)
            for tb in [1.5, 20.]:
                l2, l3, lR7, wh3tot, wh3tobb, sinbma, BRdict= call_Calculators42HDM( mH, mA, mh, mhc, tb)
                ymb = call_BottomYukawacoupling(mA, tb, wh3tobb)
               
                if run_afterYukawaFix:
                    prepare_param_cards(mH, mA, mh, mhc, MB, l2, l3, lR7, sinbma, tb, ymb, pass_ymbandmb_toparamcards=True)
                    inputsfiles= './widths_crosschecks/run_afterYukawaFix/inputs/in_param_card_{}_{}_{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string(tb))
                    outputsfiles= './widths_crosschecks/run_afterYukawaFix/outputs/out_param_card_{}_{}_{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string(tb))
                    outf.write('compute_widths h1 h2 h3 --path={} --output={} --body_decay=2\n'.format(inputsfiles, outputsfiles))
                    #outf.write('compute_widths h1 h2 h3 --path={} --output={}\n'.format(inputsfiles, outputsfiles))
                if run_beforeYukawaFix:
                    prepare_param_cards(mH, mA, mh, mhc, MB, l2, l3, lR7, sinbma, tb, ymb, pass_ymbandmb_toparamcards=False)
                    inputsfiles= './widths_crosschecks/run_beforeYukawaFix/inputs/in_param_card_{}_{}_{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string(tb))
                    outputsfiles= './widths_crosschecks/run_beforeYukawaFix/outputs/out_param_card_{}_{}_{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string(tb))
                    outf.write('compute_widths h1 h2 h3 --path={} --output={} --body_decay=2\n'.format(inputsfiles, outputsfiles))
                    #outf.write('compute_widths h1 h2 h3 --path={} --output={} \n'.format(inputsfiles, outputsfiles))
            mh3 += 50.
    os.chmod('run_madwidths.sh', os.stat('run_madwidths.sh').st_mode | stat.S_IXUSR)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Prepare Param cards', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--run_beforeYukawaFix', action='store_true', help=' Yukawa coupling == MB == 4.7 GeV')
    parser.add_argument('--run_afterYukawaFix', action='store_true', help='compute yukawa coupling and propagate the values to the param_cards')
    options = parser.parse_args()    
    prepare_computewidths_script(run_beforeYukawaFix= options.run_beforeYukawaFix, run_afterYukawaFix=options.run_afterYukawaFix)
