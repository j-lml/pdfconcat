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

def merge(path, blank_filename, output_filename):
    blank = PdfFileReader(file(blank_filename, "rb"))
    output = PdfFileWriter()

    for pdffile in glob('*.pdf'):
        if pdffile == output_filename:
            continue
        print("Parse '%s'" % pdffile)
        document = PdfFileReader(open(pdffile, 'rb'))
        for i in range(document.getNumPages()):
            output.addPage(document.getPage(i))

        if document.getNumPages() % 2 == 1:
            output.addPage(blank.getPage(0))
            print("Add blank page to '%s' (had %i pages)" % (pdffile, document.getNumPages()))
    print("Start writing '%s'" % output_filename)
    output_stream = file(output_filename, "wb")
    output.write(output_stream)
    output_stream.close()

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


OUTPUT_PATH='./cut/'
OUTPUT='output.pdf'
MAX_PAGES=100

def load_files(pathpdf,type='*.pdf'):
    #obtiene todos los ficheros de cierto tipo de forma recursiva
    files= get_files(pathpdf,type )
    files= [path_leaf(path) for path in files]

    return sorted(files)

def exec_command(command):
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    process.wait();
    #os.system("start /wait cmd /c " +  command)

cont=0
PRE='TMP_'
dest='TMP_0'

def merge_file(first, second):
    global cont
    global dest

    cont=cont+1
    dest=PRE+str(cont)
    command="pdftk.exe " + first + " " + second + " cat output " + dest
    exec_command(command)
    return dest


#ref: https://stackoverflow.com/questions/6598937/set-output-location-for-pdftk-sample-pdf-burst
#ref: pdftk burst https://www.pdflabs.com/docs/pdftk-man-page/#dest-op-burst
def split_file(filename):
    command="pdftk.exe " + filename + " burst output " + OUTPUT_PATH + "%04d.pdf"
    exec_command(command)
    return dest

procfiles=0
def tika_file(filename, inputpath="./cut/", outputpath='.'):
    global procfiles

    #tika-python -o . --server 10.10.10.1 --port 9998 parse text fichero.pdf
    command="tika-python -o " + outputpath + " --server 10.60.6.165 --port 9998 parse text " + inputpath+filename

    #si no existe O se fuerza =>
    if os.path.isfile(outputpath+filename+"_meta.json")==False or FORCE==True:
        procfiles=procfiles+1
        exec_command(command)
        print(command)

    return dest

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

items=[]
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

procfiles=0

def proc_files(files):
    global procfiles
    procfiles = 0

    last=-1

    items=[]        #lista cont todos los ficheros
    blocklist=[]    #lista de bloques
    blockfine=[]
    blockerr=[]

    block=[]
    expected=2016000001
    for f in files:
        procfiles=procfiles+1
        result = analize_file(f,INPUT)
        items.append(result) #almacena TODOS los ficheros procesados
        #print(repr(result))

        candidate=False
        if result['first'] == True and result['resolution'] > last:
            newgroup=True
            store=block
            block=[]

        block.append(result)

        if len(store) >0:
            #almacenar el bloque antiguo y comenzar nuevo
            blocklist.append(store)
            new=store[0]['resolution']
            #si no es el esperado => anterior es error
            if new != expected:
                blockerr.append( blockfine[-1] )
            #si es >= a esperado => ok
            if new >= expected:
                blockfine.append(store)


            store=[]
            expected=new+1

            #si es primero comieza bloque
            last=result['resolution']



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




if __name__ == "__main__":
    parser = ArgumentParser()

    # Add more options if you like
    parser.add_argument("-i", "--input", dest="input_path", default="./json2/",
                      help="path de tiff o pdf", metavar="PATH")
    parser.add_argument("-o", "--output", dest="output_path", default="./result/",
                      help="path de salida", metavar="PATH")
    parser.add_argument("-f", "--force", action='store_true',
                      help="force overwrite")
    args = parser.parse_args()


    INPUT=args.input_path
    OUTPUT_PATH=args.output_path
    FORCE=get_bool(args.force)

    #result=load_files(INPUT,'*.tiff')
    print("loading files...")
    result=load_files(INPUT,'*.json')
    contfiles=len(result)
    print("loaded: " + str( contfiles) )

    print("start")
    items,blocks,bfine,berr=proc_files(result)
    print("end")

    cf=[x for x in items if x['first']==True]
    cl=[x for x in items if x['last']==True]
    cr=[x for x in items if x['resolution']!=None]
    crl=[x['resolution'] for x in items if x['resolution']!=None]
    crf=[x for x in items if x['resolution']!=None and x['first']==False]
    print("total first: "  + str(len(cf)))
    print("total last: "  + str(len(cl)))
    print("total resol: "  + str(len(cr)))
    print("total resol NO repes: "  + str(len(crl)))
    #print(repr(crl))
    print("total resol NO first: "  + str(len(crf)))
    #print(repr(crf))

    #result=analize_file( '00011.json', INPUT)
    #print(repr(result))
    print("total ficheros: "  + str(contfiles))
    print("ficheros procesados: "  + str(procfiles))

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
