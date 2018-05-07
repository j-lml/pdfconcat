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

PATH_BASE='./pdf/'
PATH_BACKUP='./fin/'
OUTPUT='output.pdf'
MAX_PAGES=100

def load_files(pathpdf):
    #obtiene todos los ficheros de cierto tipo de forma recursiva
    files= get_files(pathpdf, '*.pdf')
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

def delete_files():
    files= get_files('.', 'TMP_*')
    for f in files:
        if f != dest:
            os.remove(f)

def merge_files(files):

    last=files[-1]
    first=files[0]
    max=len(files)

    source=dest

    for f in files:
        filepath=PATH_BASE + f
        filebackup=PATH_BACKUP + f

        #si no existe => crear el output con el fichero que corresponda
        if f==first:
            print('creando PDF: ' + f)
            copyfile(filepath, dest)
            os.rename(filepath, filebackup)
            source=dest
            continue

        num_pages=pdf_num_pages(source)
        add_pages=pdf_is_odd(source)

        #si es impar => concatener con pagina
        if add_pages == True:
            print('+white_page()')
            source=merge_file(source, 'blank.pdf')

        print('+'+f)
        source=merge_file(source, filepath)
        os.rename(filepath, filebackup)


        if num_pages > MAX_PAGES:
            print('last: ' + f)
            break

        #try: #used try so that if user pressed other than the given key error will not be shown
        if kbhit():
            key = getch()
            if key=='q':
                break;
            #if keyboard.is_pressed('q'):#if key 'q' is pressed  => salir
            #    break#finishing the loop
        #except:
        #    print('key_err')

    print('generando PDF: ' + OUTPUT)
    copyfile(dest, OUTPUT)
    print('end.')



if __name__ == "__main__":
    parser = ArgumentParser()

    # Add more options if you like
    parser.add_argument("-o", "--output", dest="output_filename", default="merged.pdf",
                      help="write merged PDF to FILE", metavar="FILE")
    parser.add_argument("-b", "--blank", dest="blank_filename", default="blank.pdf",
                      help="path to blank PDF file", metavar="FILE")
    parser.add_argument("-p", "--path", dest="path", default=".",
                      help="path of source PDF files")
    parser.add_argument("-m", "--max", dest="max_pages", default="100",
                    help="max pages of output")
    args = parser.parse_args()
    OUTPUT=args.output_filename
    MAX_PAGES=int(args.max_pages)

    delete_files()
    files=load_files(PATH_BASE)
    print( repr(files) )
    merge_files(files)
