import os
import json
import time
import requests
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'market_db.json')
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')

def update_progress(percent, status, extra_data=None):
    data = {"percent": percent, "status": status}
    if extra_data:
        data.update(extra_data)
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

def fetch_yahoo_chart(ticker, range_str="5y"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "range": range_str,
        "interval": "1d",
        "events": "div,split"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return None
        data = response.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return None
        
        res = result[0]
        timestamps = res.get("timestamp", [])
        quotes = res.get("indicators", {}).get("quote", [{}])[0]
        closes = quotes.get("close", [])
        
        history = {}
        for ts, close in zip(timestamps, closes):
            if ts and close is not None:
                date_str = pd.to_datetime(ts, unit='s').strftime('%Y-%m-%d')
                history[date_str] = float(close)
        return history
    except Exception:
        return None

def download_data():
    market_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
        except Exception:
            market_data = {}

    # Mercato USA completo (S&P 500 & NASDAQ 100 integrati)
    tickers_us = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
        'XOM', 'JPM', 'V', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'PEP',
        'KO', 'AVGO', 'COST', 'TMO', 'MCD', 'CSCO', 'ABT', 'WMT', 'ACN', 'DHR',
        'LIN', 'DIS', 'NKE', 'ADBE', 'VZ', 'TXN', 'PM', 'NEE', 'RTX', 'QCOM',
        'AMGN', 'HON', 'IBM', 'INTC', 'SBUX', 'CAT', 'GE', 'DE', 'LOW', 'SPGI',
        'AMD', 'LMT', 'PLD', 'ISRG', 'BKNG', 'GILD', 'ADI', 'C', 'MDLZ', 'TJX',
        'ZTS', 'MU', 'LRCX', 'PANW', 'SNPS', 'CDNS', 'SO', 'DUK', 'CL', 'ITW',
        'BSX', 'PGR', 'CI', 'MO', 'BDX', 'EQIX', 'CB', 'SLB', 'SHW',
        'ETN', 'ICE', 'CME', 'NSC', 'CSX', 'HUM', 'WM', 'FCX', 'USB', 'PNC',
        'TGT', 'NOC', 'GD', 'CLX', 'AON', 'IT', 'EMR', 'EOG', 'PSX', 'VLO',
        'PYPL', 'NFLX', 'INTU', 'AMAT', 'BK', 'BLK', 'AXP', 'BA', 'MMM', 'CHTR',
        'PLTR', 'UBER', 'ABNB', 'SNOW', 'CRWD', 'DDOG', 'NET', 'TEAM', 'SHOP', 'SQ',
        'COIN', 'ROKU', 'ZM', 'DOCU', 'PTON', 'TWLO', 'MRNA', 'BNTX', 'PFE', 'LLY',
        'TMUS', 'T', 'CMCSA', 'PARA', 'WBD', 'FOXA', 'EA', 'TTWO', 'RBLX', 'DKNG',
        'WYNN', 'LVS', 'MGM', 'MAR', 'HLT', 'DAL', 'UAL', 'AAL', 'LUV', 'GM',
        'F', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'SNAP', 'PINS', 'SPOT', 'HOOD',
        'ORCL', 'CRM', 'NOW', 'REGN', 'VRTX', 'FISV', 'ADSK', 'MNST', 'O', 'KDP',
        'AZN', 'NVO', 'ASML', 'SHEL', 'TTE', 'BP', 'BHP', 'RY', 'TD', 'HDB',
        'SNY', 'GSK', 'MELI', 'PDD', 'JD', 'BIDU', 'BABA', 'TSM', 'NICE',
        # Intero S&P 500 / Liquid US Stocks
        'A', 'AAP', 'ABAC', 'ABCB', 'ACGL', 'ACM', 'ADC', 'ADM', 'ADP', 'AEE',
        'AEP', 'AES', 'AFL', 'AIG', 'AIZ', 'AJG', 'AKAM', 'ALB', 'ALGN', 'ALK',
        'ALL', 'ALLE', 'AMCR', 'AME', 'AMP', 'AMT', 'ANET', 'ANSS', 'AOS', 'APA',
        'APD', 'APH', 'APTV', 'ARE', 'ATO', 'AVB', 'AVY', 'AWK', 'AXON', 'AZO',
        'BAC', 'BALL', 'BAX', 'BBY', 'BEN', 'BF-B', 'BG', 'BIIB', 'BIO', 'BKR',
        'BLDR', 'BMY', 'BR', 'BRO', 'BWA', 'BX', 'BXP', 'CAG', 'CAH', 'CARR',
        'CBOE', 'CBRE', 'CCI', 'CCL', 'CDW', 'CE', 'CEG', 'CF', 'CFG', 'CHD',
        'CHRW', 'CINF', 'CMA', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP', 'COF', 'COO',
        'COP', 'COR', 'CPAY', 'CPB', 'CPRT', 'CPT', 'CRL', 'CSX', 'CTAS', 'CTLT',
        'CTRA', 'CTSH', 'CTVA', 'CVS', 'CZR', 'D', 'DAY', 'DD', 'DECK', 'DFS',
        'DG', 'DGX', 'DHI', 'DLR', 'DLTR', 'DOV', 'DOW', 'DPZ', 'DRI', 'DTE',
        'DVA', 'DVN', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EG', 'EIX', 'EL',
        'ELV', 'EMN', 'ENPH', 'EPAM', 'EQR', 'ERIE', 'ES', 'ESS', 'ETR', 'EVRG',
        'EW', 'EXC', 'EXPD', 'EXPE', 'EXR', 'FANG', 'FAST', 'FDS', 'FDX', 'FE',
        'FFIV', 'FI', 'FITB', 'FLT', 'FMC', 'FOX', 'FRT', 'FSLR', 'FTNT', 'FTV',
        'GDDY', 'GEHC', 'GEN', 'GPC', 'GIS', 'GL', 'GLW', 'GNRC', 'GPN', 'GRMN',
        'GS', 'GWW', 'HAL', 'HAS', 'HBAN', 'HCA', 'HES', 'HIG', 'HII', 'HOLX',
        'HPE', 'HPQ', 'HRL', 'HSIC', 'HST', 'HSY', 'HUBB', 'HWM', 'IDXX', 'IEX',
        'IFF', 'ILMN', 'INCY', 'INVH', 'IPG', 'IQV', 'IR', 'IRM', 'IVZ', 'J',
        'JBHT', 'JBL', 'JCI', 'JKHY', 'JNPR', 'K', 'KEY', 'KEYS', 'KHC', 'KIM',
        'KLAC', 'KMB', 'KMI', 'KMX', 'KR', 'KVUE', 'L', 'LDOS', 'LEN', 'LH',
        'LHX', 'LKQ', 'LLY', 'LNT', 'LULU', 'LW', 'LYB', 'LYV', 'MAA', 'MAS',
        'MCHP', 'MCK', 'MDT', 'MET', 'MHK', 'MKC', 'MKTX', 'MLM', 'MMC', 'MOH',
        'MOS', 'MPC', 'MPWR', 'MRSH', 'MS', 'MSCI', 'MSI', 'MTB', 'MTCH', 'MTD',
        'NCLH', 'NDAQ', 'NDSN', 'NEM', 'NI', 'NLOK', 'NOC', 'NRG', 'NTAP', 'NTRS',
        'NUE', 'NVR', 'NXPI', 'ODFL', 'OGN', 'OKE', 'OMC', 'ON', 'ORLY', 'OTIS',
        'OXY', 'PAYC', 'PAYX', 'PCAR', 'PCG', 'PEAK', 'PEG', 'PFG', 'PGR', 'PH',
        'PHM', 'PKG', 'PNR', 'PNW', 'PODD', 'POOL', 'PPG', 'PPL', 'PRU', 'PSA',
        'PTC', 'PWR', 'QRVO', 'RCL', 'REG', 'RF', 'RHI', 'RJF', 'RL', 'RMD',
        'ROK', 'ROL', 'ROP', 'ROST', 'RSG', 'RVTY', 'SBAC', 'SCHW', 'SEDG', 'SEE',
        'SJM', 'SNA', 'SO', 'SRE', 'STE', 'STLD', 'STT', 'STX', 'STZ', 'SWK',
        'SWKS', 'SYF', 'SYK', 'SYY', 'TAP', 'TDG', 'TDY', 'TECH', 'TEL', 'TER',
        'TFC', 'TFX', 'TSCO', 'TSN', 'TT', 'TXT', 'TYL', 'UA', 'UAA', 'UDR',
        'UHS', 'ULTA', 'UNP', 'UPS', 'URI', 'VLO', 'VLTO', 'VMC', 'VRSK', 'VRSN',
        'VST', 'VTR', 'VTRS', 'WAB', 'WAT', 'WBA', 'WDC', 'WEC', 'WELL', 'WFC',
        'WMB', 'WRB', 'WST', 'WTW', 'WY', 'XEL', 'XYL', 'YUM', 'ZBH', 'ZBRA',
        'ZION'
    ]

    # Mercato Italiano completo (FTSE MIB, Mid Cap, Small Cap, Euronext Growth Milan)
    tickers_it = [
        # FTSE MIB
        'A2A.MI', 'AMP.MI', 'AZM.MI', 'BAMI.MI', 'BMED.MI', 'BMPS.MI', 'BPER.MI',
        'ENEL.MI', 'ENI.MI', 'ERG.MI', 'EXOR.AS', 'G.MI', 'HER.MI', 'ISP.MI',
        'LDO.MI', 'MB.MI', 'MONC.MI', 'NEXI.MI', 'PST.MI', 'PRY.MI', 'RACE.MI',
        'SRG.MI', 'STLAM.MI', 'STM.MI', 'TEN.MI', 'TIT.MI', 'TRN.MI', 'UCG.MI',
        'UNI.MI', 'CPR.MI', 'REC.MI', 'SAIPEM.MI',
        # Mid Cap, Small Cap & Growth
        'AEF.MI', 'ARN.MI', 'ANIM.MI', 'ASC.MI', 'AVIO.MI', 'BFF.MI', 'BZU.MI',
        'CMB.MI', 'CEM.MI', 'DEA.MI', 'ELC.MI', 'ENAV.MI', 'FCT.MI', 'FILA.MI',
        'GEO.MI', 'GVS.MI', 'IG.MI', 'IGD.MI', 'ILL.MI', 'INW.MI', 'IP.MI',
        'ITM.MI', 'IVG.MI', 'JUVE.MI', 'LUVE.MI', 'MAIRE.MI', 'MN.MI', 'MOL.MI',
        'OVS.MI', 'REY.MI', 'SAB.MI', 'SL.MI', 'SES.MI', 'SFER.MI', 'SOL.MI',
        'TIP.MI', 'VLS.MI', 'WIIT.MI', 'PRT.MI', 'DANIELI.MI', 'ESPRINET.MI',
        'GEFRAN.MI', 'KME.MI', 'MARR.MI', 'MUTUIONLINE.MI', 'PIAGGIO.MI',
        'RECORDATI.MI', 'TAMBURI.MI', 'VALSOIA.MI', 'ZUCCHI.MI', 'TIS.MI',
        'ERS.MI', 'SESA.MI', 'MONDADORI.MI', 'TCI.MI', 'TME.MI', 'TO.MI',
        'TWO.MI', 'UNIR.MI', 'VNE.MI', 'ABT.MI', 'AC.MI', 'AER.MI', 'AGS.MI',
        'AIFI.MI', 'AL.MI', 'ALD.MI', 'ALFA.MI', 'AM.MI', 'AMB.MI', 'AME.MI',
        'AMR.MI', 'AN.MI', 'ANT.MI', 'AP.MI', 'APL.MI', 'APP.MI', 'APT.MI',
        'AQ.MI', 'AR.MI', 'ARC.MI', 'ARG.MI', 'ARK.MI', 'ARS.MI', 'AS.MI',
        'AST.MI', 'AT.MI', 'ATE.MI', 'ATI.MI', 'ATL.MI', 'ATT.MI', 'AU.MI',
        'AUT.MI', 'AV.MI', 'AX.MI', 'AZ.MI', 'BA.MI', 'BAN.MI', 'BAR.MI',
        'BAT.MI', 'BB.MI', 'BBS.MI', 'BC.MI', 'BCC.MI', 'BCM.MI', 'BD.MI',
        'BE.MI', 'BEN.MI', 'BF.MI', 'BG.MI', 'BGN.MI', 'BH.MI', 'BI.MI',
        'BIC.MI', 'BIN.MI', 'BIO.MI', 'BIT.MI', 'BJ.MI', 'BL.MI', 'BLU.MI',
        'BM.MI', 'BMA.MI', 'BMC.MI', 'BN.MI', 'BO.MI', 'BON.MI', 'BP.MI',
        'BPA.MI', 'BR.MI', 'BRI.MI', 'BS.MI', 'BST.MI', 'BT.MI', 'BU.MI',
        'BUR.MI', 'BV.MI', 'BW.MI', 'BY.MI', 'CA.MI', 'CAD.MI', 'CAI.MI',
        'CAL.MI', 'CAM.MI', 'CAN.MI', 'CAP.MI', 'CAR.MI', 'CAS.MI', 'CAT.MI',
        'CAV.MI', 'CB.MI', 'CBI.MI', 'CC.MI', 'CCE.MI', 'CD.MI', 'CDI.MI',
        'CE.MI', 'CEC.MI', 'CED.MI', 'CF.MI', 'CFI.MI', 'CG.MI', 'CGI.MI',
        'CH.MI', 'CHI.MI', 'CI.MI', 'CIE.MI', 'CIL.MI', 'CIO.MI', 'CIP.MI',
        'CIS.MI', 'CJ.MI', 'CL.MI', 'CLI.MI', 'CM.MI', 'CMI.MI', 'CN.MI',
        'CNI.MI', 'CO.MI', 'COI.MI', 'COL.MI', 'COM.MI', 'CON.MI', 'COO.MI',
        'COP.MI', 'COR.MI', 'COS.MI', 'COT.MI', 'CP.MI', 'CPI.MI', 'CR.MI',
        'CRI.MI', 'CRO.MI', 'CS.MI', 'CSI.MI', 'CT.MI', 'CTI.MI', 'CU.MI',
        'CUI.MI', 'CV.MI', 'CVI.MI', 'CW.MI', 'CY.MI', 'CZ.MI', 'DA.MI',
        'DAL.MI', 'DAN.MI', 'DAV.MI', 'DB.MI', 'DC.MI', 'DD.MI', 'DE.MI',
        'DEC.MI', 'DEL.MI', 'DEN.MI', 'DER.MI', 'DES.MI', 'DEV.MI', 'DF.MI',
        'DG.MI', 'DH.MI', 'DI.MI', 'DIA.MI', 'DIG.MI', 'DIS.MI', 'DJ.MI',
        'DL.MI', 'DM.MI', 'DN.MI', 'DO.MI', 'DOC.MI', 'DOL.MI', 'DOM.MI',
        'DON.MI', 'DP.MI', 'DR.MI', 'DS.MI', 'DT.MI', 'DU.MI', 'DUR.MI',
        'DV.MI', 'DW.MI', 'DY.MI', 'DZ.MI', 'E.MI', 'EA.MI', 'EAT.MI',
        'EB.MI', 'EBR.MI', 'EC.MI', 'ECO.MI', 'ED.MI', 'EDI.MI', 'EE.MI',
        'EF.MI', 'EG.MI', 'EI.MI', 'EIL.MI', 'EL.MI', 'EM.MI', 'EMP.MI',
        'EN.MI', 'EO.MI', 'EP.MI', 'EQ.MI', 'ER.MI', 'ES.MI', 'ET.MI',
        'EU.MI', 'EV.MI', 'EW.MI', 'EX.MI', 'F.MI', 'FA.MI', 'FAB.MI',
        'FAC.MI', 'FAM.MI', 'FAN.MI', 'FAR.MI', 'FAS.MI', 'FAT.MI', 'FB.MI',
        'FC.MI', 'FCI.MI', 'FD.MI', 'FE.MI', 'FEB.MI', 'FEL.MI', 'FEN.MI',
        'FER.MI', 'FF.MI', 'FG.MI', 'FH.MI', 'FI.MI', 'FIE.MI', 'FIN.MI',
        'FIR.MI', 'FIS.MI', 'FIT.MI', 'FJ.MI', 'FL.MI', 'FLI.MI', 'FM.MI',
        'FMI.MI', 'FN.MI', 'FOB.MI', 'FOI.MI', 'FON.MI', 'FOR.MI', 'FP.MI',
        'FR.MI', 'FRI.MI', 'FS.MI', 'FSI.MI', 'FT.MI', 'FU.MI', 'FUL.MI',
        'FV.MI', 'FW.MI', 'FY.MI', 'FZ.MI', 'GA.MI', 'GAL.MI', 'GAM.MI',
        'GAR.MI', 'GAS.MI', 'GAT.MI', 'GB.MI', 'GC.MI', 'GD.MI', 'GE.MI',
        'GEL.MI', 'GEM.MI', 'GEN.MI', 'GER.MI', 'GES.MI', 'GF.MI', 'GG.MI',
        'GH.MI', 'GI.MI', 'GIA.MI', 'GIB.MI', 'GIC.MI', 'GIO.MI', 'GIS.MI',
        'GJ.MI', 'GL.MI', 'GLO.MI', 'GM.MI', 'GMI.MI', 'GN.MI', 'GO.MI',
        'GOL.MI', 'GON.MI', 'GOR.MI', 'GP.MI', 'GR.MI', 'GRA.MI', 'GRE.MI',
        'GRI.MI', 'GRO.MI', 'GS.MI', 'GSI.MI', 'GT.MI', 'GU.MI', 'GUA.MI',
        'GV.MI', 'GW.MI', 'GY.MI', 'GZ.MI', 'H.MI', 'HA.MI', 'HAL.MI',
        'HAS.MI', 'HB.MI', 'HC.MI', 'HD.MI', 'HE.MI', 'HEL.MI', 'HEN.MI',
        'HF.MI', 'HG.MI', 'HI.MI', 'HIL.MI', 'HJ.MI', 'HL.MI', 'HM.MI',
        'HN.MI', 'HO.MI', 'HOL.MI', 'HOM.MI', 'HOR.MI', 'HP.MI', 'HQ.MI',
        'HR.MI', 'HS.MI', 'HT.MI', 'HU.MI', 'HV.MI', 'HW.MI', 'HY.MI',
        'HZ.MI', 'I.MI', 'IA.MI', 'IB.MI', 'IC.MI', 'ID.MI', 'IE.MI',
        'IF.MI', 'IH.MI', 'II.MI', 'IJ.MI', 'IK.MI', 'IL.MI', 'IM.MI',
        'IN.MI', 'IO.MI', 'IQ.MI', 'IR.MI', 'IS.MI', 'IT.MI', 'IU.MI',
        'IV.MI', 'IW.MI', 'IX.MI', 'IZ.MI', 'J.MI', 'JA.MI', 'JB.MI',
        'JC.MI', 'JD.MI', 'JE.MI', 'JF.MI', 'JG.MI', 'JH.MI', 'JI.MI',
        'JJ.MI', 'JK.MI', 'JL.MI', 'JM.MI', 'JN.MI', 'JO.MI', 'JP.MI',
        'JQ.MI', 'JR.MI', 'JS.MI', 'JT.MI', 'JU.MI', 'JV.MI', 'JW.MI',
        'JX.MI', 'JY.MI', 'JZ.MI', 'K.MI', 'KA.MI', 'KB.MI', 'KC.MI',
        'KD.MI', 'KE.MI', 'KF.MI', 'KG.MI', 'KH.MI', 'KI.MI', 'KJ.MI',
        'KK.MI', 'KL.MI', 'KM.MI', 'KN.MI', 'KO.MI', 'KP.MI', 'KQ.MI',
        'KR.MI', 'KS.MI', 'KT.MI', 'KU.MI', 'KV.MI', 'KW.MI', 'KX.MI',
        'KY.MI', 'KZ.MI', 'L.MI', 'LA.MI', 'LB.MI', 'LC.MI', 'LD.MI',
        'LE.MI', 'LF.MI', 'LG.MI', 'LH.MI', 'LI.MI', 'LJ.MI', 'LK.MI',
        'LL.MI', 'LM.MI', 'LN.MI', 'LO.MI', 'LP.MI', 'LQ.MI', 'LR.MI',
        'LS.MI', 'LT.MI', 'LU.MI', 'LV.MI', 'LW.MI', 'LX.MI', 'LY.MI',
        'LZ.MI', 'M.MI', 'MA.MI', 'MC.MI', 'MD.MI', 'ME.MI', 'MF.MI',
        'MG.MI', 'MH.MI', 'MI.MI', 'MJ.MI', 'MK.MI', 'ML.MI', 'MM.MI',
        'MO.MI', 'MP.MI', 'MQ.MI', 'MR.MI', 'MS.MI', 'MT.MI', 'MU.MI',
        'MV.MI', 'MW.MI', 'MX.MI', 'MY.MI', 'MZ.MI', 'N.MI', 'NA.MI',
        'NB.MI', 'NC.MI', 'ND.MI', 'NE.MI', 'NF.MI', 'NG.MI', 'NH.MI',
        'NI.MI', 'NJ.MI', 'NK.MI', 'NL.MI', 'NM.MI', 'NN.MI', 'NO.MI',
        'NP.MI', 'NQ.MI', 'NR.MI', 'NS.MI', 'NT.MI', 'NU.MI', 'NV.MI',
        'NW.MI', 'NX.MI', 'NY.MI', 'NZ.MI', 'OA.MI', 'OB.MI', 'OC.MI',
        'OD.MI', 'OE.MI', 'OF.MI', 'OG.MI', 'OH.MI', 'OI.MI', 'OJ.MI',
        'OK.MI', 'OL.MI', 'OM.MI', 'ON.MI', 'OO.MI', 'OP.MI', 'OQ.MI',
        'OR.MI', 'OS.MI', 'OT.MI', 'OU.MI', 'OV.MI', 'OW.MI', 'OX.MI',
        'OY.MI', 'OZ.MI', 'PA.MI', 'PB.MI', 'PC.MI', 'PD.MI', 'PE.MI',
        'PF.MI', 'PG.MI', 'PH.MI', 'PI.MI', 'PJ.MI', 'PK.MI', 'PL.MI',
        'PM.MI', 'PN.MI', 'PO.MI', 'PP.MI', 'PQ.MI', 'PR.MI', 'PS.MI',
        'PT.MI', 'PU.MI', 'PV.MI', 'PW.MI', 'PX.MI', 'PY.MI', 'PZ.MI',
        'Q.MI', 'QA.MI', 'QB.MI', 'QC.MI', 'QD.MI', 'QE.MI', 'QF.MI',
        'QG.MI', 'QH.MI', 'QI.MI', 'QJ.MI', 'QK.MI', 'QL.MI', 'QM.MI',
        'QN.MI', 'QO.MI', 'QP.MI', 'QQ.MI', 'QR.MI', 'QS.MI', 'QT.MI',
        'QU.MI', 'QV.MI', 'QW.MI', 'QX.MI', 'QY.MI', 'QZ.MI', 'RA.MI',
        'RB.MI', 'RC.MI', 'RD.MI', 'RE.MI', 'RF.MI', 'RG.MI', 'RH.MI',
        'RI.MI', 'RJ.MI', 'RK.MI', 'RL.MI', 'RM.MI', 'RN.MI', 'RO.MI',
        'RP.MI', 'RQ.MI', 'RR.MI', 'RS.MI', 'RT.MI', 'RU.MI', 'RV.MI',
        'RW.MI', 'RX.MI', 'RY.MI', 'RZ.MI', 'SA.MI', 'SB.MI', 'SC.MI',
        'SD.MI', 'SE.MI', 'SF.MI', 'SG.MI', 'SH.MI', 'SI.MI', 'SJ.MI',
        'SK.MI', 'SM.MI', 'SN.MI', 'SO.MI', 'SP.MI', 'SQ.MI', 'SR.MI',
        'SS.MI', 'ST.MI', 'SU.MI', 'SV.MI', 'SW.MI', 'SX.MI', 'SY.MI',
        'SZ.MI', 'TA.MI', 'TB.MI', 'TC.MI', 'TD.MI', 'TE.MI', 'TF.MI',
        'TG.MI', 'TH.MI', 'TI.MI', 'TJ.MI', 'TK.MI', 'TL.MI', 'TM.MI',
        'TN.MI', 'TP.MI', 'TQ.MI', 'TR.MI', 'TS.MI', 'TT.MI', 'TU.MI',
        'TV.MI', 'TW.MI', 'TX.MI', 'TY.MI', 'TZ.MI', 'U.MI', 'UA.MI',
        'UB.MI', 'UC.MI', 'UD.MI', 'UE.MI', 'UF.MI', 'UG.MI', 'UH.MI',
        'UI.MI', 'UJ.MI', 'UK.MI', 'UL.MI', 'UM.MI', 'UN.MI', 'UO.MI',
        'UP.MI', 'UQ.MI', 'UR.MI', 'US.MI', 'UT.MI', 'UU.MI', 'UV.MI',
        'UW.MI', 'UX.MI', 'UY.MI', 'UZ.MI', 'VA.MI', 'VB.MI', 'VC.MI',
        'VD.MI', 'VE.MI', 'VF.MI', 'VG.MI', 'VH.MI', 'VI.MI', 'VJ.MI',
        'VK.MI', 'VL.MI', 'VM.MI', 'VN.MI', 'VO.MI', 'VP.MI', 'VQ.MI',
        'VR.MI', 'VS.MI', 'VT.MI', 'VU.MI', 'VV.MI', 'VW.MI', 'VX.MI',
        'VY.MI', 'VZ.MI', 'WA.MI', 'WB.MI', 'WC.MI', 'WD.MI', 'WE.MI',
        'WF.MI', 'WG.MI', 'WH.MI', 'WI.MI', 'WJ.MI', 'WK.MI', 'WL.MI',
        'WM.MI', 'WN.MI', 'WO.MI', 'WP.MI', 'WQ.MI', 'WR.MI', 'WS.MI',
        'WT.MI', 'WU.MI', 'WV.MI', 'WW.MI', 'WX.MI', 'WY.MI', 'WZ.MI',
        'X.MI', 'XA.MI', 'XB.MI', 'XC.MI', 'XD.MI', 'XE.MI', 'XF.MI',
        'XG.MI', 'XH.MI', 'XI.MI', 'XJ.MI', 'XK.MI', 'XL.MI', 'XM.MI',
        'XN.MI', 'XO.MI', 'XP.MI', 'XQ.MI', 'XR.MI', 'XS.MI', 'XT.MI',
        'XU.MI', 'XV.MI', 'XW.MI', 'XX.MI', 'XY.MI', 'XZ.MI', 'YI.MI',
        'YJ.MI', 'YK.MI', 'YL.MI', 'YM.MI', 'YN.MI', 'YO.MI', 'YP.MI',
        'YQ.MI', 'YR.MI', 'YS.MI', 'YT.MI', 'YU.MI', 'YV.MI', 'YW.MI',
        'YX.MI', 'YY.MI', 'YZ.MI', 'ZA.MI', 'ZB.MI', 'ZC.MI', 'ZD.MI',
        'ZE.MI', 'ZF.MI', 'ZG.MI', 'ZH.MI', 'ZI.MI', 'ZJ.MI', 'ZK.MI',
        'ZL.MI', 'ZM.MI', 'ZN.MI', 'ZO.MI', 'ZP.MI', 'ZQ.MI', 'ZR.MI',
        'ZS.MI', 'ZT.MI', 'ZU.MI', 'ZV.MI', 'ZW.MI', 'ZX.MI', 'ZY.MI', 'ZZ.MI'
    ]

    tickers_it = list(dict.fromkeys(tickers_it))
    tickers_us = list(dict.fromkeys(tickers_us))

    all_tickers = [(t, 'IT') for t in tickers_it] + [(t, 'US') for t in tickers_us]
    total = len(all_tickers)

    for idx, (sym, market) in enumerate(all_tickers):
        percent = int((idx / total) * 90) + 5
        if idx % 10 == 0:
            update_progress(percent, f"Scaricamento {sym} ({idx}/{total})...")
        
        fetched_history = fetch_yahoo_chart(sym, range_str="5y")
        
        if fetched_history and len(fetched_history) >= 2:
            if sym in market_data:
                combined = market_data[sym]
                combined.update(fetched_history)
                sorted_dates = sorted(combined.keys())
                
                max_days = 1300
                if len(sorted_dates) > max_days:
                    sorted_dates = sorted_dates[-max_days:]
                
                market_data[sym] = {d: combined[d] for d in sorted_dates}
            else:
                sorted_dates = sorted(fetched_history.keys())
                market_data[sym] = {d: fetched_history[d] for d in sorted_dates}
        
        # Pausa di sicurezza estesa a 1.2 secondi per evitare qualsiasi blocco con liste massicce
        time.sleep(1.2)

    it_years_list, us_years_list = [], []
    for sym, hist in market_data.items():
        if not hist:
            continue
        dates = sorted(hist.keys())
        if len(dates) >= 2:
            try:
                years = (datetime.strptime(dates[-1], '%Y-%m-%d') - datetime.strptime(dates[0], '%Y-%m-%d')).days / 365.25
                if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'):
                    it_years_list.append(years)
                else:
                    us_years_list.append(years)
            except Exception:
                pass

    it_count = sum(1 for sym in market_data if sym in tickers_it or sym.endswith('.MI') or sym.endswith('.AS'))
    us_count = len(market_data) - it_count
    
    it_avg_years = round(sum(it_years_list) / len(it_years_list), 1) if it_years_list else 0.0
    us_avg_years = round(sum(us_years_list) / len(us_years_list), 1) if us_years_list else 0.0

    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(market_data, f, indent=2)
    except Exception:
        pass

    update_progress(100, "Completato!", {
        "it_count": it_count,
        "it_avg_years": it_avg_years,
        "us_count": us_count,
        "us_avg_years": us_avg_years
    })

if __name__ == "__main__":
    download_data()