(function(){var $gwt_version = "1.5.3";var $wnd = window;var $doc = $wnd.document;var $moduleName, $moduleBase;var $stats = $wnd.__gwtStatsEvent ? function(a) {return $wnd.__gwtStatsEvent(a);} : null;$stats && $stats({moduleName:'com.google.gwt.visualization.customvisualization.CustomVisualization',subSystem:'startup',evtGroup:'moduleStartup',millis:(new Date()).getTime(),type:'moduleEvalStart'});var z='',D=', Row size: ',kb=', Size: ',sb=':',qb='<\/b>',pb='<b>',eb='Cannot create a column with a negative index: ',fb='Cannot create a row with a negative index: ',xb='CustomVisualization',v='DOMMouseScroll',jb='Index: ',Cb='Integer;',Fb='JavaScriptObject$;',Db='Object;',C='Row index: ',Ab='Widget;',Eb='[Lcom.google.gwt.core.client.',zb='[Lcom.google.gwt.user.client.ui.',Bb='[Ljava.lang.',ib='__widgetID',mb='backgroundColor',l='blur',m='change',x='click',hb='col',gb='colgroup',wb='com.google.gwt.visualization.customvisualization.client.CustomVisualizationEntryPoint',w='contextmenu',cb='dblclick',t='error',nb='focus',yb='keydown',ac='keypress',bc='keyup',y='left',cc='load',dc='losecapture',ub='moduleStartup',n='mousedown',o='mousemove',p='mouseout',q='mouseover',r='mouseup',u='mousewheel',vb='onModuleLoadStart',B='position',s='scroll',lb='select',rb='selection changed',tb='startup',bb='table',E='tagName',db='tbody',F='td',A='top',ab='tr',ob='white';var _;function Cm(a){return (this==null?null:this)===(a==null?null:a)}
function Dm(){return this.$H||(this.$H=++Ac)}
function Am(){}
_=Am.prototype={};_.eQ=Cm;_.hC=Dm;_.tM=Cr;_.tI=1;function hc(b){var a,c;c=[];for(a=0;a<b.length;++a){c[a]=b[a]}c.constructor=$wnd.Array;return c}
function oc(b,a){return b.tM==Cr||b.tI==2?b.eQ(a):(b==null?null:b)===(a==null?null:a)}
function qc(a){return a.tM==Cr||a.tI==2?a.hC():a.$H||(a.$H=++Ac)}
var Ac=0;function Ec(b){var a=b.firstChild;while(a&&a.nodeType!=1)a=a.nextSibling;return a}
function Fc(a){var b=a.parentNode;if(b==null){return null}if(b.nodeType!=1)b=null;return b}
function ad(a,b){while(a.firstChild){a.removeChild(a.firstChild)}if(b!=null){a.appendChild($doc.createTextNode(b))}}
function wd(e,c){var d=[null,0,false,[0,0]];var f=d[e];var a=new Array(c);for(var b=0;b<c;++b){a[b]=f}return a}
function xd(a,f,c,b,e){var d;d=wd(e,b);yd(a,f,c,d);return d}
function yd(b,d,c,a){if(!zd){zd=new sd()}Cd(a,zd);a.tI=d;a.qI=c;return a}
function Ad(a,b,c){if(c!=null){if(a.qI>0&&!Fd(c.tI,a.qI)){throw new zl()}if(a.qI<0&&(c.tM==Cr||c.tI==2)){throw new zl()}}return a[b]=c}
function Cd(a,c){for(var b in c){var d=c[b];if(d){a[b]=d}}return a}
function sd(){}
_=sd.prototype=new Am();_.tI=0;_.length=0;_.qI=0;var zd=null;function ae(b,a){return b&&!!me[b][a]}
function Fd(b,a){return b&&me[b][a]}
function be(b,a){if(b!=null&&!Fd(b.tI,a)){throw new Dl()}return b}
function ee(b,a){return b!=null&&ae(b.tI,a)}
var me=[{},{},{1:1,17:1,18:1,19:1},{2:1,17:1},{2:1,17:1},{2:1,17:1},{2:1,17:1},{9:1},{4:1,5:1,9:1},{4:1,5:1,8:1,9:1},{4:1,5:1,8:1,9:1},{4:1,5:1,8:1,9:1},{4:1,5:1,9:1},{4:1,5:1,8:1,9:1},{4:1,5:1,8:1,9:1},{4:1,5:1,6:1,8:1,9:1},{3:1},{4:1,5:1,6:1,8:1,9:1},{13:1},{13:1,17:1},{13:1,17:1},{4:1,5:1,9:1},{4:1,5:1,9:1},{7:1},{2:1,17:1},{2:1,17:1},{2:1,17:1},{2:1,17:1},{2:1,17:1},{17:1,20:1},{2:1,17:1},{2:1,17:1},{11:1,17:1,19:1,20:1},{18:1},{18:1},{2:1,17:1},{15:1},{15:1},{12:1},{12:1},{12:1},{15:1},{14:1,17:1},{15:1,17:1},{12:1},{2:1,17:1},{10:1}];function df(b,a,c){var d;if(a==gf){if(hg(b)==8192){gf=null}}d=cf;cf=b;try{c.z(b)}finally{cf=d}}
function hf(a,b){jg();a.__eventBits=b;a.onclick=b&1?fg:null;a.ondblclick=b&2?fg:null;a.onmousedown=b&4?fg:null;a.onmouseup=b&8?fg:null;a.onmouseover=b&16?fg:null;a.onmouseout=b&32?fg:null;a.onmousemove=b&64?fg:null;a.onkeydown=b&128?fg:null;a.onkeypress=b&256?fg:null;a.onkeyup=b&512?fg:null;a.onchange=b&1024?fg:null;a.onfocus=b&2048?fg:null;a.onblur=b&4096?fg:null;a.onlosecapture=b&8192?fg:null;a.onscroll=b&16384?fg:null;a.onload=b&32768?fg:null;a.onerror=b&65536?fg:null;a.onmousewheel=b&131072?fg:null;a.oncontextmenu=b&262144?fg:null}
var cf=null,gf=null;function nf(a){uf();if(!pf){pf=qq(new pq())}rq(pf,a)}
function qf(){var a;if(pf){for(a=hp(new fp(),pf);a.a<a.b.ab();){be(kp(a),3);hj()}}}
function rf(){var a,b;b=null;if(pf){for(a=hp(new fp(),pf);a.a<a.b.ab();){be(kp(a),3);b=null}}return b}
function tf(){__gwt_initHandlers(function(){},function(){return rf()},function(){qf()})}
function uf(){if(!sf){tf();sf=true}}
var pf=null,sf=false;function hg(a){switch(a.type){case l:return 4096;case m:return 1024;case x:return 1;case cb:return 2;case nb:return 2048;case yb:return 128;case ac:return 256;case bc:return 512;case cc:return 32768;case dc:return 8192;case n:return 4;case o:return 64;case p:return 32;case q:return 16;case r:return 8;case s:return 16384;case t:return 65536;case u:return 131072;case v:return 131072;case w:return 262144;}}
function jg(){if(!lg){ag();lg=true}}
function mg(a){return a!=null&&ae(a.tI,4)&&!(a!=null&&(a.tM!=Cr&&a.tI!=2))}
var lg=false;function Ff(c,e){var b=0,a=c.firstChild;while(a){if(a===e){return b}if(a.nodeType==1){++b}a=a.nextSibling}return -1}
function ag(){eg=function(b){if(dg(b)){var a=cg;if(a&&a.__listener){if(mg(a.__listener)){df(b,a,a.__listener);b.stopPropagation()}}}};dg=function(a){return true};fg=function(b){var c,a=this;while(a&&!(c=a.__listener)){a=a.parentNode}if(a&&a.nodeType!=1){a=null}if(c){if(mg(c)){df(b,a,c)}}};$wnd.addEventListener(x,eg,true);$wnd.addEventListener(cb,eg,true);$wnd.addEventListener(n,eg,true);$wnd.addEventListener(r,eg,true);$wnd.addEventListener(o,eg,true);$wnd.addEventListener(q,eg,true);$wnd.addEventListener(p,eg,true);$wnd.addEventListener(u,eg,true);$wnd.addEventListener(yb,dg,true);$wnd.addEventListener(bc,dg,true);$wnd.addEventListener(ac,dg,true)}
function bg(e,g,d){var c=0,b=e.firstChild,a=null;while(b){if(b.nodeType==1){if(c==d){a=b;break}++c}b=b.nextSibling}e.insertBefore(g,a)}
var cg=null,dg=null,eg=null,fg=null;function uj(b,a){b.i=a}
function sj(){}
_=sj.prototype=new Am();_.tI=7;_.i=null;function fk(a){if(a.v()){throw new im()}a.g=true;a.i.__listener=a;a.m();a.B()}
function gk(a){if(!a.v()){throw new im()}try{a.C()}finally{a.n();a.i.__listener=null;a.g=false}}
function hk(a){if(ee(a.h,8)){be(a.h,8).D(a)}else if(a.h){throw new im()}}
function ik(c,b){var a;a=c.h;if(!b){if(!!a&&a.v()){c.A()}c.h=null}else{if(a){throw new im()}c.h=b;if(b.v()){c.y()}}}
function jk(){}
function kk(){}
function lk(){return this.g}
function mk(){fk(this)}
function nk(a){}
function ok(){gk(this)}
function pk(){}
function qk(){}
function vj(){}
_=vj.prototype=new sj();_.m=jk;_.n=kk;_.v=lk;_.y=mk;_.z=nk;_.A=ok;_.B=pk;_.C=qk;_.tI=8;_.g=false;_.h=null;function Bi(){var a,b;for(b=this.w();b.u();){a=be(b.x(),5);a.y()}}
function Ci(){var a,b;for(b=this.w();b.u();){a=be(b.x(),5);a.A()}}
function Di(){}
function Ei(){}
function zi(){}
_=zi.prototype=new vj();_.m=Bi;_.n=Ci;_.B=Di;_.C=Ei;_.tI=9;function ug(c,a,b){hk(a);Ej(c.a,a);b.appendChild(a.i);ik(a,c)}
function wg(b,c){var a;if(c.h!=b){return false}ik(c,null);a=c.i;Fc(a).removeChild(a);dk(b.a,c);return true}
function xg(){return zj(new xj(),this.a)}
function yg(a){return wg(this,a)}
function sg(){}
_=sg.prototype=new zi();_.w=xg;_.D=yg;_.tI=10;function og(a,b){ug(a,b,a.i)}
function qg(a){a.style[y]=z;a.style[A]=z;a.style[B]=z}
function rg(b){var a;a=wg(this,b);if(a){qg(b.i)}return a}
function ng(){}
_=ng.prototype=new sg();_.D=rg;_.tI=11;function Bg(a,b){if(a.e){throw new im()}hk(b);uj(a,b.i);a.e=b;ik(b,a)}
function Cg(){if(this.e){return this.e.g}return false}
function Dg(){fk(this.e);this.i.__listener=this}
function Eg(a){oi(this.e,a)}
function Fg(){gk(this.e)}
function zg(){}
_=zg.prototype=new vj();_.v=Cg;_.y=Dg;_.z=Eg;_.A=Fg;_.tI=12;_.e=null;function di(b,a){if(!b.e){b.e=oj(new nj());hf(b.i,1|(b.i.__eventBits||0))}rq(b.e,a)}
function ei(c,a){var b;b=c.a.rows.length;if(a>=b||a<0){throw mm(new lm(),C+a+D+b)}}
function gi(d){var a,b,c;for(c=0;c<d.a.rows.length;++c){for(b=0;b<(ei(d,c),d.a.rows[c].cells.length);++b){a=li(d,c,b);if(a){pi(d,a)}}}}
function ki(d,b){var a,c,e;c=b.target;for(;c;c=Fc(c)){if(mn(c[E]==null?null:String(c[E]),F)){e=Fc(c);a=Fc(e);if(a==d.a){return c}}if(c==d.a){return null}}return null}
function li(e,d,b){var a,c;c=e.b.a.a.rows[d].cells[b];a=Ec(c);if(!a){return null}else{return Dh(e.f,a)}}
function mi(b,a){var c;if(a!=b.a.rows.length){ei(b,a)}c=$doc.createElement(ab);bg(b.a,c,a);return a}
function ni(d,c,a){var b,e;b=Ec(c);e=null;if(b){e=Dh(d.f,b)}if(e){pi(d,e);return true}else{if(a){c.innerHTML=z}return false}}
function oi(f,c){var a,b,d,e,g;switch(hg(c)){case 1:{if(f.e){e=ki(f,c);if(!e){return}g=Fc(e);a=Fc(g);d=Ff(a,g);b=Ff(g,e);qj(f.e,d,b)}break}}}
function pi(b,c){var a;if(c.h!=b){return false}ik(c,null);a=c.i;Fc(a).removeChild(a);Eh(b.f,a);return true}
function ri(b,a){b.c=a;rh(b.c)}
function si(f,d,a,c){var e,b;gh(f,d,a);e=(b=f.b.a.a.rows[d].cells[a],ni(f,b,c==null),b);if(c!=null){e.innerHTML=c||z}}
function ti(f,c,a,e){var d,b;gh(f,c,a);d=(b=f.b.a.a.rows[c].cells[a],ni(f,b,e==null),b);if(e!=null){ad(d,e)}}
function ui(){return vh(new th(),this.f)}
function vi(a){oi(this,a)}
function wi(a){return pi(this,a)}
function jh(){}
_=jh.prototype=new zi();_.w=ui;_.z=vi;_.D=wi;_.tI=13;_.a=null;_.b=null;_.c=null;_.d=null;_.e=null;function eh(a){a.f=Bh(new sh());a.d=$doc.createElement(bb);a.a=$doc.createElement(db);a.d.appendChild(a.a);a.i=a.d;a.b=ch(new bh(),a);ri(a,ph(new oh(),a));return a}
function gh(e,d,b){var a,c;hh(e,d);if(b<0){throw mm(new lm(),eb+b)}a=(ei(e,d),e.a.rows[d].cells.length);c=b+1-a;if(c>0){ih(e.a,d,c)}}
function hh(d,b){var a,c;if(b<0){throw mm(new lm(),fb+b)}c=d.a.rows.length;for(a=c;a<=b;++a){mi(d,a)}}
function ih(f,d,c){var e=f.rows[d];for(var b=0;b<c;b++){var a=$doc.createElement(F);e.appendChild(a)}}
function ah(){}
_=ah.prototype=new jh();_.tI=14;function kh(){}
_=kh.prototype=new Am();_.tI=0;_.a=null;function ch(b,a){b.a=a;return b}
function bh(){}
_=bh.prototype=new kh();_.tI=0;function ph(b,a){b.b=a;return b}
function rh(a){if(!a.a){a.a=$doc.createElement(gb);bg(a.b.d,a.a,0);a.a.appendChild($doc.createElement(hb))}}
function oh(){}
_=oh.prototype=new Am();_.tI=0;_.a=null;_.b=null;function Bh(a){a.a=qq(new pq());return a}
function Dh(d,b){var c,a;c=(a=b[ib],a==null?-1:a);if(c<0){return null}return be(tq(d.a,c),5)}
function Eh(d,b){var c,a;c=(a=b[ib],a==null?-1:a);b[ib]=null;vq(d.a,c,null)}
function sh(){}
_=sh.prototype=new Am();_.tI=0;function vh(b,a){b.b=a;xh(b);return b}
function xh(a){while(++a.a<a.b.a.b){if(tq(a.b.a,a.a)!=null){return}}}
function yh(){return this.a<this.b.a.b}
function zh(){var a;if(this.a>=this.b.a.b){throw new vr()}a=be(tq(this.b.a,this.a),5);xh(this);return a}
function th(){}
_=th.prototype=new Am();_.u=yh;_.x=zh;_.tI=0;_.a=-1;_.b=null;function gj(){gj=Cr;kj=Fq(new Eq());lj=dr(new cr())}
function fj(b,a){gj();b.a=Dj(new wj());b.i=a;fk(b);return b}
function hj(){var b,a;gj();var c,d;for(d=(b=En(new Dn(),iq(lj.a).b.a),yp(new xp(),b));d.a.u();){c=be((a=d.a.x(),a.q()),5);if(c.v()){c.A()}}}
function jj(b){gj();var a,c;c=be(Co(kj,b),6);if(c){return c}a=null;if(b!=null){if(!(a=$doc.getElementById(b))){return null}}if(kj.d==0){nf(new aj())}if(!a){c=dj(new cj())}else{c=fj(new Fi(),a)}cp(kj,b,c);er(lj,c);return c}
function Fi(){}
_=Fi.prototype=new ng();_.tI=15;var kj,lj;function aj(){}
_=aj.prototype=new Am();_.tI=16;function ej(){ej=Cr;gj()}
function dj(a){ej();fj(a,$doc.body);return a}
function cj(){}
_=cj.prototype=new Fi();_.tI=17;function xn(a,b){var c;while(a.u()){c=a.x();if(b==null?c==null:oc(b,c)){return a}}return null}
function zn(a){throw new tn()}
function An(b){var a;a=xn(this.w(),b);return !!a}
function wn(){}
_=wn.prototype=new Am();_.k=zn;_.l=An;_.tI=0;function pp(a){this.j(this.ab(),a);return true}
function op(b,a){throw new tn()}
function qp(a,b){if(a<0||a>=b){tp(a,b)}}
function rp(e){var a,b,c,d,f;if((e==null?null:e)===(this==null?null:this)){return true}if(!(e!=null&&ae(e.tI,13))){return false}f=be(e,13);if(this.ab()!=f.ab()){return false}c=hp(new fp(),this);d=f.w();while(c.a<c.b.ab()){a=kp(c);b=kp(d);if(!(a==null?b==null:oc(a,b))){return false}}return true}
function sp(){var a,b,c;b=1;a=hp(new fp(),this);while(a.a<a.b.ab()){c=kp(a);b=31*b+(c==null?0:qc(c));b=~~b}return b}
function tp(a,b){throw mm(new lm(),jb+a+kb+b)}
function up(){return hp(new fp(),this)}
function ep(){}
_=ep.prototype=new wn();_.k=pp;_.j=op;_.eQ=rp;_.hC=sp;_.w=up;_.tI=18;function qq(a){a.a=xd(se,0,0,0,0);a.b=0;return a}
function rq(b,a){Ad(b.a,b.b++,a);return true}
function tq(b,a){qp(a,b.b);return b.a[a]}
function uq(c,b,a){for(;a<c.b;++a){if(Br(b,c.a[a])){return a}}return -1}
function vq(d,a,b){var c;c=(qp(a,d.b),d.a[a]);Ad(d.a,a,b);return c}
function xq(a){return Ad(this.a,this.b++,a),true}
function wq(a,b){if(a<0||a>this.b){tp(a,this.b)}this.a.splice(a,0,b);++this.b}
function yq(a){return uq(this,a,0)!=-1}
function zq(a){return qp(a,this.b),this.a[a]}
function Aq(){return this.b}
function pq(){}
_=pq.prototype=new ep();_.k=xq;_.j=wq;_.l=yq;_.t=zq;_.ab=Aq;_.tI=19;_.a=null;_.b=0;function oj(a){a.a=xd(se,0,0,0,0);a.b=0;return a}
function qj(e,d,a){var b,c;for(c=hp(new fp(),e);c.a<c.b.ab();){b=be(kp(c),7);b.a.b=wm(a);b.a.c=wm(d-1);$wnd.google.visualization.events.trigger(b.a.d,lb,null)}}
function nj(){}
_=nj.prototype=new pq();_.tI=20;function Dj(a){a.a=xd(qe,0,5,4,0);return a}
function Ej(a,b){bk(a,b,a.b)}
function ak(b,c){var a;for(a=0;a<b.b;++a){if(b.a[a]==c){return a}}return -1}
function bk(d,e,a){var b,c;if(a<0||a>d.b){throw new lm()}if(d.b==d.a.length){c=xd(qe,0,5,d.a.length*2,0);for(b=0;b<d.a.length;++b){Ad(c,b,d.a[b])}d.a=c}++d.b;for(b=d.b-1;b>a;--b){Ad(d.a,b,d.a[b-1])}Ad(d.a,a,e)}
function ck(c,b){var a;if(b<0||b>=c.b){throw new lm()}--c.b;for(a=b;a<c.b;++a){Ad(c.a,a,c.a[a+1])}Ad(c.a,c.b,null)}
function dk(b,c){var a;a=ak(b,c);if(a==-1){throw new vr()}ck(b,a)}
function wj(){}
_=wj.prototype=new Am();_.tI=0;_.a=null;_.b=0;function zj(b,a){b.b=a;return b}
function Bj(){return this.a<this.b.b-1}
function Cj(){if(this.a>=this.b.b){throw new vr()}return this.b.a[++this.a]}
function xj(){}
_=xj.prototype=new Am();_.u=Bj;_.x=Cj;_.tI=0;_.a=-1;_.b=null;function Ck(b,c,a){var d;d=sl(new el());d.d=c;og(jj(a.id),d);if(d){Ek(c)}return d}
function Ek(b){b.getSelection=function(){return this.gwt_vis.r()};b.setSelection=function(a){this.gwt_vis.E(a)}}
function Fk(d,c){$wnd[d]=function(a){this.gwt_vis=Ck(c,this,a)};$wnd[d].prototype.draw=function(a,b){this.gwt_vis.o(a,b)}}
function zk(){}
_=zk.prototype=new zg();_.tI=21;_.d=null;function sl(a){a.a=eh(new ah());Bg(a,a.a);return a}
function ul(b,c){var a,d;gi(this.a);if(c){this.a.i.style[mb]=c.backgroundColor||ob}for(a=0;a<b.getNumberOfColumns();++a){si(this.a,0,a,pb+b.getColumnLabel(a)+qb)}for(d=0;d<b.getNumberOfRows();++d){for(a=0;a<b.getNumberOfColumns();++a){ti(this.a,d+1,a,b.getFormattedValue(d,a))}}di(this.a,gl(new fl(),this))}
function vl(){return hc(yd(pe,0,-1,[{row:this.c.a,column:this.b.a}]))}
function wl(a){$wnd.alert(rb)}
function el(){}
_=el.prototype=new zk();_.o=ul;_.r=vl;_.E=wl;_.tI=22;_.b=null;_.c=null;function gl(b,a){b.a=a;return b}
function fl(){}
_=fl.prototype=new Am();_.tI=23;_.a=null;function ql(a){if($wnd.onLoadCallback!=undefined){$wnd.onLoadCallback(a)}}
function nl(){}
_=nl.prototype=new Am();_.tI=0;function rn(){}
_=rn.prototype=new Am();_.tI=3;function gm(){}
_=gm.prototype=new rn();_.tI=4;function Em(){}
_=Em.prototype=new gm();_.tI=5;function zl(){}
_=zl.prototype=new Em();_.tI=25;function am(c,a){var b;b=new Cl();return b}
function Cl(){}
_=Cl.prototype=new Am();_.tI=0;function Dl(){}
_=Dl.prototype=new Em();_.tI=28;function im(){}
_=im.prototype=new Em();_.tI=30;function mm(b,a){return b}
function lm(){}
_=lm.prototype=new Em();_.tI=31;function ym(){}
_=ym.prototype=new Am();_.tI=29;function sm(a,b){a.a=b;return a}
function um(a){return a!=null&&ae(a.tI,11)&&be(a,11).a==this.a}
function vm(){return this.a}
function wm(a){var b,c;if(a>-129&&a<128){b=a+128;c=(qm(),rm)[b];if(!c){c=rm[b]=sm(new om(),a)}return c}return sm(new om(),a)}
function om(){}
_=om.prototype=new ym();_.eQ=um;_.hC=vm;_.tI=32;_.a=0;function qm(){qm=Cr;rm=xd(re,0,11,256,0)}
var rm;function mn(b,a){if(a==null)return false;return b==a||b.toLowerCase()==a.toLowerCase()}
function pn(a){if(!(a!=null&&ae(a.tI,1))){return false}return String(this)==a}
function qn(){return hn(this)}
_=String.prototype;_.eQ=pn;_.hC=qn;_.tI=2;function cn(){cn=Cr;dn={};gn={}}
function en(e){var a,b,c,d;d=e.length;c=d<64?1:~~(d/32);a=0;for(b=0;b<d;b+=c){a<<=1;a+=e.charCodeAt(b)}a|=0;return a}
function hn(c){cn();var a=sb+c;var b=gn[a];if(b!=null){return b}b=dn[a];if(b==null){b=en(c)}jn();return gn[a]=b}
function jn(){if(fn==256){dn=gn;gn={};fn=0}++fn}
var dn,fn=0,gn;function tn(){}
_=tn.prototype=new Em();_.tI=35;function iq(b){var a;a=co(new Cn(),b);return Dp(new wp(),b,a)}
function jq(c){var a,b,d,e,f;if((c==null?null:c)===(this==null?null:this)){return true}if(!(c!=null&&ae(c.tI,14))){return false}e=be(c,14);if(be(this,14).d!=e.d){return false}for(b=En(new Dn(),co(new Cn(),e).a);jp(b.a);){a=be(kp(b.a),12);d=a.q();f=a.s();if(!(d==null?be(this,14).c:d!=null&&ae(d.tI,1)?Eo(be(this,14),be(d,1)):Do(be(this,14),d,~~qc(d)))){return false}if(!Br(f,d==null?be(this,14).b:d!=null&&ae(d.tI,1)?be(this,14).e[sb+be(d,1)]:Ao(be(this,14),d,~~qc(d)))){return false}}return true}
function kq(){var a,b,c;c=0;for(b=En(new Dn(),co(new Cn(),be(this,14)).a);jp(b.a);){a=be(kp(b.a),12);c+=a.hC();c=~~c}return c}
function vp(){}
_=vp.prototype=new Am();_.eQ=jq;_.hC=kq;_.tI=0;function vo(g,c){var e=g.a;for(var d in e){if(d==parseInt(d)){var a=e[d];for(var f=0,b=a.length;f<b;++f){c.k(a[f])}}}}
function wo(e,a){var d=e.e;for(var c in d){if(c.charCodeAt(0)==58){var b=to(e,c.substring(1));a.k(b)}}}
function zo(b,a){return a==null?b.c:a!=null&&ae(a.tI,1)?Eo(b,be(a,1)):Do(b,a,~~qc(a))}
function Co(b,a){return a==null?b.b:a!=null&&ae(a.tI,1)?b.e[sb+be(a,1)]:Ao(b,a,~~qc(a))}
function Ao(h,g,e){var a=h.a[e];if(a){for(var f=0,b=a.length;f<b;++f){var c=a[f];var d=c.q();if(h.p(g,d)){return c.s()}}}return null}
function Do(h,g,e){var a=h.a[e];if(a){for(var f=0,b=a.length;f<b;++f){var c=a[f];var d=c.q();if(h.p(g,d)){return true}}}return false}
function Eo(b,a){return sb+a in b.e}
function cp(b,a,c){return a==null?ap(b,c):a!=null&&ae(a.tI,1)?bp(b,be(a,1),c):Fo(b,a,c,~~qc(a))}
function Fo(i,g,j,e){var a=i.a[e];if(a){for(var f=0,b=a.length;f<b;++f){var c=a[f];var d=c.q();if(i.p(g,d)){var h=c.s();c.F(j);return h}}}else{a=i.a[e]=[]}var c=or(new nr(),g,j);a.push(c);++i.d;return null}
function ap(b,c){var a;a=b.b;b.b=c;if(!b.c){b.c=true;++b.d}return a}
function bp(d,a,e){var b,c=d.e;a=sb+a;if(a in c){b=c[a]}else{++d.d}c[a]=e;return b}
function dp(a,b){return (a==null?null:a)===(b==null?null:b)||a!=null&&oc(a,b)}
function Bn(){}
_=Bn.prototype=new vp();_.p=dp;_.tI=0;_.a=null;_.b=null;_.c=false;_.d=0;_.e=null;function nq(b){var a,c,d;if((b==null?null:b)===(this==null?null:this)){return true}if(!(b!=null&&ae(b.tI,15))){return false}c=be(b,15);if(c.ab()!=this.ab()){return false}for(a=c.w();a.u();){d=a.x();if(!this.l(d)){return false}}return true}
function oq(){var a,b,c;a=0;for(b=this.w();b.u();){c=b.x();if(c!=null){a+=qc(c);a=~~a}}return a}
function lq(){}
_=lq.prototype=new wn();_.eQ=nq;_.hC=oq;_.tI=36;function co(b,a){b.a=a;return b}
function fo(c){var a,b,d;if(c!=null&&ae(c.tI,12)){a=be(c,12);b=a.q();if(zo(this.a,b)){d=Co(this.a,b);return br(a.s(),d)}}return false}
function go(){return En(new Dn(),this.a)}
function ho(){return this.a.d}
function Cn(){}
_=Cn.prototype=new lq();_.l=fo;_.w=go;_.ab=ho;_.tI=37;_.a=null;function En(c,b){var a;c.b=b;a=qq(new pq());if(c.b.c){rq(a,jo(new io(),c.b))}wo(c.b,a);vo(c.b,a);c.a=hp(new fp(),a);return c}
function ao(){return jp(this.a)}
function bo(){return be(kp(this.a),12)}
function Dn(){}
_=Dn.prototype=new Am();_.u=ao;_.x=bo;_.tI=0;_.a=null;_.b=null;function fq(b){var a;if(b!=null&&ae(b.tI,12)){a=be(b,12);if(Br(this.q(),a.q())&&Br(this.s(),a.s())){return true}}return false}
function gq(){var a,b;a=0;b=0;if(this.q()!=null){a=qc(this.q())}if(this.s()!=null){b=qc(this.s())}return a^b}
function dq(){}
_=dq.prototype=new Am();_.eQ=fq;_.hC=gq;_.tI=38;function jo(b,a){b.a=a;return b}
function lo(){return null}
function mo(){return this.a.b}
function no(a){return ap(this.a,a)}
function io(){}
_=io.prototype=new dq();_.q=lo;_.s=mo;_.F=no;_.tI=39;_.a=null;function po(c,a,b){c.b=b;c.a=a;return c}
function ro(){return this.a}
function so(){return this.b.e[sb+this.a]}
function to(b,a){return po(new oo(),a,b)}
function uo(a){return bp(this.b,this.a,a)}
function oo(){}
_=oo.prototype=new dq();_.q=ro;_.s=so;_.F=uo;_.tI=40;_.a=null;_.b=null;function hp(b,a){b.b=a;return b}
function jp(a){return a.a<a.b.ab()}
function kp(a){if(a.a>=a.b.ab()){throw new vr()}return a.b.t(a.a++)}
function lp(){return this.a<this.b.ab()}
function mp(){return kp(this)}
function fp(){}
_=fp.prototype=new Am();_.u=lp;_.x=mp;_.tI=0;_.a=0;_.b=null;function Dp(b,a,c){b.a=a;b.b=c;return b}
function aq(a){return zo(this.a,a)}
function bq(){var a;return a=En(new Dn(),this.b.a),yp(new xp(),a)}
function cq(){return this.b.a.d}
function wp(){}
_=wp.prototype=new lq();_.l=aq;_.w=bq;_.ab=cq;_.tI=41;_.a=null;_.b=null;function yp(a,b){a.a=b;return a}
function Bp(){return this.a.u()}
function Cp(){var a;return a=this.a.x(),a.q()}
function xp(){}
_=xp.prototype=new Am();_.u=Bp;_.x=Cp;_.tI=0;_.a=null;function Fq(a){a.a=[];a.e={};a.c=false;a.b=null;a.d=0;return a}
function br(a,b){return (a==null?null:a)===(b==null?null:b)||a!=null&&oc(a,b)}
function Eq(){}
_=Eq.prototype=new Bn();_.tI=42;function dr(a){a.a=Fq(new Eq());return a}
function er(c,a){var b;b=cp(c.a,a,c);return b==null}
function gr(b){var a;return a=cp(this.a,b,this),a==null}
function hr(a){return zo(this.a,a)}
function ir(){var a;return a=En(new Dn(),iq(this.a).b.a),yp(new xp(),a)}
function jr(){return this.a.d}
function cr(){}
_=cr.prototype=new lq();_.k=gr;_.l=hr;_.w=ir;_.ab=jr;_.tI=43;_.a=null;function or(b,a,c){b.a=a;b.b=c;return b}
function qr(){return this.a}
function rr(){return this.b}
function tr(b){var a;a=this.b;this.b=b;return a}
function nr(){}
_=nr.prototype=new dq();_.q=qr;_.s=rr;_.F=tr;_.tI=44;_.a=null;_.b=null;function vr(){}
_=vr.prototype=new Em();_.tI=45;function Br(a,b){return (a==null?null:a)===(b==null?null:b)||a!=null&&oc(a,b)}
function xl(){!!$stats&&$stats({moduleName:$moduleName,subSystem:tb,evtGroup:ub,millis:(new Date()).getTime(),type:vb,className:wb});Fk(xb,new nl());ql($moduleName)}
function gwtOnLoad(b,d,c){$moduleName=d;$moduleBase=c;if(b)try{xl()}catch(a){b(d)}else{xl()}}
function Cr(){}
var qe=am(zb,Ab),re=am(Bb,Cb),se=am(Bb,Db),pe=am(Eb,Fb);$stats && $stats({moduleName:'com.google.gwt.visualization.customvisualization.CustomVisualization',subSystem:'startup',evtGroup:'moduleStartup',millis:(new Date()).getTime(),type:'moduleEvalEnd'});if (com_google_gwt_visualization_customvisualization_CustomVisualization) {  var __gwt_initHandlers = com_google_gwt_visualization_customvisualization_CustomVisualization.__gwt_initHandlers;  com_google_gwt_visualization_customvisualization_CustomVisualization.onScriptLoad(gwtOnLoad);}})();