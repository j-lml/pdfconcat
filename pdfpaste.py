#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime, calendar
import glob
import os
import sys
import fnmatch
import ntpath
import urllib
import time
import logging

import regex as re

import json
import collections

from shutil import copyfile
import shutil

from argparse import ArgumentParser
from glob import glob
from pyPdf import PdfFileReader, PdfFileWriter

from subprocess import call
import subprocess

from msvcrt import getch
from msvcrt import kbhit
#import keyboard
#pip3 install keyboard



# TIKA
# Instalar Servidor:
#     docker pull logicalspark/docker-tikaserver # only on initial download/update
#
# Ejecuta maquina en puerto:
#     docker run --rm -p 9998:9998 logicalspark/docker-tikaserver
#
# Instalar cliente:
#     pip install tika
#
# Ejecuta cliente:
#     tika-python -o . --server 10.10.10.1 --port 9998 parse text fichero.pdf

#https://github.com/LexPredict/tika-server
#docker pull lexpredict/tika-server
#docker run -p 9998:9998 -it lexpredict/tika-server
#

def pdf_num_pages(pathfile):
    document = PdfFileReader(open(pathfile, 'rb'))
    return document.getNumPages()

def pdf_is_odd(pathfile):
    #es impar? si impar => poner pagina en blanco
    flag=False
    if ( pdf_num_pages(pathfile) % 2 == 1 ):
        flag=True
    return flag


#devuelve array de nombres de ficheros (incluido el PATH) de forma recursiva
#used: para buscar ficheros que ya existen
def get_files(dirname, ext):
    matches = []
    for root, dirnames, filenames in os.walk(dirname):
        for filename in fnmatch.filter(filenames, ext):
            matches.append(os.path.join(root, filename))
    return matches

#devuelve la hoja (nombre del fichero) de cierto PATH
def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def load_files(pathpdf,type='*.pdf'):
    #obtiene todos los ficheros de cierto tipo de forma recursiva
    files= get_files(pathpdf,type )
    files= [path_leaf(path) for path in files]

    return sorted(files)


def exec_command(command):
    #ejecuta el comando SOLO si comando force -f
    if FORCE==True:
        process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
        process.wait();
        #os.system("start /wait cmd /c " +  command)


def delete_files():
    files= get_files('.', 'TMP_*')
    for f in files:
        if f != dest:
            os.remove(f)

def get_bool(s):
    s=''+str(s)
    s = s.lower()
    flag=False
    if s in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
        flag=True
    return flag

#####################################################
# PROGRAMA PRINCIPAL
#####################################################


#usado por proc_files()
#sirve para cargar el fichero indicado en filename y realizar un primer analisis (si > 80 => true pe)
def analize_file(filename, inputpath='./'):
    result=""
    with open(inputpath+filename, 'r') as handle:
        result = json.load(handle)
    #result[]=
    item={}
    item['fscan']=result['info']['filename']
    item['fpdf']=result['info']['filename'].split('_')[0]
    item['fjson']=filename
    item['first']=True if result['resolution_info']['total'] > 80 else False
    item['last']=True if result['sign_info']['total'] >= 75 else False
    res=result['resolution_info']['resolution']
    try:
        item['resolution']= int(res) if res != None else None
    except:
        item['resolution']=None
        print("resolucion no valida")

    j=json.dumps(result, indent=4, sort_keys=True)
    #print(j)
    return item

#procedimiento ppal:
#a partir de un array de ficheros => los analiza => genera bloques
procfiles=0
def proc_files(files, lastres, limit=0 ):
    global procfiles
    procfiles = 0

    last=lastres

    items=[]        #lista cont todos los ficheros
    blocklist=[]    #lista de bloques
    blockfine=[]
    blockerr=[]

    block=[]
    first_expected=2016000001
    expected=first_expected

    limite=0

    files=sorted(files)

    firstgroup=False

    store=[]
    for f in files:
        procfiles=procfiles+1
        result = analize_file(f,INPUT)


        items.append(result) #almacena TODOS los ficheros procesados
        

        #1. si empieza nuevo bloque => prepara bloque anterior
        if result['first'] == True and result['resolution'] > last  and result['resolution'] >= expected:
            firstgroup=True
            store=block
            block=[]

        #1.1 saltar todos los que ya estan procesados en pdf ./result/
        #si no empieza => continuar (solo comienza si result > last siendo last el ultimo pdf  )
        if firstgroup==False:
            continue

        #2. almacena el nuevo bloque
        block.append(result)

        #3. guarda el bloque anterior
        if len(store) >0:
            #almacenar el bloque antiguo y comenzar nuevo
            blocklist.append(store)
            new=store[0]['resolution']
            #si no es el esperado => anterior es error
            if new != expected and len(blockfine)>=1:
                blockerr.append( blockfine[-1] )
            #si es >= a esperado => ok
            if new >= expected:
                blockfine.append(store)

            #salir si diferencia es muy grande!
            if new > (expected+100) and expected != first_expected:
                print("ERROR: diferencia muy grande en file " + store[0]['fjson'] + " " + str(expected) + " : " + str(new))
                break

            store=[]
            expected=new+1

            #si es primero comieza bloque
            last=result['resolution']


        #4. para poner limite (en pruebas). normalmente 10
        limite=limite+1
        if limite > limit and limit > 0:
            break




    #almacenar si queda alguno pendiente
    if len(block) > 0:
        blocklist.append(block)
        new=block[0]['resolution']
        if new == expected:
            blockfine.append(block)
        else:
            blockerr.append(block)
        expected=new+1

    return items,blocklist,blockfine,blockerr


#a partir de un bloque de ficheros lo transforma en un pdf en outputpath
#los bloques de fichero se obtienen en proc_files()
def paste_pdf(block, outputpath='./result/', inputpath='./pdf/'):
    cad=""

    dest=outputpath + str(block[0]['resolution']) + ".pdf"
    for item in block:
        cad = cad + " " + inputpath + item['fpdf']
    cad=cad.strip()
    command="pdftk.exe " + cad + " " + " cat output " + dest

    #con param -g se muestran los comandos a generar
    #NECESITA param -f para que se ejecute el comando!
    print(command)
    exec_command(command)

#muestra estadisticas de los bloques
contfiles=0
def statistics(items,blocks,bfine,berr):
    print("statistics:")
    cf=[x for x in items if x['first']==True]
    cl=[x for x in items if x['last']==True]
    cr=[x for x in items if x['resolution']!=None]
    crl=[x['resolution'] for x in items if x['resolution']!=None]
    crf=[x for x in items if x['resolution']!=None and x['first']==False]

    #en el caso ideal => total first == total resol
    print("total first: "  + str(len(cf)))
    print("total last: "  + str(len(cl)))
    print("total resol: "  + str(len(cr)))
    print("total resol NO repes: "  + str(len(crl)))
    print("total resol NO first: "  + str(len(crf)))

    #ficheros en carpeta de entrada
    print("ficheros json: "  + str(contfiles))
    #ficheros procesados
    print("ficheros procesados: "  + str(procfiles))

    #sobre resultados:
    temp=bfine[0]
    #print(repr(temp))
    min=bfine[0][0]['resolution']
    max=bfine[-1][0]['resolution']

    print("min detected: " + str(min))
    print("max detected: " + str(max))
    exp=max - min + 1
    print("expected: " + str(exp))
    det=len(bfine)
    print("detected: " + str(det))
    err=len(berr)
    print("errors: " + str(err))
    pdet= (float(det) * 100 ) / float(exp)
    print("% detected: " + str(pdet))
    perr= (float(err) * 100 ) / float(exp)
    print("% errores: " + str(perr))




if __name__ == "__main__":
    #ej: python pdfpaste.py -i .\json2\  -o .\result\ -g
    #
    #dirs por defecto:
    # -i ./json/ => los extractos con la metainformacion
    # -o ./result/ => donde se almacena resultando
    #    ./result_err/ => mismo que -o con _err (donde se almacenan erroneos)
    # -p ./pdf/ => donde se encuentran los pdf a concatenar
    # -g -> crea comandos de pegado
    # -f => realiza la creacion de documentos!
    # -s => muestra estadisticas
    #con param -g se muestran los comandos a generar
    #nota: NECESITA param -f para que se ejecute el comando!


    parser = ArgumentParser()

    # Add more options if you like
    parser.add_argument("-i", "--input", dest="input_path", default="./json2/",
                      help="path con json", metavar="PATH")
    parser.add_argument("-o", "--output", dest="output_path", default="./result/",
                      help="path de salida", metavar="PATH")
    parser.add_argument("-p", "--pdf", dest="pdf_path", default="./pdf/",
                    help="path de de los pdf", metavar="PATH")
    parser.add_argument("-f", "--force", action='store_true',
                      help="force overwrite")
    parser.add_argument("-g", "--generate", action='store_true',
                      help="force overwrite")
    parser.add_argument("-s", "--statistics", action='store_true',
                    help="muestra estadisticas")
    args = parser.parse_args()


    INPUT=args.input_path
    OUTPUT_PATH=args.output_path
    PDF_PATH=args.pdf_path
    FORCE=get_bool(args.force)
    GENERATE=get_bool(args.generate)
    STATS=get_bool(args.statistics)

    #result=load_files(INPUT,'*.tiff')
    print("loading files...")
    result=load_files(INPUT,'*.json')
    contfiles=len(result)
    print("loaded: " + str( contfiles) )

    #result=load_files(INPUT,'*.tiff')
    print("loading pdf...")
    pdfs=load_files(OUTPUT_PATH,'*.pdf')
    pdfs=sorted(pdfs)
    contpdf=len(pdfs)
    print("loaded: " + str( contpdf) )
    lastpdf=pdfs[-1] if len(pdfs)>=1 else ""
    print("last pdf: " + lastpdf)

    lastres=-1
    try:
        lastres=int(lastpdf.split('.')[0])
    except:
        print('no encontrado resolucion pdf '  + OUTPUT_PATH)

    print("last pdf: " + lastpdf)
    print("last res: " + str(lastres))



    print("processing files")
    items,blocks,bfine,berr=proc_files(result,lastres)
    print("end")

    if GENERATE == True:
        print("pdf:")
        for f in bfine:
            paste_pdf(f,OUTPUT_PATH, PDF_PATH)

        print("errors:")
        for f in berr:
            paste_pdf(f,OUTPUT_PATH[:-1]+'_err/', PDF_PATH)


    if STATS == True:
        statistics(items,blocks,bfine,berr)

    '''
    print("--------------")
    for f in blocks:
        print("res: " + str(f[0]['resolution']) )
        fine=[x['fpdf'] for x in f]
        print(repr(fine))

    print("--------------")
    for f in bfine:
        print("fine: " + str(f[0]['resolution']) )
        fine=[x['fpdf'] for x in f]
        print(repr(fine))

    print("--------------")
    for f in berr:
        print("err: " + str(f[0]['resolution']) )
        fine=[x['fpdf'] for x in f]
        print(repr(fine))
    '''
