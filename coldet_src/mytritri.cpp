/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * Triangle-Triangle intersection test.
 * Based on Tomas Moller's algorithm:
 * "A Fast Triangle-Triangle Intersection Test", 1997.
 */
#include <math.h>

#define FABS(x) ((float)fabs(x))

#define CROSS(dest,v1,v2)           \
  dest[0]=v1[1]*v2[2]-v1[2]*v2[1]; \
  dest[1]=v1[2]*v2[0]-v1[0]*v2[2]; \
  dest[2]=v1[0]*v2[1]-v1[1]*v2[0];

#define DOT(v1,v2) (v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2])

#define SUB(dest,v1,v2) \
  dest[0]=v1[0]-v2[0]; \
  dest[1]=v1[1]-v2[1]; \
  dest[2]=v1[2]-v2[2];

#define SORT(a,b)               \
  if(a>b) { float c; c=a; a=b; b=c; }

#define ISECT(VV0,VV1,VV2,D0,D1,D2,isect0,isect1) \
  isect0=VV0+(VV1-VV0)*D0/(D0-D1);                \
  isect1=VV0+(VV2-VV0)*D0/(D0-D2);

static int edge_edge_test(float V0[3], float U0[3], float U1[3],
                          int i0, int i1, float Ax, float Ay)
{
    float Bx=U0[i0]-U1[i0];
    float By=U0[i1]-U1[i1];
    float Cx=V0[i0]-U0[i0];
    float Cy=V0[i1]-U0[i1];
    float f=Ay*Bx-Ax*By;
    float d=By*Cx-Bx*Cy;
    if((f>0&&d>=0&&d<=f)||(f<0&&d<=0&&d>=f)) {
        float e=Ax*Cy-Ay*Cx;
        if(f>0) { if(e>=0&&e<=f) return 1; }
        else    { if(e<=0&&e>=f) return 1; }
    }
    return 0;
}

#define EDGE_AGAINST_TRI_EDGES(V0,V1,U0,U1,U2,i0,i1)      \
{                                                           \
  float Ax=V1[i0]-V0[i0];                                  \
  float Ay=V1[i1]-V0[i1];                                  \
  if(edge_edge_test(V0,U0,U1,i0,i1,Ax,Ay)) return 1;      \
  if(edge_edge_test(V0,U1,U2,i0,i1,Ax,Ay)) return 1;      \
  if(edge_edge_test(V0,U2,U0,i0,i1,Ax,Ay)) return 1;      \
}

#define POINT_IN_TRI(V0,U0,U1,U2,i0,i1)                    \
{                                                           \
  float a=U1[i1]-U0[i1];                                   \
  float b=-(U1[i0]-U0[i0]);                                \
  float c=-a*U0[i0]-b*U0[i1];                              \
  float d0=a*V0[i0]+b*V0[i1]+c;                            \
  a=U2[i1]-U1[i1];                                         \
  b=-(U2[i0]-U1[i0]);                                      \
  c=-a*U1[i0]-b*U1[i1];                                    \
  float d1=a*V0[i0]+b*V0[i1]+c;                            \
  a=U0[i1]-U2[i1];                                         \
  b=-(U0[i0]-U2[i0]);                                      \
  c=-a*U2[i0]-b*U2[i1];                                    \
  float d2=a*V0[i0]+b*V0[i1]+c;                            \
  if(d0*d1>0.0f&&d0*d2>0.0f) return 1;                    \
}

static int coplanar_tri_tri(float N[3],
                            float V0[3], float V1[3], float V2[3],
                            float U0[3], float U1[3], float U2[3])
{
    float A[3];
    short i0,i1;
    A[0]=FABS(N[0]); A[1]=FABS(N[1]); A[2]=FABS(N[2]);
    if(A[0]>A[1]) {
        if(A[0]>A[2]) { i0=1; i1=2; }
        else          { i0=0; i1=1; }
    } else {
        if(A[2]>A[1]) { i0=0; i1=1; }
        else          { i0=0; i1=2; }
    }
    EDGE_AGAINST_TRI_EDGES(V0,V1,U0,U1,U2,i0,i1);
    EDGE_AGAINST_TRI_EDGES(V1,V2,U0,U1,U2,i0,i1);
    EDGE_AGAINST_TRI_EDGES(V2,V0,U0,U1,U2,i0,i1);
    POINT_IN_TRI(V0,U0,U1,U2,i0,i1);
    POINT_IN_TRI(U0,V0,V1,V2,i0,i1);
    return 0;
}

#define COMPUTE_INTERVALS(VV0,VV1,VV2,D0,D1,D2,D0D1,D0D2,isect0,isect1)    \
  if(D0D1>0.0f)        { ISECT(VV2,VV0,VV1,D2,D0,D1,isect0,isect1); }      \
  else if(D0D2>0.0f)   { ISECT(VV1,VV0,VV2,D1,D0,D2,isect0,isect1); }      \
  else if(D1*D2>0.0f||D0!=0.0f) { ISECT(VV0,VV1,VV2,D0,D1,D2,isect0,isect1); } \
  else if(D1!=0.0f)    { ISECT(VV1,VV0,VV2,D1,D0,D2,isect0,isect1); }      \
  else if(D2!=0.0f)    { ISECT(VV2,VV0,VV1,D2,D0,D1,isect0,isect1); }      \
  else { return coplanar_tri_tri(N1,V0,V1,V2,U0,U1,U2); }

// Exposed with C linkage so box.cpp can find it without name mangling
extern "C" int tri_tri_intersect(float V0[3], float V1[3], float V2[3],
                                 float U0[3], float U1[3], float U2[3])
{
    float E1[3],E2[3];
    float N1[3],N2[3],d1,d2;
    float du0,du1,du2,dv0,dv1,dv2;
    float D[3];
    float isect1[2],isect2[2];
    float du0du1,du0du2,dv0dv1,dv0dv2;
    short index;
    float vp0,vp1,vp2;
    float up0,up1,up2;
    float bb,cc,max2;

    SUB(E1,V1,V0); SUB(E2,V2,V0);
    CROSS(N1,E1,E2);
    d1=-DOT(N1,V0);
    du0=DOT(N1,U0)+d1; du1=DOT(N1,U1)+d1; du2=DOT(N1,U2)+d1;
    if(FABS(du0)<1e-5f) du0=0.0f;
    if(FABS(du1)<1e-5f) du1=0.0f;
    if(FABS(du2)<1e-5f) du2=0.0f;
    du0du1=du0*du1; du0du2=du0*du2;
    if(du0du1>0.0f&&du0du2>0.0f) return 0;

    SUB(E1,U1,U0); SUB(E2,U2,U0);
    CROSS(N2,E1,E2);
    d2=-DOT(N2,U0);
    dv0=DOT(N2,V0)+d2; dv1=DOT(N2,V1)+d2; dv2=DOT(N2,V2)+d2;
    if(FABS(dv0)<1e-5f) dv0=0.0f;
    if(FABS(dv1)<1e-5f) dv1=0.0f;
    if(FABS(dv2)<1e-5f) dv2=0.0f;
    dv0dv1=dv0*dv1; dv0dv2=dv0*dv2;
    if(dv0dv1>0.0f&&dv0dv2>0.0f) return 0;

    CROSS(D,N1,N2);
    max2=FABS(D[0]); index=0;
    bb=FABS(D[1]); cc=FABS(D[2]);
    if(bb>max2) { max2=bb; index=1; }
    if(cc>max2) { index=2; }

    vp0=V0[index]; vp1=V1[index]; vp2=V2[index];
    up0=U0[index]; up1=U1[index]; up2=U2[index];

    COMPUTE_INTERVALS(vp0,vp1,vp2,dv0,dv1,dv2,dv0dv1,dv0dv2,isect1[0],isect1[1]);
    COMPUTE_INTERVALS(up0,up1,up2,du0,du1,du2,du0du1,du0du2,isect2[0],isect2[1]);

    SORT(isect1[0],isect1[1]);
    SORT(isect2[0],isect2[1]);

    if(isect1[1]<isect2[0]||isect2[1]<isect1[0]) return 0;
    return 1;
}
