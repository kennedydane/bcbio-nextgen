#!/usr/bin/env python
"""Resort a BAM file karyotypically to match GATK's preferred file order.

Broad's GATK and associated resources prefer BAM files sorted as:

    chr1, chr2... chr10, chr11... chrX

instead of the simple alphabetic sort:

    chr1, chr10, chr2 ...

This takes a sorted BAM files with an alternative ordering of chromosomes
and re-sorts it the karyotypic way.

Usage:
    resort_bam_karyotype.py [<in_files>]

Requires:
    pysam -- http://code.google.com/p/pysam/
"""
import os
import sys

import pysam

def main(in_bams):
    for bam in in_bams:
        sort_bam(bam, sort_by_karyotype)

def sort_bam(in_bam, sort_fn):
    out_file = "%s-ksort%s" % os.path.splitext(in_bam)
    index_file = "%s.bai" % in_bam
    if not os.path.exists(index_file):
        pysam.index(in_bam)

    orig = pysam.Samfile(in_bam, "rb")
    chroms = [(c["SN"], c) for c in orig.header["SQ"]]
    new_chroms = chroms[:]
    new_chroms.sort(sort_fn)
    remapper = id_remapper(chroms, new_chroms)
    new_header = orig.header
    new_header["SQ"] = [h for (_, h) in new_chroms]

    new = pysam.Samfile(out_file, "wb", header=new_header)
    for (chrom, _) in new_chroms:
        for read in orig.fetch(chrom):
            read.rname = remapper[read.rname]
            read.mrnm = remapper[read.mrnm]
            new.write(read)

def id_remapper(orig, new):
    """Provide a dictionary remapping original read indexes to new indexes.

    When re-ordering the header, the individual read identifiers need to be
    updated as well.
    """
    new_chrom_to_index = {}
    for i_n, (chr_n, _) in enumerate(new):
        new_chrom_to_index[chr_n] = i_n
    remap_indexes = {}
    for i_o, (chr_o, _) in enumerate(orig):
        remap_indexes[i_o] = new_chrom_to_index[chr_o]
    remap_indexes[None] = None
    return remap_indexes

def sort_by_karyotype(one, two):
    """Sort function to order reads by karyotype.
    """
    return cmp(_split_to_karyotype(one[0]),
               _split_to_karyotype(two[0]))

def _split_to_karyotype(name):
    parts = name.replace("chr", "").split("_")
    try:
        parts[0] = int(parts[0])
    except ValueError:
        pass
    # anything with an extension (_random) goes at the end
    if len(parts) > 1:
        parts.insert(0, "z")
    return parts

if __name__ == "__main__":
    main(sys.argv[1:])

