#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>
#include <math.h>

#include <nicklib.h>  
#include "admutils.h" 

#define MAXSTR 512 
#define LONGSTR 10000
#define MAXFF  50
#define MAXCH  100
#define MTCHROM 90 
#define XYCHROM 91
#define BADCHROM 99
#define GDISMUL 1000000
// multiplier for gdis to make integer for sort

enum outputmodetype  { 
ANCESTRYMAP, 
EIGENSTRAT, 
PED, 
PACKEDPED,
PACKEDANCESTRYMAP  }  ;  


typedef struct {
  char ID[IDSIZE];
  double gpos ; 
  double ppos ; 
  int chrom ;
  int nn[4] ;
  int ignore ;
  int isrfake ; 
  char alleles[2] ;
  int inputrow ;
  int cuptnum ;
}  SNPDATA ;


int numfakes(SNPDATA **snpraw, int *snpindx, int nreal, double spacing)  ;
double nextmesh(double val, double spacing) ;
double interp (double l, double r, double x, double al, double ar) ;

int
loadsnps(SNP **snpm, SNPDATA **snpraw, 
  int *snpindx, int nreal, double spacing, int *numignore) ;

int readsnpdata(SNPDATA **snpraw, char *fname)  ; 
int readinddata(Indiv **indivmarkers, char *fname) ;
int readindpeddata(Indiv **indivmarkers, char *fname)  ;
void pedname(char *name, char *sx0, char *sx1) ;

int readtldata(Indiv **indivmarkers, int numind, char *fname) ;
int readindval(Indiv **indivmarkers, int numind, char *fname) ;
int readfreqdata(SNP **snpm, int numsnps, char *fname) ;
void clearsnp(SNP *cupt) ;
int rmsnps(SNP **snpm, int numsnps) ;
void clearind(Indiv **indm, int numind)  ;
void cleartg(Indiv **indm, int nind)  ;

double mknn(int *nn, int  n0, int n1) ;
int getsnps(char *snpfname, SNP ***snpmarkpt, double spacing,
 char *badsnpname, int *nignore, int numrisks) ;
int getsizex(char *fname) ;
int getindivs(char *indivfname, Indiv ***indmarkpt) ;

int setstatus(Indiv **indm, int numindivs, char *smatch)  ;
int setstatusv(Indiv **indm, int numindivs, char *smatch, int val)  ;

int getgenos(char *genoname, SNP **snpmarkers, Indiv **indivmarkers, 
 int numsnps, int numindivs, int nignore)  ;
void getgenos_list(char *genotypelist, SNP **snpmarkers, Indiv **indivmarkers, 
 int  numsnps, int numindivs, int nignore) ; 
void printsnps(char *snpoutfilename, SNP **snpm, int num, 
  Indiv **indm, int printfake, int printvalids) ;
int checkxval(SNP *cupt, Indiv *indx, int val) ;
void printdata(char *genooutfilename, char *indoutfilename, 
  SNP **snpm, Indiv **indiv, int numsnps,int numind, int packmode);
int readgdata(Indiv **indivmarkers, int numind, char *gname) ; 
int numvalidind(Indiv **indivmarkers, int  numind)   ;
int numvalidgtind(SNP **snpm, int numsnps, int ind)  ;
int numvalidgt(Indiv **indivmarkers, SNP *cupt)   ;
int numvalidgtx(Indiv **indivmarkers, SNP *cupt, int affst)  ;
int getweights(char *fname, SNP **snpm, int numsnps)   ;
void outpack(char *genooutfilename, SNP **snpm, Indiv **indiv, int numsnps, int numind)  ;
int ispack(char *gname) ;
int iseigenstrat(char *gname) ;
void inpack(char *genooutfilename, SNP **snpm, Indiv **indiv, int numsnps, int numind)  ;
int inpack2(char *genooutfilename, SNP **snpm, Indiv **indiv, int numsnps, int numind)  ;
int ineigenstrat(char *genooutfilename, SNP **snpm, Indiv **indiv, int numsnps, int numind)  ;
void setepath(SNP **snpm, int n) ;
void clearepath(char *xpack) ;

// pedfile support
int getpedgenos(char *genoname, SNP **snpmarkers, Indiv **indivmarkers, 
 int numsnps, int numindivs, int nignore) ;
void genopedcnt(char *genoname, int **gcounts, int nsnp) ;

int pedval(char *sx) ;
int xpedval(char c) ;
int ptoachrom(char *ss) ;

void setgref(int **gcounts, int nsnp, int *gvar, int *gref) ;
void cleargdata(SNP **snpmarkers, int numsnps, int numindivs) ;
void setgenotypename(char **gname, char *iname) ;
void settersemode(int mode) ;

void dobadsnps(SNPDATA **snpraw, int nreal, char *badsnpname) ;
int snprawindex(SNPDATA **snpraw, int nreal, char *sname) ;
int readsnpmapdata(SNPDATA **snpraw, char *fname)  ;
int checkfake(char *ss)  ;

void
outeigenstrat(char *snpname, char *indname, char *gname, 
SNP **snpm, Indiv **indiv, int numsnps, int numind) ;

void
outped(char *snpname, char *indname, char *gname, 
SNP **snpm, Indiv **indiv, int numsnps, int numind, int ogmode) ;

void
outpackped(char *snpname, char *indname, char *gname, SNP **snpm, Indiv **indiv, 
  int numsnps, int numind, int ogmode) ;

void setbedbuff(char *buff, int *gtypes, int numind) ;
int bedval(int g) ;
int str2chrom(char *ss) ;

void outindped(char *indname, Indiv **indiv, int numind, int ogmode)  ;

void
printmap(char *snpname, SNP **snpm, int numsnps, Indiv **indiv) ;

int maxlinelength(char *fname)  ;
int checksize(int numindivs, int numsnps, enum outputmodetype outputmode) ;

void setomode(enum outputmodetype *outmode, char *omode)  ;

void
outfiles(char *snpname, char *indname, char *gname, SNP **snpm, 
  Indiv **indiv, int numsnps, int numind, int packem, int ogmode) ;

void snpdecimate(SNP **snpm, int nsnp, int decim, int mindis, int maxdis)  ;
void decimate(SNP **cbuff, int n, int decim, int mindis, int maxdis) ;
int vvadjust(double *cc, int n, double *pmean) ;
int killhir2(SNP **snpm, int numsnps, int numind, double physlim, double genlim, double rhothresh) ; 
void freecupt(SNP **cupt) ;
