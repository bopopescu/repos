#include <stdio.h>
#include "strsubs.h" 
#include "vsubs.h" 
#include "ranmath.h" 
#include "linsubs.h" 

#include "vsubs.h" 
#include "ranmath.h" 
#include "sortit.h" 

#include <values.h>
#include <float.h>

static int ranb1 (int n, double p) ;
static double ranpoiss1(double xm) ;

double gds(  double a)

{
 return rangam(a) ;
}

static double 
randev1(double a)
{
  /**
   Random gamma deviate:  a>=1
   GBEST algorithm  (D.J. BEST: Appl. Stat. 29 p 181 1978
  */
  double          x, d, e, c, g, f, r1, r2;

  e = a - 1.0;
  c = 3.0 * a - 0.75;


  for (;;) {
    r1 = DRAND2();
    g = r1 - (r1 * r1);
    if (g <= 0.0)
      continue;
    f = (r1 - 0.5) * sqrt(c / g);
    x = e + f;
    if (x <= 0.0)
      continue;
    r2 = DRAND2();
    d = 64.0 * r2 * r2 * g * g * g;
    if ((d >= 1.0 - 2.0 * f * f / x) && (log(d) >= 2.0 * (e * log(x / e) - f)))
      continue;
    return (x);
  }

}

static double 
randev0(double a)
{
  /**
   algorithm G6: Gamma for a < 1
  */
  double          r1, r2, x, w;
  double t = 1.0 - a;
  double p = t / (t + a * exp(-t));
  double s = 1.0 / a;
  for (;;) {
    r1 = DRAND2();
    if (r1 <= p) {
      x = t * pow(r1 / p, s);
      w = x;
    } else {
      x = t + log((1.0 - p) / (1.0 - r1));
      w = t * log(x / t);
    }
    r2 = DRAND2();
    if ((1.0 - r2) <= w) {
      if ((1.0 / r2 - 1.0) <= w)
	continue;
      if (-log(r2) <= w)
	continue;
    }
    if (x==0.0) x = 1.0e-20 ;
    return x;

  }

}

double 
ranexp( void)
{
  /**
   exponential mean 1
  */
  double          x, t;
  t = DRAND2();
  x = -log(1.0 - t);
  return x;
}

double
rangam(double a)
{
  /**
   generate gamma deviate mean a
  */
  if (a < 1.0) {
    return( randev0(a));
  }
  if (a == 1.0) {
    return( ranexp());
  }
  return( randev1(a));
}
#define PI 3.14159265358979

double ranpoiss(double xm) 
{
 return poidev(xm) ;
}

double ranpoissx(double xm) 
/* poisson variable conditional on >0 */
{
   double x, t, tc, s, y ;
   int k ;
   if (xm>1.0)  {  
    for (;;) {  
     x = ranpoiss(xm) ;
     if (x>0.5) return x ;
    }
   }
   return ranpoiss1(xm) ;
}

double poidev(double xm)
/** 
 NUM REC pp 293 ff (modified) 
*/
{
	static double sq,alxm,g,oldm=(-1.0);
	double em,t,y;

	if (xm < 12.0) {
		if (xm != oldm) {
			oldm=xm;
			g=exp(-xm);
		}
		em = -1;
		t=1.0;
		do {
			++em;
			t *= DRAND2();
		} while (t > g);
	} else {
		if (xm != oldm) {
			oldm=xm;
			sq=sqrt(2.0*xm);
			alxm=log(xm);
			g=xm*alxm-lgamma(xm+1.0);
		}
		do {
			do {
				y=tan(PI*DRAND2());
				em=sq*y+xm;
			} while (em < 0.0);
			em=floor(em);
			t=0.9*(1.0+y*y)*exp(em*alxm-lgamma(em+1.0)-g);
		} while (DRAND2() > t);
	}
	return em;
}
#undef PI

int randis(double *a, int n) 
{
/* a should be prob dis summing to 1 */ 
  int i ;  
  double t, y ;
  static int nfirst=0 ;

  t  = DRAND2() ;

  for (i=0; i<n; i++)  {
   t -= a[i] ;
   if (t<=0.0) return i ;
  }
  if (nfirst==0) {  
   printf("pos t: %15.9f\n",t) ;
   for (i=0; i<n ; i++) {  
    printf("zzrand %4d %9.3f\n",i, a[i]) ;
   }
  }
  ++nfirst ;
  fprintf(stderr, "probable bug (randis)\n") ;
  return -1  ;
  return n-1 ;
}

void ransamp(int *samp, int nsamp, double *p, int plen) 
/** 
 pick nsamp elements from random distribution 
 uses randis but array is at least sorted optimally 
*/
{
    double *px ;  
    int *indx ;
    double y ;
    int i, j, k ;

    if (plen<=1) { 
     ivzero(samp, nsamp) ;
     return ;
    }

    ZALLOC(px, plen, double) ;
    ZALLOC(indx, plen, int) ;

    y = asum(p, plen) ;
    vst(px, p, -1.0/y, plen) ;       
    sortit(px, indx, plen) ;
    vst(px, px, -1.0, plen) ;

    for (i=0; i<nsamp; i++) {  
/** 
 really need binary chop picker 
*/
     j = randis(px, plen) ;
     if (j<0) {  
      for (k=0; k<plen; k++) {  
       printf("zz %d %d %12.6f  %12.6f\n",k, indx[k], p[k], px[k]) ;
      }
      fatalx("bad ransamp\n") ;
     }
     k = indx[j] ;  
     samp[i] = k ;
    }
    

    free (px) ;
    free (indx) ;


}

void pick2(int n, int *k1, int *k2) 
{
 long l1 , l2 ;
 /* pick 2 distinct integers < n  */ ;
 if (n<2) fatalx("bad pick2 call\n") ;
 for (;;) {
  l1 = LRAND() ;
  l2 = LRAND() ;
  l1 = l1%n ;
  l2 = l2%n ;
  if (l1 != l2) break ;
 }
 *k1 = l1 ;
 *k2 = l2 ;
}

void ranperm (int *a, int n) 
/** 
 a must be initialized say by idperm 
*/
{
  int l,k,tmp  ;
  long r ;
  for (l=n; l>1 ; l--)  {

   r = LRAND() ;
   k = r % l ;
/* now swap k and l-1 */ 
   tmp = a[l-1] ;  a[l-1]=a[k] ;  a[k] = tmp ;

  }
}
int ranmod(int n) 
/* random number 0,...n-1 */
{

  long r, big ;
  big = (2 << 29) - 1 ; 
  r = LRAND() ;
  r %= big ;
  return (r % n) ;

}
double ranbeta(double a, double b) 
{
   double xa, xb ;

   if ((a<=0.0) || (b<=0.0)) fatalx("(ranbeta) bad parameters: %9.3f %9.3f\n", a, b) ;
   xa = rangam(a) ;
   xb = rangam(b) ;
   return xa/(xa+xb) ;
}

int ranbinom(int n, double p) 
{
/** 
 Knuth Vol 2, p 131
*/
#define BTHRESH  50 
   int a, b ;
   double x ; 
   if (p>=1) return n ;
   if (p<=0) return 0 ;
   if (n<=0) return 0 ;

   if (n<=BTHRESH) {
    return ranb1(n,p) ;  /** small case */
   }

   a  = 1 + n/2 ;  
   b  = n + 1 - a ;
   x = ranbeta((double) a, (double) b) ;
   if (x>=p) return ranbinom(a-1, p/x) ;
   return (a + ranbinom(b-1, (p-x)/(1.0-x)) ) ;
}
static int ranb1 (int n, double p) 
/** 
 binomial dis. 
 Naive routine
*/
{ 
    int cnt = 0, i ;

    for (i=0 ; i< n ; i++)  {
     if (DRAND2() <= p) ++ cnt ;
    }

    return cnt ;

}
void ewens(int *a, int n, double theta) 
/**
 implements the Ewens sampler.  Categories 1...K
*/
{
     int i, k, maxcat=0 ;
     double t, x ;

    if (n==0) return ;
    a[0] = maxcat = 1 ;
    for (i=1 ; i< n ; i++)  {
     t = theta/ ((double) i + theta) ;
     x = DRAND2() ;
     if (x > t)  {        
       k = ranmod(i) ;
       a[i] = a[k] ;
     }
     else {
       ++maxcat ;
       a[i] = maxcat ;
     }
    }
}

double ranpoiss1(double xm) 
/* poisson variable conditioned on x>0 */
/** xm should be small here 
 ranpoissx is the driver. 
 Don' t call thus directly
*/
{
   double x, t, tc, s, y ;
   int k ;
    t = exp(-xm) ;
    tc = 1.0-t ;
    if (tc==0.0) return 1 ;
    y = t ;  
    s = tc*DRAND2() ;  
/* s uniform [0, tc] */  
    k = 1 ;
    y *= xm / (double) k ;
    for (;;) {  
     if (s<y)  return (double) k ;
     s -= y ;
     ++k ;
     y *= xm / (double) k ;
     if (k>=100)  {  
      fprintf(stderr,"(ranpoiss1) bug? \n") ;
      return k ;
     }
    }
}

void
genmultgauss(double *rvec, int num, int n, double *covar)
{
  double *cf ;
  ZALLOC(cf, n*n, double) ;
  cholesky(cf, covar, n) ;
  transpose(cf, cf, n, n) ;
  gaussa(rvec, num*n) ;
  mulmat(rvec, rvec, cf, num, n, n) ;
  free(cf) ;
}

double drand2()  
{
  double x, y ;
  double maxran, maxran1 ;
  static double eps = -1.0 ;
/** 
 DRAND2 is quantized 1/2^31 
 call it twice and get max precision 
*/

  if (eps < 0.0) {
   maxran = 1.0-DBL_EPSILON  ;
   maxran1 = (double) (BIGINT-1) / (double) BIGINT ;
   eps = maxran - maxran1 ;
  }

  x = DRAND() ;
  y = DRAND() ;
  return x + y * eps ;
}


void ranmultinom(int *samp, int n, double *p, int len) 
// multinomial sample p is prob dist  n samples returned
// work is O(len^2) which is silly 
{
  int x ;
  double *pp ;

  if (len==0) return ;   
  ivzero(samp, len) ;
  if (n<=0) return ;

   if (len==1)  { 
    samp[0] = n ;
    return ;
   }

   ZALLOC(pp, len, double) ;
   copyarr(p, pp, len) ;
   bal1(pp, len) ;

   samp[0] = x = ranbinom(n, pp[0]) ;
   ranmultinom(samp+1, n-x, p+1, len-1) ;
   free(pp) ;
}
double ranchi (int d) 
{
  double y ; 

  y = 2.0 * rangam(0.5 * (double) d) ;
  return y ;

}

double raninvwis(double *wis, int t, int d, double *s) 
// invers Wishart:  t d.o.f. d dimension S data matrix  
// Ref Liu: Monte Carlo Strategies pp 40-41

{
   double *b, *n, *v, *cf, *ww, y ;
   int i, j ;

   if (t < d)  { 
     fatalx("(raninvwis) d.o.f. too small %d %d\n", t, d) ;
   }

   ZALLOC(b, d*d, double) ;
   ZALLOC(n, d*d, double) ;
   ZALLOC(v, d, double) ;
   ZALLOC(cf, d*d, double) ;
   ZALLOC(ww, d*d, double) ;

   for (i=0; i<d; i++) { 
    v[i] = ranchi(t-i) ;
    for (j=0; j<i; j++) {  
     n[i*d+j] = n[j*d+i] = gauss() ;
    }
   }

   y = b[0] = v[0] ;  
   for (j=1; j<d; j++)  {  
    b[j*d+0] = b[j] = sqrt(y)*n[j] ;
   }
   for (j=1; j<d; j++)  {  
    b[j*d+j] = v[j]  ;
    for (i=0; i<j; i++) {  
     y = n[i*d+j] ;
     b[j*d+j] += y*y ;
     b[j*d+i] = b[i*d+j] = y*sqrt(v[i]) + vdot(n+i*d, n+j*d, i-1) ;
    }
   }

   cholesky(cf, s, d) ;
   mulmat(ww, cf, b, d, d, d) ;
   transpose(cf, cf, d, d) ;
   mulmat(wis, ww, cf, d, d, d) ;

   free(b) ; 
   free(n) ;
   free(v) ;
   free(cf) ;
   free(ww) ;
}

double uniform(double lo, double hi) 
{
   double x, width ;
   
   width = hi - lo ;  

   if (width < 0) 
    return uniform(hi, lo) ;  
   
   x = DRAND2() *  width ;

   return x + lo ;

}


void randirichlet(double *x, double *pp, int n) 
/** 
 generate dirichlet r.v. parameters pp
*/
{
  double y ;
  int i ;

  for (i=0; i<n; i++) { 
   x[i] = rangam(pp[i]) ;
  }
  bal1(x,n) ;
}


void randirmult(double *pp, int *aa, int len, int m)

{
/**
 compound dirichlet - Multinomial
*/
     int k ;
     double a, b, p ;
     double *x ;

    if (len==0) return ;
    if (len==1) {
      aa[0] = m ;
      return ;
    }
    ZALLOC(x, len, double) ;  
    randirichlet(x, pp, len) ;
    ranmultinom(aa, m, x, len) ;
    free(x) ;
}




