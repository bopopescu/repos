
class PhenotypeData:
    """
    A class that knows how to read simple tsv or csv phenotypefiles and facilitates their interactions with SnpsData objects.    
    """
    accessions = []
    phenotypeNames = []
    phenotypeValues = [] # list[accession_index][phenotype_index]

    def __init__(self, accessions, phenotypeNames, phenotypeValues):
        self.accessions = accessions
        self.phenotypeNames = phenotypeNames
        self.phenotypeValues=phenotypeValues

    def orderAccessions(self, ordering):
        """
        Removes accessions from the data.
        """
        newAccessions = []
        newPhenotVals = []
        print len(indicesToKeep)
        for i in indicesToKeep:
            newAccessions.append(self.accessions[i])
            newPhenotVals.append(self.phenotypeValues[i])
        self.accessions = newAccessions
        self.phenotypeValues = newPhenotVals
        
    def removeAccessions(self, indicesToKeep):
        """
        Removes accessions from the data.
        """
        newAccessions = []
        newPhenotVals = []
        print len(indicesToKeep)
        for i in indicesToKeep:
            newAccessions.append(self.accessions[i])
            newPhenotVals.append(self.phenotypeValues[i])
        self.accessions = newAccessions
        self.phenotypeValues = newPhenotVals
        
    def writeToFile(self, outputFile, phenotypes=None, delimiter=','):
        print "Writing out phenotype file:",outputFile
        outStr = "ecotype_id"
        if phenotypes:
            for i in phenotypes:
                name = self.phenotypeNames[i]
                outStr += delimiter+name
            outStr += '\n'
            for i in range(0,len(self.accessions)):
                outStr += str(self.accessions[i])
                for j in phenotypes:
                    outStr += delimiter+str(self.phenotypeValues[i][j])
                outStr +="\n"
        else:
            for name in self.phenotypeNames:
                outStr += delimiter+name
            outStr += '\n'
            for i in range(0,len(self.accessions)):
                outStr += str(self.accessions[i])
                for j in range(0, len(self.phenotypeNames)):
                    outStr += delimiter+str(self.phenotypeValues[i][j])
                outStr +="\n"

        f = open(outputFile,"w")
        f.write(outStr)
        f.close()

def readPhenotypeFile(filename, delimiter=',', missingVal='NA', accessionDecoder=None, type=1):
    """
    Reads a phenotype file and returns a phenotype object.
    """
    f = open(filename,"r")
    lines = f.readlines()
    f.close()
    shift = 2
    if type==2:
        shift = 1
    line = (lines[0].rstrip()).split(delimiter)
    phenotypeNames = line[shift:]
    accessions = []
    phenotypeValues = []
    for i in range(1, len(lines)):
        line = (lines[i].rstrip()).split(delimiter)
        if accessionDecoder:
            accessions.append(accessionDecoder[line[0]])
        else:
            accessions.append(line[0])
        phenotypeValues.append(line[shift:])

    return PhenotypeData(accessions,phenotypeNames,phenotypeValues)
    




def _runTest_():
    import dataParsers
    filename = "/Users/bjarni/Projects/Python-snps/phenotypes.tsv"
    #phed = readPhenotypeFile(filename,accessionDecoder=dataParsers.accessionName2EcotypeId)    
    phed = readPhenotypeFile(filename,delimiter='\t')    
    print phed.accessions
    print phed.phenotypeNames
    #print phed.phenotypeValues
        
if __name__ == '__main__':
	_runTest_()

