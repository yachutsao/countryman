import csv, re 
import numpy as np
import pandas as pd
import math
from itertools import zip_longest
import Lily.ctao2.ctao2_database_alias
from Lily.ctao2.ctao2_database_alias import manidb, alias, tickwatch
from multiprocessing import Pool

#from osgeo import ogr
import osgeo, ogr
#%% text conversion
CT2_HTAB_SECT_NUM = str.maketrans (
    {
    '0':'○',
    'ㄧ':'一',
    '1':'一', 
    '2':'二',
    '3':'三',
    '4':'四',
    '5':'五',
    '6':'六',
    '7':'七',
    '8':'八',
    '9':'九',
#０-９ 65296-65305
    65296:'○',
    65297:'一', 
    65298:'二', 
    65299:'三', 
    65300:'四', 
    65301:'五', 
    65302:'六', 
    65303:'七', 
    65304:'八',
    65305:'九'
    })

CT2_HTAB_CHN = str.maketrans (
    {
    '巿':'市',
    '臺':'台',
    '褔':'福', 
    '豊':'豐',
    '陜':'陝',
    '恒':'恆',
    'ㄧ':'一'
    })

CT2_HTAB_ENG = str.maketrans(
    {# uppercase
    'Ａ':'A',
    'Ｂ':'B',
    'Ｃ':'C',
    'Ｄ':'D',
    'Ｅ':'E',
    'Ｆ':'F',
    'Ｇ':'G',
    'Ｈ':'H',
    'Ｉ':'I',
    'Ｊ':'J',
    'Ｋ':'K',
    'Ｌ':'L',
    'Ｍ':'M',
    'Ｎ':'N',
    'Ｏ':'O',
    'Ｐ':'P',
    'Ｑ':'Q',
    'Ｒ':'R',
    'Ｓ':'S',
    'Ｔ':'T',
    'Ｕ':'U',
    'Ｖ':'V',
    'Ｗ':'W',
    'Ｘ':'X',
    'Ｙ':'Y',
    'Ｚ':'Z',
    # lowercase
    'ａ':'a',
    'ｂ':'b',
    'ｃ':'c',
    'ｄ':'d',
    'ｅ':'e',
    'ｆ':'f',
    'ｇ':'g',
    'ｈ':'h',
    'ｉ':'i',
    'ｊ':'j',
    'ｋ':'k',
    'ｌ':'l',
    'ｍ':'m',
    'ｎ':'n',
    'ｏ':'o',
    'ｐ':'p',
    'ｑ':'q',
    'ｒ':'r',
    'ｓ':'s',
    'ｔ':'t',
    'ｕ':'u',
    'ｖ':'v',
    'ｗ':'w',
    'ｘ':'x',
    'ｙ':'y',
    'ｚ':'z',
    })

CT2_HTAB_NUM = str.maketrans(
    {
    '○':'0',
    'ㄧ':'1',
    '一':'1', 
    '二':'2',
    '三':'3',
    '四':'4',
    '五':'5',
    '六':'6',
    '七':'7',
    '八':'8',
    '九':'9',
    '十':'10',
#０-９ 65296-65305
    65296:'0', 
    65297:'1', 
    65298:'2', 
    65299:'3', 
    65300:'4', 
    65301:'5', 
    65302:'6', 
    65303:'7', 
    65304:'8',
    65305:'9'
    })

CT2_HTAB_SYMBOL = str.maketrans(
   {# brackets
    '（' :'(',
    '﹙' :'(',
    '『' :'(',
    '「' :'(',
    '﹝' :'(',
    '〔' :'(',
    '｛' :'(',
    '【' :'(',
    '《' :'(',
    '〈' :'(',

    '）' :')',
    '﹚' :')',
    '』' :')',
    '」' :')',
    '﹞' :')',
    '〕' :')',
    '｝' :')',
    '】' :')',
    '》' :')',
    '〉' :')',
    # comma
    '、' :',',
    '，' :',',
    # desh, hyphen
    '﹣' :'-',
    '–'  :'-',
    '－' :'-',
    '─'  :'-',
    '—'  :'-',
    '＿' :'-',
    'ˍ'  :'-',
    '▁'  :'-',
    '之' :'-',
    '附' :'-',
    # tilde
    '～' :'~',
    # colon
    '：':':',
    '﹕':':',
    # semicolon
    '；':';',
    '﹔':';',
    # question
    '？':'?',
    '﹖':'?',
    # exclamation
    '！':'!',
    '﹗':'!',
    # slash
    '╱' :"/",
    '／':"/",
    '∕' :"/",
    # hashtag
    '＃':'#',
    "#":'#',
    # quotation
    '‘' :'"',
    '’' :'"',
    '“' :'"',
    '”' :'"',
    '〝':'"',
    '〞':'"',
    '‵' :'"'
    })

def fun4checkgeo(arg):
    res1     = {'check_town_geo' : 0}
    try:
        bnd     = ogr.CreateGeometryFromWkt(arg[0])
        poi     = ogr.CreateGeometryFromWkt(arg[1])
        res1['check_town_geo'] = poi.Within(bnd)  
    except:
        res1['check_town_geo'] = 3
    return res1

def fun4cntycode(arg):
    return {'reCntycode' : (arg[1] == arg[0]) }

def fun4towncode(arg):
    return {'reTowncode' : (arg[1][:5] == arg[0]) }

def fun4number(arg):
    res1     = {}
    arg      = arg[1]
    if arg is None:

        res1['number'] = ''
        res1['floor']  = ''
        return res1

    ans1     = arg.split('號')

    if len(ans1) == 2:
        res1['number'] = ans1[0].translate(CT2_HTAB_NUM).translate(CT2_HTAB_SYMBOL)
        res1['floor']  = ans1[1].translate(CT2_HTAB_NUM).translate(CT2_HTAB_SYMBOL)
    else:
        res1['number'] = ans1[0].translate(CT2_HTAB_NUM).translate(CT2_HTAB_SYMBOL)
        res1['floor']  = ''
    #-------------------------------------------------------------------------------
    #step 1 NUMd  = r'[0123456789]{1,4}'
    #step 2 NUMd  = r'[臨]{0,1}[0123456789]{1,4}'
    #step 3 NUMd  = r'^[臨]{0,1}[0123456789]{1,4}$'
    #step 4 NUMd  = r'^[臨]{0,1}[0-9\-]{1,4}$'
    #step 5 NUMd  = r'^[臨]{0,1}[0-9]{1,4}[\-0-9]{0,5}$'
    #-------------------------------------------------------------------------------
    
    NUMd  = r'^([臨建附特()]{0,3})([0-9]{1,4})([0-9A-Z]{0,6}){0,3}([\-]{1}[0-9A-Z甲乙丙丁]{0,6}){0,3}$'

    FLOORd = r'^([地下底室\-]{0,4}([0-9A-Z,]{0,4}[樓層]{1}[0-9A-Z,\-]{0,7}){0,4}){0,10}([\-]{0,1}[0-9A-Z]{0,3}){0,7}$'

    repattern       = re.compile(NUMd)
    match           = re.match(repattern, res1['number'] ) 
    
    if match:
        res1['reNumber'] = 1
    else:
        res1['reNumber'] = 0

    repattern      = re.compile(FLOORd)
    match          = re.match(repattern, res1['floor'] )
  
    if match:
        res1['reFloor'] = 1
    else:
        res1['reFloor'] = 0 

    return res1

def lookup_value(arg1, arg2, arg3):
    list0 = []; dic = {}
    list_town_code = arg1[arg2].tolist()
    list_point_geo = arg1['point_wkt'].tolist()

    df = arg3.set_index(arg2)
    for town_code in list_town_code:
        town_wkt = 0
        if town_code in df.index:
            town_wkt = df.loc[town_code, 'town_wkt']
        else:
            town_wkt = ''
        list0.append(town_wkt)

    dic['town_wkt'] = list0
    df = pd.DataFrame.from_dict(dic, orient = 'columns')
    return df

def check_addr_column(cnty_source_name, cnty_source_df, col_name , fun_obj):
    
    mpool          = Pool(8)   

    list_arg       = cnty_source_df[col_name].tolist()
    a              = [cnty_source_name]*len(list_arg)
    ziparg         = zip(a, list_arg)

    result_trans   = mpool.map(fun_obj, ziparg)

    df = pd.DataFrame.from_dict(result_trans, orient = 'columns')

    for colname in df.columns:
        cnty_source_df[colname] = df[colname]

    mpool.close()
    return cnty_source_df

def output_error(mydb, df0, target):

    cputime = tickwatch()

    df1    = df0[df0['check_town_geo']==0]
    df2    = df0[df0['reCntycode']    ==0]
    df3    = df0[df0['reTowncode']    ==0]
    df4    = df0[df0['reNumber']      ==0]
    frames = [df1, df2, df3, df4]

    result = pd.concat(frames)
    result = result[['geom','origin_address','fid', 'cnty_code', 'town_code', 'lie', 'lin', 'road', 'zone', 'lane', 'alley', 'number','floor','checklist']]
    name   = target + '_modify'

    mydb.get_alias(name).write(result)
    cputime.tick('Write down dataframe' + name)

def function_x(mydb, cnty, town, cntynum, cnty_wkt):

    cputime = tickwatch()

    target   = 'A' + cntynum
        
    #resource
    df0     = mydb.get_alias(target).read()
    cputime.tick('Data read')

    sdf     = df0[['fid', 'cnty_code', 'town_code', 'lie', 'lin', 'road', 'zone', 'lane', 'alley', 'num']]
    df0.insert(0, 'origin_address', sdf.apply( lambda a : str(a.to_list()),  axis =1 ) ) 

    df0['point_wkt'] = df0[['TWD97_X', 'TWD97_Y']].astype(str).apply(lambda x: ' '.join(x), axis=1)
    df0['point_wkt'] = df0['point_wkt'].apply (lambda x : f'POINT({x})')
    
    #if df0.empty :
    #    continue
        
    cputime.tick('Point_wkt added')

    #check county boundary
    df0             = check_addr_column(cnty_wkt, df0, 'point_wkt', fun4checkgeo)
    # check town boundary
    town_wkt        = lookup_value(df0, 'town_code', town)
    ziparg          = zip(town_wkt['town_wkt'].tolist(), df0['point_wkt'].tolist())

    #-----------------------------------------
    with Pool(8) as mpool :             
        check_town = mpool.map(fun4checkgeo, ziparg)

    #-----------------------------------------
    #debug 
    #check_town = []
    #for arg in ziparg:
    #    check_town.append(fun4checkgeo(arg))        
    #------------------------------------
    df_check_town   = pd.DataFrame.from_dict(check_town, orient = 'columns')
    df0['check_town_geo'] = df_check_town['check_town_geo']
        
    cputime.tick('Geometry checked')
        
    #check county code
    df0     = check_addr_column(cntynum,  df0, 'cnty_code', fun4cntycode)
    # check town code
    df0     = check_addr_column(cntynum,  df0, 'town_code', fun4towncode)
    # check number
    df0     = check_addr_column(cntynum,  df0, 'num', fun4number)

    cputime.tick('Code and number checked')

    cdf     = df0[['check_town_geo', 'reCntycode', 'reTowncode', 'reNumber', 'reFloor']]
    df0['checklist'] = cdf.apply( lambda a : a.to_csv(),  axis =1 ) 
        
    df_tran = df0[['geom', 'origin_address','fid', 'cnty_code', 'town_code', 'lie', 'lin', 'road', 'zone', 'lane', 'alley', 'number','floor','checklist']]
        
    mydb.get_alias(target + '_TRAN' ).write(df_tran)
    cputime.tick('Write down dataframe' + target)

    # take out error data
    output_error(mydb, df0, target)

def fun4yeh(mydb, tran, modify):
    
    df0     = mydb.get_alias(tran).read()
    df1     = mydb.get_alias(modify).read()
    

    df0     = df0.set_index(['fid'])
    df1     = df1.set_index(['fid'])

    df0.loc[df1.index, :] = df1[:]

    sdf = df0[['geom', 'origin_address', 'cnty_code', 'town_code', 'lie', 'lin', 'road', 'zone', 'lane', 'alley', 'number', 'floor']]

    mydb.get_alias(tran + '_yeh' ).write_with_index(sdf)
    cputime.tick('Write down dataframe '+ tran)

if __name__ == '__console__' or __name__ == '__main__':
    cputime = tickwatch()

    mydb     = manidb('G:/NCREE_GIS/2020_address/2021_TGOS_NLSC_TWN22.sqlite')
    #cnty     = mydb.get_alias('metadata_nsg_cnty').read()
    cnty     = mydb.get_alias('metadata_nsg_cnty_3825').read()
    town     = mydb.get_alias('metadata_nsg_town').read()

    for key, row in cnty[ cnty['ncity'] =='09020'].iterrows():

        cntynum  = row['ncity']
        cnty_wkt = row['cnty_wkt']

        #function_x(mydb, cnty, town, cntynum, cnty_wkt)

        tran     = 'A' + cntynum + '_TRAN'
        modify   = 'A' + cntynum + '_modify'
        fun4yeh(mydb, tran, modify)

    
