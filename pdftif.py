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


#ref: https://stackoverflow.com/questions/6598937/set-output-location-for-pdftk-sample-pdf-burst
#ref: pdftk burst https://www.pdflabs.com/docs/pdftk-man-page/#dest-op-burst
def split_file(filename):
    command="pdftk.exe " + filename + " burst output " + OUTPUT_PATH  + "%04d.pdf"
    exec_command(command)
    return dest

procfiles=0
def convert(filename,type='tiff'):
    global procfiles
    name=INPUT + filename
    f=filename.split('.')

    output=OUTPUT_PATH + f[0] + '.' + type

    #  -resize 25% -monochrome
    command="magick.exe convert -colorspace rgb -density 300 " + name + ' +dither  -colors 2  -colorspace Gray  -normalize ' + output
    command="magick.exe convert -colorspace rgb -density 300 " + name + ' -resize 25% -monochrome ' + output
    command="gswin32c.exe -q -dNOPAUSE   -r600  -sDEVICE=tiff24nc -sOutputFile=" + output + " " + name + " -c quit"
    command="gswin32c.exe -q -dNOPAUSE   -r600  -sDEVICE=tiffg4 -sOutputFile=" + output + " " + name + " -c quit"

    command="magick.exe convert -density 300 " + name + " -background white -alpha off -depth 8 -compress lzw "  + output

    #command="gswin32c.exe -q -dNOPAUSE   -r600 -sDEVICE=tiffg3 -dSAFER -sOutputFile=" + output + " " + name + " -c quit"

    #si no existe O se fuerza =>
    if os.path.isfile(output)==False or FORCE==True:
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

if __name__ == "__main__":
    parser = ArgumentParser()

    # Add more options if you like
    parser.add_argument("-i", "--input", dest="input_path", default="./cut/",
                      help="input path with PDFs", metavar="DIR")
    parser.add_argument("-o", "--output", dest="output_path", default="./tiff/",
                      help="output path with tiff", metavar="DIR")
    parser.add_argument("-f", "--force", action='store_true',
                    help="force overwrite")
    parser.add_argument("-b", "--blank", dest="blank_filename", default="blank.pdf",
                      help="path to blank PDF file", metavar="FILE")
    args = parser.parse_args()

    INPUT=args.input_path
    OUTPUT_PATH=args.output_path
    FORCE=get_bool(args.force)

    print("pdf path: " + str(INPUT) )
    print("tiff path: " + str(OUTPUT_PATH) )
    print("forzar overwrite: " + str(FORCE) )

    result=load_files(INPUT)

    contfiles = 0
    for f in result:
        contfiles=contfiles+1
        convert(f)

    print("total ficheros: "  + str(contfiles))
    print("ficheros procesados: "  + str(procfiles))
