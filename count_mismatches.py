'''
count_mismatches.py - count the number of mismatches per gene
====================================================

:Author: Ian Sudbery
:Release: $Id$
:Date: |today|
:Tags: Python

Purpose
-------

Count the number of high quality mismatches per gene per base sequenced. Will discard reads marked as duplicate

Usage
-----

.. Example use case

Example::

   python cgat_script_template.py

Type::

   python cgat_script_template.py --help

for command line help.

Command line options
--------------------

'''

import sys
from collections import defaultdict

from CGAT import Experiment as E
from CGAT import GTF
from CGAT import IOTools
from CGAT.IndexedFasta import IndexedFasta
import textwrap
import pysam

def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.OptionParser(version="%prog version: $Id$",
                            usage=globals()["__doc__"])

    parser.add_option("-b", "--bamfile", dest="bam", type="string",
                      help="BAM formated alignment file to test. Should have MD and NH tags set")
    parser.add_option("-t", "--quality-threshold", dest="threshold", type="int",
                       default=30,
                       help="minimum quality threshold for a mismatched base to count")
    parser.add_option("-f", "--fasta-path", dest="fastapath", type="string",
                       help="path to indexed fasta file for genome of choice")
    # add common options (-h/--help, ...) and parse command line
    (options, args) = E.Start(parser, argv=argv)

    bamfile = pysam.AlignmentFile(options.bam)
    fastafile = IndexedFasta(options.fastapath)
    options.stdout.write("\t".join(["gene_id",
                                    "mismatches",
                                    "bases",
                                    "low_qual",
                                    "a","t","c","g",
                                    "a_to_t","a_to_g","a_to_c",
                                    "t_to_a","t_to_g","t_to_c",
                                    "g_to_a","g_to_t","g_to_c",
                                    "c_to_a","c_to_t","c_to_g"]) + "\n")

    for gene in GTF.flat_gene_iterator(GTF.iterator(options.stdin)):

        start = min(e.start for e in gene)
        end = max(e.end for e in gene)  

        seq = fastafile.getSequence(gene[0].contig, "+", start, end)

        reads = bamfile.fetch(gene[0].contig, start, end)

        gene_id = gene[0].gene_id
        mm_count = 0
        base_count = 0
        skipped = 0
        matched_bases = defaultdict(int)
        transition = {"a_to_t":0,"a_to_g":0,"a_to_c":0,"t_to_a":0,"t_to_g":0,
        "t_to_c":0,"g_to_a":0,"g_to_t":0,"g_to_c":0,"c_to_a":0,"c_to_t":0,
        "c_to_g":0}
        for read in reads:

            if read.is_unmapped:
                continue
            if read.is_duplicate:
                continue

            if read.get_tag("NH") > 1:
                continue
            qualities = read.query_qualities

            alignment = read.get_aligned_pairs(with_seq=True)

            alignment = [base for base in alignment 
                         if not base[0] is None and not base[1] is None]

           
            base_count += sum(1 for base in alignment
                          if start <= base[1] < end and
                          base[2].lower() != "n")
                          
	    matched = [base for base in alignment
 		       if not base[2].islower() and
                       start <= base[1] < end]            
          
            for base in matched:
                if seq[(base[1])-start].lower() != base[2].lower():
                       print read.query_alignment_sequence
                       print seq[(alignment[0][1]-start):(alignment[-1][1]-start)]
                       print seq[((base[1]-10)-start):((base[1]+10)-start)].lower()
                       print read.tostring(bamfile)
                       print start, end
                       print seq[(base[1])-start]
                       print base[2]
                       print base[0]
                       print base[1]-start                      
                       print seq[(alignment[0][1]-start):(alignment[-1][1]-start)].upper()[base[0]]
                       print ((alignment[0][1]-start) + base[0])
                       print seq[(base[1])-start]
                       print alignment[0][1]-start
                       print read.get_aligned_pairs(with_seq=True)
                       print textwrap.fill(seq,50)
                       raise ValueError
                else:
		       matched_bases[base[2].lower()] += 1 
            
            if read.get_tag("NM") == 0:
                continue

            # mismatches
            

            readseq = read.query_alignment_sequence

            mismatches = [base for base in alignment
                          if base[2].islower() and
                          start <= base[1] < end and
		          qualities[base[0]] >= options.threshold and
                          base[2].lower() != "n"]
            
            total_mm = sum(1 for base in alignment
                        if base[2].islower() and
                        start <= base[1] < end and
                        base[2].lower() != "n")
            
            hq_mm = sum(1 for base in mismatches
                        if qualities[base[0]] >= options.threshold and
                        base[2].lower() != "n")


            for base in mismatches:
                genomebase = base[2].lower()
                readbase = readseq[base[0]].lower()
                try:
                    transition["%s_to_%s"%(genomebase, readbase)] += 1
                except KeyError:
                    print transition
                    print read.query_alignment_sequence.upper() 
                    print seq[(alignment[0][1]-start):(alignment[-1][1]-start)].upper()
	            print read.tostring(bamfile)
                    raise

	    
		    
            mm_count += hq_mm
            skipped += total_mm - hq_mm

        outline = "\t".join(map(str,[gene_id,
                                     mm_count,
                                     base_count,
                                     skipped,
                                     matched_bases['a'],
                                     matched_bases['t'],
                                     matched_bases['c'],
                                     matched_bases['g'],
                                     transition['a_to_t'],
                                     transition['a_to_g'],
                                     transition['a_to_c'],
                                     transition['t_to_a'],
                                     transition['t_to_g'],
                                     transition['t_to_c'],
                                     transition['g_to_a'],
                                     transition['g_to_t'],
                                     transition['g_to_c'],
                                     transition['c_to_a'],
                                     transition['c_to_t'],
                                     transition['c_to_g']]))
        options.stdout.write(outline + "\n")

    # write footer and output benchmark information.
    E.Stop()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
