import argparse

def genJpegs(args):
    inputf = file(args.input,'r')
    outputf = file(args.output,'w')

    for line in inputf:
        line = line.rsplit('files/',1)[1]
        outputf.write(line)
    
    outputf.close
    inputf.close

parser = argparse.ArgumentParser(description='Leave just the tile coords.')
parser.add_argument("-i", "--input", type=str, help="Input file")
parser.add_argument("-o", "--output", type=str, help="Output file")

args = parser.parse_args()
print args

genJpegs(args)
