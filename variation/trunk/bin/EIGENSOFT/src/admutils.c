#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
// #include <openssl/md2.h>
#include "admutils.h" 

#include  "packit.h"   
static int fastdupnum = 10 ;
static int snptab = NO ;

int hashit (char *str)  ;

int countcol(char *fname) {
 FILE *fp ;
 int t ;

 openit(fname, &fp, "r") ;
 t = countcolumns(fp) ;
 fclose(fp) ;
 return t ;
}


int countcolumns(FILE *fp)
{  /* count number of text columns separated by whitespace */
  int i=0,c;
  fpos_t ptr;

  if (fgetpos(fp,&ptr)) {
    printf("error counting columns\n");
    return 0;
  }

  while ( (c = getc(fp)) != '\n' ) {
    if (isgraph(c)) {
      i++;
      while (isgraph(c = getc(fp))) {}
      ungetc(c,fp);
    }
  }
  fsetpos(fp,&ptr);
  return i;
}

void sett1(double *tt, double theta, int numstates) 
{
    if (numstates==2)  { 
     tt[0] = 1.0-theta ;
     tt[1] = theta ;
     tt[2] = 0.0 ;
    }
    if (numstates==3)  { 
     tt[0] = (1.0-theta)*(1.0-theta) ;
     tt[1] = 2.0*theta*(1.0-theta) ;
     tt[2] = theta*theta ;
    }
}

void sett1r(double *tt, double theta, int numstates, double risk)
{
  double y ;
  sett1(tt, theta, numstates) ;
  tt[1] *= risk ;
  tt[2] *= risk*risk ;  
  y = asum(tt, numstates) ;
  vst(tt, tt, 1.0/y, numstates) ;
}

void gettln(SNP *cupt, Indiv *indx, 
  double *ptheta, double *plambda, int *pnumstates, int *pignore) 
/* set theta, lambda numstates */
{
   double theta, lambda ; 
   int numstates, chrom, ignore ;

   theta  = indx->theta_mode ;
   lambda = indx->lambda_mode ;
   ignore = indx->ignore ;
   numstates = 3 ;

   chrom = cupt -> chrom ;

   if (chrom == 23) { 
    theta  = indx->Xtheta_mode ;
    lambda = indx->Xlambda_mode ;
    if (indx -> gender == 'M') numstates = 2;
    if (indx -> gender == 'U') ignore = YES ;
   }
   if (ptheta !=NULL) *ptheta = theta ;
   if (plambda != NULL) *plambda = lambda ;
   if (pnumstates != NULL) *pnumstates = numstates ;
   if (pignore != NULL) *pignore = ignore ;
}


void puttln(SNP *cupt, Indiv *indx, 
  double ptheta, double plambda) 
/* put theta, lambda */
{

   int chrom ;


   chrom = cupt -> chrom ;

   if (chrom == 23) { 
    indx->Xtheta_mode = ptheta;
    indx->Xlambda_mode  = plambda ;
    return ;
   }
   indx->theta_mode = ptheta;
   indx->lambda_mode  = plambda ;
   return ;
}


double hwcheck (SNP *cupt, double *cc) 
{

      int i, n, g ;


      vzero(cc, 3) ;

      n = cupt -> ngtypes ;
      for (i=0; i<n; i++)  {
        g = getgtypes(cupt, i) ;
        if (g<0) continue ;
        ++cc[g] ;
     }
     return (hwstat(cc)) ;

}

double hwcheckx (SNP *cupt, Indiv **indm, double *cc) 
// deals with X  
{

      int i, n, g, ignore, numstates ;
      Indiv *indx ;
      double t, l ; 


      vzero(cc, 3) ;

      n = cupt -> ngtypes ;
      for (i=0; i<n; i++)  {
        indx = indm[i] ;
        gettln(cupt, indx, &t, &l, &numstates, &ignore) ;
        if (ignore) continue ; 
        if (numstates != 3) continue ;
        g = getgtypes(cupt, i) ;
        if (g<0) continue ;
        ++cc[g] ;
     }
     return (hwstat(cc)) ;

}



void cntit(double *xc, SNP *c1, SNP *c2) 
{
 int n, i, e, f ;

 n = MIN(c1->ngtypes, c2->ngtypes) ;
 vzero(xc, 9) ;
 for (i=0; i<n; i++) {  
  e = getgtypes(c1, i) ;
  f = getgtypes(c2, i) ;
  if (e<0) continue ;
  if (f<0) continue ;
  ++xc[3*e+f] ;
 }
}

/******** UTILITY FUNCTIONS **********/
void fataly(const char *name)
{
  printf("%s",name);
  exit(1);
}

int compare_doubles (const void *a, const void *b)
{
  const double *da = (const double *) a;
  const double *db = (const double *) b;

  return (*da > *db) - (*da < *db);
}

void pcheck (char *name, char x) 
{
 
  if (name != NULL) return ;
  if (x != CNULL) 
   fatalx ("parameter %c compulsory\n",x) ;
  else fatalx("missing argument\n") ;
}

void printm(double **M, int numstates)  
{
     int i,j ;
     printf("M:\n") ;
     for (i=0; i<numstates; i++)  {  
      for (j=0; j<numstates; j++)  {  
       printf("%9.3f ", M[j][i]) ;
      }
      printf("\n") ;
     }
}


int numvalidgtypes(SNP *cupt) 
{
  int nvalid, n, i, k ;
  if (cupt -> isfake) return 0 ;
  n = cupt -> ngtypes ;
  nvalid = 0 ;
  for (i=0; i<n; i++)  {
   k = getgtypes(cupt, i) ;
   if (k >= 0) ++nvalid ;  
  }
  return nvalid ;
}  

int numvalids(Indiv *indx, SNP **snpmarkers, int fc, int lc)  
{ 
  SNP *cupt ; 
  int idnum, numstates, ignore ;  
  int k, nval= 0 ; 
 
  if (fc>lc) return 0 ; 
  if (lc<0) return 0 ; 
  idnum = indx -> idnum ; 
  for (k=fc; k<=lc; ++k) {   
    cupt = snpmarkers[k] ; 
    if (cupt -> isfake) continue ; 
    gettln(cupt, indx, NULL, NULL, &numstates, &ignore) ; 
    if (ignore) continue ; 
    if (cupt -> ngtypes == 0) continue ; 
    if (getgtypes(cupt, idnum) >= 0) ++nval ; 
  } 
  return nval ; 
} 

double malefreq(Indiv **indmarkers, int numindivs) 

/* pop freq of males in sample */
{
   int i ;
   Indiv *indx ; 
   double cmale, cfemale ;

   cmale = 0 ;
   for (i=0; i<numindivs; ++i) { 
    indx = indmarkers[i] ;
    if (indx -> gender == 'M') ++cmale ;
   }

   cmale /= (double) numindivs ;

   return cmale ;
}

int isimatch(int a, int b)
{
   if (a < 0)  return YES ;
   if (b < 0)  return YES ;
   if (a==b)   return YES ;
   return NO;
}

void gethpos(int *fc, int *lc, SNP **snpm, int numsnps,  
 int xchrom, int lo, int hi)  
{ 
   int k, xfc, xlc, pos ; 
   SNP *cupt ; 
 
   xfc = 9999999 ; 
   xlc = -9999999 ; 
   for (k=0; k<numsnps; k++) {  
    cupt = snpm[k] ; 
    if (cupt -> chrom != xchrom) continue ; 
    pos = cupt -> physpos ; 
    if (pos < lo) continue ; 
    if (pos > hi) continue ; 
    xfc = MIN(xfc, k) ; 
    xlc = MAX(xlc, k) ; 
   } 
   *fc = xfc ;  
   *lc = xlc ; 
} 

void makedir (char * dirname) 
// AT wrote original 
// sets up directory.  Will fail hard if directory does not 
// exist and can't be made 
{
 int fdir ; 
   fdir  = open(dirname,O_RDONLY,0);
   if (fdir >= 0) {  
    close (fdir) ;
    return ;
   }
   fdir = mkdir(dirname,0775);
   if (fdir < 0) {  
    perror("makedir") ;
    fatalx("(makedir) directory %s not created\n") ;
   }
   printf("Created a new directory %s\n",dirname);
}


int
indxindex(char **namelist, int len, char *strid)  
// look for string in list
{
     int k ; 
     for (k=0; k< len; k++) {  
      if (strcmp(namelist[k], strid) == 0) return k ;
     }
     return -1 ;
}

int indindex(Indiv **indivmarkers, int numindivs, char *indid) 
/* hash table would be good here */
{
     int k ; 
     for (k=0; k< numindivs; k++) {  
      if (strcmp(indivmarkers[k] -> ID, indid) == 0) return k ;
     }
     return -1 ;
}

int snpindex(SNP **snpmarkers, int numsnps, char *snpid) 
{
     int k ; 
     char **ss ;  

     if (snptab==NO) {  
// set up hash table
      snptab = YES ;
      ZALLOC(ss, numsnps, char *) ;
      for (k=0; k< numsnps; k++) {  
       ss[k] = strdup(snpmarkers[k] -> ID) ;
      }
      xloadsearch(ss, numsnps) ;
      freeup(ss, numsnps) ;
     }
     
     k = xfindit(snpid) ;
     return k ;
}
void freesnpindex() 
{
 snptab = NO ; 
 xdestroy() ;
}

int ignoresnp(SNP *cupt)  
{
 if (cupt -> ignore) return YES ;
 if (cupt -> isfake) return YES ;
 if (cupt -> ngtypes == 0) return YES ;
 if (cupt -> isrfake) return NO ; 
 return NO ;
}

double entrop(double *a, int n) 
{
  int i ;
  double ysum, t, ans ;

  ans = 0.0 ; 
  ysum = asum(a,n) ;
  for (i=0; i<n ; i++) {
   t = a[i]/ysum ;
   ans += xxlog2(t) ;
  }
  return -ans ;
}
double xxlog2(double t) 
{
  if (t<=0.0) return t ;
  return t * log(t) / log(2.0) ;
}

void 
testnan(double *a, int n) 
{
  int i ;

  for (i=0; i<n; i++) {
   if (!finite(a[i])) fatalx("(testnan) fails:  index %d\n",i) ;
  }
}
void getgall(SNP *cupt, int *x, int n) 
{
  int k, t, a ;
  unsigned char b, w ;

  if (cupt -> gtypes == NULL) {          
   ivclear(x, -1, n) ;
   return ;
  }

  if (!packmode) {  
   copyiarr(cupt-> gtypes, x, n) ;
   return ;
  }

  k = 0 ;
  for (a=0; 4*a<n; ++a) {  
   w = cupt -> pbuff[a] ;
   for (t = 0; t < 4 ; t++)  { 
    b = w >> 2*(3-t) ;
    x[k] = b & 3 ;
    ++k ; 
    if (k>=n) break ;
   }
  }
}

int getgtypes(SNP *cupt, int k) 
{
  char *buff ; 
  int  g ;

  if (cupt -> gtypes == NULL) return -1 ;

  if (packmode)  {  
   buff = cupt -> pbuff ;          
   g = rbuff((unsigned char *)buff, k) ;  
   if (g==3) g = -1 ; 
   return g ;
  }

  return cupt -> gtypes[k] ;
}

void putgtypes(SNP *cupt, int k, int val) 
{
  char *buff ; 
  int   g ;

  if (k>= cupt -> ngtypes) fatalx("(putgtypes)\n") ;
  if (packmode)  {  
   buff = cupt -> pbuff ;          
   g = val ; 
   if (g <0) g=3 ;
   wbuff((unsigned char *)buff, k, g) ;  
   return ;
  }
  cupt ->gtypes[k] = val ;
}

int getep(SNP *cupt, int k) 
{
  char *buff ; 
  int   g ;

  if (cupt -> gtypes == NULL) return -1 ;
  if (k>= cupt -> ngtypes) return -1 ; 
   buff = cupt -> ebuff ;          
   g = rbuff((unsigned char *)buff, k) ;  
   if (g==3) g = -1 ; 
   return g ;

}

void putep(SNP *cupt, int k, int val) 
{
  char *buff ; 
  int   g ;

  if (k>= cupt -> ngtypes) fatalx("(putep)\n") ;
   buff = cupt -> ebuff ;          
   g = val ; 
   if (g <0) g=3 ;
   wbuff((unsigned char *)buff, k, g) ;  
   return ;

}

int hasharr(char **xarr, int nxarr)  
// in application ordering  matters so we hash order dependent 
{
  
   int hash, thash, i, n ;  

   hash = 0 ;  

   for (i=0; i< nxarr; i++)  { 
    thash = hashit(xarr[i]) ;
    hash *= 17 ;
    hash ^= thash ;
   }
   return hash ;
}
int hashit (char *str) 
{
/* simple and unimpressive hash function NJP */
   int j, len, hash ; 

   hash = 0 ;
   len = strlen(str) ;

   for (j=0; j<len ; j++) {  
     hash *= 23 ;
     hash += (int) str[j] ;
   }
   return hash ;
}
void
wbuff(unsigned char *buff, int num, int g) 
// low level routine writes 2 bits to buffer 
// g should be 0 1 2 or 3   (3 = missing) 
{

   int wnum, wplace ;  
   unsigned char mm, msk, ones ;
   static int ncall = 0 ;
 
   if ((g<0) || (g>3)) fatalx("(wbuff) invalid g value\n", g) ;

   ++ncall ;

   msk = 3 << 6 ;  
   mm = g << 6 ;
   ones = 0XFF  ;

   wnum = num/4 ;  
   wplace = num%4 ;

   mm = mm >> (wplace * 2) ;  
   msk = (msk >> (wplace *2)) ^ ones ;  
   buff[wnum] &= msk ;
   buff[wnum] |= mm ;

/**
     printf("zz %d  %d %d %d %02x\n", num, wnum, wplace, g, buff[wnum]) ;
     printf("yyy %d %d\n", g, rbuff(buff,num)) ;
*/
}
int
rbuff(unsigned char *buff, int num) 
{
   int wnum, wplace, rshft ;  
   unsigned char  b ;
   static int ncall = 0 ;
 
// ++ncall ;


   wnum = num >> 2 ;
   wplace = num & 3 ; 

   rshft = (3-wplace) << 1 ;
   b = buff[wnum] >> rshft ;

   b = b & 3 ;
   return b ;
}
int ridfile(char *fname) 
{
  int t ;

  chmod(fname, 0777) ;
  t = unlink(fname) ;
  return t ;
}

// fast dup code
void setfastdupnum(int  num) 
{
 fastdupnum = num ;
}

void
fastdupcheck(SNP **snpmarkers, Indiv **indivmarkers, int numsnps, int numindivs)
{
 SNP *cupt ; 
 Indiv *indx ;
 int *gtypes ;
 int i, j, k, n ;
 int *snphets, *indsnp, tab[15], ww[15], **codeit, *cc, g, *cbuff ; 
 int *buff, val, vv, lbuff, itry, ilo, ihi ;

 ZALLOC(gtypes, numindivs, int) ;
 ZALLOC(cbuff, 2*numindivs, int) ;
 ZALLOC(codeit, numindivs, int *) ;
 ZALLOC(snphets, numsnps, int) ;
 ZALLOC(indsnp, numsnps, int) ;
 for (i=0; i<numsnps; i++) {  
  cupt = snpmarkers[i]  ;
  if (cupt -> ignore) continue ;  
  if (cupt -> isfake) continue ; 
  if (cupt -> chrom > 22) continue ;
  grabgtypes(gtypes, cupt, numindivs) ;
  for (k=0; k<numindivs; k++) { 
    if (gtypes[k] == 1) ++snphets[i] ;
  }
 }
 ivst(snphets, snphets, -1, numsnps) ;
 isortit(snphets, indsnp, numsnps) ;
// make fastdupnum shots at exact match on 15 snps */
 for (itry = 1; itry < fastdupnum; itry++) {
  ilo = 15*itry ;  
  if ((ilo+15)>=numsnps) break ;
  for (i=0; i<15; i++) { 
   j = indsnp[i+ilo] ; 
   tab[i] = j ;
  }
  n = 0 ;
  for (k=0; k<numindivs; ++k) {  
   indx = indivmarkers[k] ; 
   if (indx -> ignore) continue ;
   for (i=0; i<15; i++) { 
    j = tab[i] ;
    g  = getgtypes(snpmarkers[j], k) ;
    if (g<0) break ;
    ww[i] = g ; 
   }
   if (g < 0 ) continue ;
   cc = codeit[n] = cbuff+2*n ;
   cc[0] = kcode(ww, 15, 4) ;
   cc[1] = k ; 
   ++n  ;
  }


  if (n==0) continue ;
  ipsortit(codeit, NULL, n, 2) ;  

  buff = gtypes ; lbuff = 0; val = -1 ;  

  for (i=0; i<n; i++)  {  
   cc=codeit[i] ;  
   vv = cc[0] ;
   if (vv != val) {  
    cdup(snpmarkers, indivmarkers, numsnps, buff, lbuff) ;
    lbuff = 0 ; 
    val = vv ; 
   }
   buff[lbuff] = cc[1] ;
   ++lbuff ;
  }
  cdup(snpmarkers, indivmarkers, numsnps, buff, lbuff) ;
 }  // itry

 free(snphets) ;
 free(indsnp) ;
 free(gtypes) ;
 free(codeit) ;
 free(cbuff) ;
}

void cdup(SNP **snpm, Indiv **indm, int nsnp, int *buff, int lbuff) 
{ 
 static int ncall = 0 ;
 SNP * cupt ;
 Indiv *inda, *indb ;
 double ytot, yhit ;
 int g1, g2, k1, k2, match, nomatch ;
 int i1, i2, j ;
#define MINMARK 200 


 if (lbuff <= 1) return ;
 ++ncall ;
/**
 printf ("cdup: %d\n", ncall) ;
 printimat(buff, lbuff, 1) ;
*/
 for (i1=0; i1<lbuff; ++i1) {  
  for (i2=i1+1; i2<lbuff; ++i2) {
   k1 = buff[i1] ; 
   k2 = buff[i2] ;  
   match = nomatch = 0 ;
   for (j=0; j<nsnp; ++j) {  
    cupt = snpm[j] ;
    if (cupt -> ignore) continue ;
    if (cupt -> isfake) continue ;
    g1 = getgtypes(cupt, k1) ;
    g2 = getgtypes(cupt, k2) ;
    if ( (g1<0) || (g2<0) ) continue ;
    if (g1==g2) ++match ;
    if (g1!=g2) ++nomatch ;
   }

   inda = indm[k1] ;
   indb = indm[k2] ;
   ytot = (double) (match + nomatch) ;
   if (ytot< MINMARK) continue ;
   yhit = ((double) match) / ytot  ; 
   if (yhit>0.75) { 
    printdup(snpm, nsnp, inda, indb, match, nomatch)  ;
    killdup(inda, indb, snpm, nsnp) ;
   }
  }
 }
}

void killdup(Indiv *inda, Indiv *indb, SNP **snpm, int nsnp) 
{
       int t1, t2 ;
       Indiv *indx ;

       t1 = numvalids(inda, snpm, 0, nsnp-1) ;
       t2 = numvalids(indb, snpm, 0, nsnp-1) ;
       indx = inda ; 
       if (t1>t2) indx = indb ;
       indx -> ignore = YES ; 
       printf("dup.  %s ignored\n", indx -> ID) ;
}

void printdup(SNP **snpm, int numsnp, Indiv *inda, Indiv *indb, int nmatch, int nnomatch) 
{
       int t1, t2 ;
       char status1[30], status2[30] ;

       if (inda -> ignore) return ;
       if (indb -> ignore) return ;


       t1 = numvalids(inda, snpm, 0, numsnp-1) ;
       t2 = numvalids(indb, snpm, 0, numsnp-1) ;
       printf("dup? %s %s \n match: %d mismatch: %d   %d %d\n", 
        inda->ID, indb -> ID, nmatch, nnomatch, t1, t2) ;
       /*AT: 1/20/05 adding the status field to output*/
       /* NJP added valid coun */
       strcpy(status1, "Control") ; 
       if (inda->affstatus) strcpy(status1,"Case") ; 
       strcpy(status2, "Control") ; 
       if (indb->affstatus) strcpy(status2,"Case") ; 
       if(strcmp(status1,status2))
         {
           printf("status_1: %s status_2: %s\n", 
                  status1, status2) ;
         }
}

int kcode(int *w, int len, int base) 
{
 int i, t ;
 t = 0; 
 for (i=0; i<len; i++) {  
  t *= base ;  
  t += w[i] ;
 }
 return t ;
}

int 
 grabgtypes(int *gtypes, SNP *cupt, int numindivs) 
{

 int k ;

 for (k=0; k<numindivs; k++) { 
  gtypes[k] = getgtypes(cupt, k) ;
 }

}

double kurtosis(double *a, int n) 
{

  double  y1, y2, y4 ;  
  double *w  ;

  ZALLOC(w, n, double) ;

  y1 = asum(a,n) / (double) n ;  
  vsp(w, a, -y1, n) ; 
  
  y2 = asum2(w, n) / (double) n ;
  vst(w, w, 1.0/sqrt(y2), n) ;

  vvt(w, w, w, n) ;  

  y4 = asum2(w, n) / (double) n ;


  free(w) ;
  return y4 ; 

}

int getlist(char *name, char **list) 
{
#define MAXSTR 128
#define MAXFF 5
  FILE *fff ;
  char line[MAXSTR] ;
  char *spt[MAXFF] ;
  char *sx ;
  int nsplit, num=0 ;

  num = 0;
  if (name == NULL) fatalx("(numlines)  no name")  ;
  openit(name, &fff, "r") ;
  while (fgets(line, MAXSTR, fff) != NULL)  {
   nsplit = splitup(line, spt, MAXFF) ;
   if (nsplit==0) continue ;
   sx = spt[0] ;
   if (sx[0] == '#') {
    freeup(spt, nsplit) ;
    continue ;
   }
   list[num] = strdup(sx) ;
   ++num ;
   freeup(spt, nsplit) ;
  }
  fclose(fff) ;
  return num ;
}
void printvers(char *progname, char *vers) 
{
 printf("## %s  version: %s", progname, vers) ; 
 printnl() ;
}






