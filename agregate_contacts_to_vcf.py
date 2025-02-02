# -*- coding: utf-8 -*-
#python 3.5+
#v1.4 добавлен pandas и парсинг и dump в excel.  приоритизация. фио номеров из экселей не заменяются иными. 
import os
import sys
import re
import json
import quopri
import pandas

def parse_json(path='result.json')->list:    
    with open(path, 'r',encoding='utf-8') as file:
        _base_list = json.load(file) #['contacts']['list']
        try:
            _base_list=_base_list['contacts']['list'] #for tg desctop export
        except: pass
        
    fields=( 'last_name' , 'first_name' , 'phone_number' ) # формируем рабочий список без лишних записей и ключей
    _ld=[]
    for k in _base_list:
        if set(fields).issubset(k.keys()):             #фильтруем по наличию необходимых ключей
            _ld.append( {'first_name': k['first_name'],
                        'last_name': k['last_name'],
                        'id': (k['first_name']+' '+k['last_name']).strip(),
                        'phone_number':  re.sub(r'^00', '+', ''.join(re.findall(r'(^\+|\d)', k['phone_number'] ))   ), 
                       } )
            
    print(f'json have {len(_base_list)}  notes, was chosen  {len(_ld)} contacts')
    return _ld
    
def parse_vcf(path) ->list:
    with open(path, 'r',encoding='utf-8') as f: 
        data=f.read()
    
    if data.find('ENCODING=QUOTED-PRINTABLE')!=-1:  #requares lib quopri
        data=quopri.decodestring(data, header=False).decode('UTF-8')
    
    _ld=[] #выделяем записи из строки
    for k in re.split('END:VCARD\n?', re.sub(r'\n" "*?', r'\n', data )  ):
        if k:
            _a=re.findall('\nN.*?:(.*?)\n', k )[0].split(';')  
            try:
                _ld.extend( [
                    {
                        'first_name': _a[1],
                        'last_name': _a[0],
                        'id': re.findall('FN.*?:(.*)\n', k  )[0],    #имя фамилия first last
                        #'id': (_a[1].strip()+' '+_a[0].strip()).strip(), # for version 2.1
                        'phone_number':  ''.join(re.findall('(^\+|\d)',n) )     #удаляет лишнее из номера
                    } for n in re.findall('TEL.*?([\(\)\+\-\s\d]*)\n', k  ) 
                        ])  #генератор словарей по числу тел.номеров

            except Exception as e:
                print('ERROR with: ',k)
    print(f'was chosen  {len(_ld)} contacts')
    return _ld

def parse_excel(path='result.xls') -> tuple:       #->list:    
    try:
        df=pandas.read_excel(path, dtype='str', keep_default_na=False)[ ['last_name' , 'first_name' , 'phone_number'] ] 
    except Exception:
        print(f'ERROR fail to open {path}')        
    _ld=[]
    for k in df.itertuples():
        _ld.extend( [{'first_name': k[2].strip(),
                    'last_name': k[1].strip(),
                    'id': (k[2].strip()+' '+k[1].strip()), #.strip(),
                    'phone_number':  ''.join(re.findall(r'(^\+|\d)', ph_number )),  # re.sub(r'^8', '+', 
                   } for ph_number in k[3].split(';') ]  )
            
    print(f'excel have {df.shape[0]}  notes, was chosen  {len(_ld)} contacts')
    return (_ld , [k['phone_number'] for k in _ld] ) ) 

def compare(_lt)->str:
    t=list(filter(None, _lt))
    if not t:
        return ''
    else:
        return min(t).strip()

def excel_dump(rows,path='',):
    pandas.DataFrame(rows)[['last_name', 'first_name', 'phone_number']].to_excel(path+'_all.xls', index=False)
    
def write_vcf(rows, path=''):
    with open(path+'_ALL.vcf', 'w',encoding='utf-8') as allvcf:
        i = 0
        for row in rows:
            st='BEGIN:VCARD\n'
            st+='VERSION:3.0\n'  
            st+=f'''N:{row['last_name']};{row['first_name']};;;\n'''
            st+=f'''FN:{row['id']}\n'''
            st+="\n".join([f'TEL;TYPE=CELL:{k}' for k in row['phone_number'].split(';') ])+"\n" #по одному номеру на строку
            #st+=f'EMAIL:{row[3]}\n'
            st+='END:VCARD\n'
            
            allvcf.write(st)
            i += 1#counts            
    print ('\n',str(i) + " vcf cards generated")
    
def merging_duplicates(_ld, _show_merged_rows=None)->list: #объединяет схожие записи по имени или номеру
    _phone_d={} 
    _name_d={} 
    _merged=[]
    
    for k in _ld: #при совпадении номеров, выбираем КОРОТКИЕ имена
        if k['phone_number'] in _phone_d:

            _d=_phone_d[k['phone_number']]   #dictionary link
            _merged.extend([ _d['id']+k['phone_number'],  k['id']+k['phone_number'] ]) 
            
            _d['last_name']='' if _d['first_name']==_d['last_name'] else _d['last_name']  #устраняем дублирование
            k['last_name']='' if k['first_name']==k['last_name'] else k['last_name'] 
            
            if  (_d['last_name']==k['first_name'] and  _d['first_name']==k['last_name']): pass            
            elif set(_d['id'].split(' '))==set(k['id'].split(' ')):  #допущенно объединение в одном из источников, привилегия разделенному
                _d['last_name']=compare( [_d['last_name'], k['last_name']])  
                _d['first_name']=compare( [_d['first_name'], k['first_name']])  
            else:
                _d['first_name']=compare( [_d['first_name'], k['first_name']])  
                _d['last_name']=' '.join([k for k in max(_d['id'],k['id']).split(' ') if k not in _d['first_name'].split(' ') ]) #убрать вхождения
                _d['id']: _d['first_name']+' '+_d['last_name']                  
                          
        else:
            _phone_d[k['phone_number']]=k

    for k in _phone_d.values():   #при совпадении имен, собираем номера
        if k['id'] in _name_d:
            _merged.extend([ k['id']+_name_d[k['id']]['phone_number'],  k['id']+k['phone_number'] ])
            _name_d[k['id']]['phone_number']+=f';{k["phone_number"]}'  
        else:
            _name_d[k['id']]=k

    print('merged : ' + str(len(set(_merged))) )
    if _show_merged_rows: print('\n',*_merged, sep='\n')                #optional
    return(_name_d.values())
    
def get_listFiles(path)->list:
    _listFiles=[]

    for d, dirs, files in os.walk(path):
        for file in files:
            fullname = os.path.join(d, file)
            extention=os.path.splitext(file)[1].replace('.', '', 1)
            try:
                _listFiles.append( [fullname,None,extention,file])  #getsize(fullname)
            except (OSError,):
                pass

    return _listFiles

def add_notes_with_filter(notes,candidates, priority_numbers=[]) -> list:
    for k in candidates:
        if k['phone_number'] not in priority_numbers:
            notes.append( k )  

def worker(listFiles,allow_extentions=['json','vcf','xls'], priority_numbers=[])->list:   #should rename agregate lists
    notes=[]
    for row in listFiles:  #index, row in df[[0,1,2,3]].iterrows():
        if row[2] not in allow_extentions:  #пропускаем файлы не подхоящего разрешения
            print( f'skip {row[0]}')
        else:
            print(row[0]) #file path 
            try:
                if row[2]=='vcf':
                    add_notes_with_filter(notes ,parse_vcf(row[0]), priority_numbers)
                    print( len(notes) , 'notes after vcf')
                elif row[2]=='json':  
                    add_notes_with_filter(notes ,parse_json(row[0]), priority_numbers) 
                    print( len(notes) , 'notes after json')
                elif row[2]=='xls':  
                    _ld= parse_excel(row[0])                    
                    add_notes_with_filter(notes ,_ld[0], priority_numbers) 
                    priority_numbers.extend( _ld[1] )
                    print( len(notes) , 'notes after xls')

            except Exception as e:
                print('error with ',row[0], e)
    return notes

def main(args):      # all extentions
    #print(args)
    if len(args)==2:
        arg =args[1]
    elif type(args) is str:
        arg =args
    else:
        arg = 'vcf,json,xls'
    allow_extentions=arg.split(',')
    
    path_files=os.getcwd()+'\\'
    print(f'Try find all {allow_extentions} files in {path_files}')
    
    notes=worker(get_listFiles(path_files), allow_extentions) 
    notes=merging_duplicates(notes, _show_merged_rows=None) #optional
    excel_dump(notes,path_files)
    write_vcf(notes, path_files)

if __name__ == '__main__':
    main(sys.argv)

