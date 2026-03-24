// Lean compiler output
// Module: SixBirdsNoGo.FiniteProbabilityCoreExample
// Imports: public import Init public import SixBirdsNoGo.FiniteProbabilityCore
#include <lean/lean.h>
#if defined(__clang__)
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wunused-label"
#elif defined(__GNUC__) && !defined(__CLANG__)
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#endif
#ifdef __cplusplus
extern "C" {
#endif
static uint8_t lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__7;
uint8_t l_Rat_instDecidableLe(lean_object*, lean_object*);
static uint8_t lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__1;
uint8_t l_instDecidableEqRat_decEq(lean_object*, lean_object*);
static uint8_t lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0;
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipState___boxed(lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw;
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pathLaw___redArg(lean_object*, lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_dirac___redArg(lean_object*);
uint8_t lean_nat_dec_eq(lean_object*, lean_object*);
lean_object* lean_nat_mod(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel(lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0;
lean_object* lean_nat_sub(lean_object*, lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_half;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3;
lean_object* l_Rat_div(lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___boxed(lean_object*);
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_massSum___redArg(lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_dirac(lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1;
lean_object* l_Nat_cast___at___00Dyadic_toRat_spec__0(lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipState(lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1;
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(1u);
x_2 = l_Nat_cast___at___00Dyadic_toRat_spec__0(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = l_Nat_cast___at___00Dyadic_toRat_spec__0(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0;
x_3 = l_Rat_div(x_2, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_half() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(0u);
x_2 = l_Nat_cast___at___00Dyadic_toRat_spec__0(x_1);
return x_2;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; uint8_t x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0;
x_3 = l_Rat_instDecidableLe(x_2, x_1);
return x_3;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1() {
_start:
{
uint8_t x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__1;
return x_1;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_dirac___redArg(lean_object* x_1) {
_start:
{
lean_object* x_2; lean_object* x_3; lean_object* x_4; lean_object* x_5; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_1);
lean_ctor_set(x_3, 1, x_2);
x_4 = lean_box(0);
x_5 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_5, 0, x_3);
lean_ctor_set(x_5, 1, x_4);
return x_5;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_dirac(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___redArg(x_2);
return x_3;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; uint8_t x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0;
x_3 = l_Rat_instDecidableLe(x_2, x_1);
return x_3;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1() {
_start:
{
uint8_t x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1___closed__0;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_mod(x_2, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = lean_unsigned_to_nat(1u);
x_3 = lean_nat_mod(x_2, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_box(0);
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3;
x_3 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1;
x_3 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_massSum___redArg(x_1);
return x_2;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__7() {
_start:
{
lean_object* x_1; lean_object* x_2; uint8_t x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6;
x_3 = l_instDecidableEqRat_decEq(x_2, x_1);
return x_3;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2() {
_start:
{
uint8_t x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__7;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5;
return x_1;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipState(lean_object* x_1) {
_start:
{
lean_object* x_2; uint8_t x_3; 
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_dec_eq(x_1, x_2);
if (x_3 == 1)
{
lean_object* x_4; 
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2;
return x_4;
}
else
{
lean_object* x_5; lean_object* x_6; uint8_t x_7; lean_object* x_8; 
x_5 = lean_unsigned_to_nat(1u);
x_6 = lean_nat_sub(x_1, x_5);
x_7 = lean_nat_dec_eq(x_6, x_2);
lean_dec(x_6);
x_8 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0;
return x_8;
}
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipState___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_flipState(x_1);
lean_dec(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___redArg(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_dirac___redArg(x_1);
return x_2;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel(lean_object* x_1) {
_start:
{
lean_object* x_2; uint8_t x_3; 
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_dec_eq(x_1, x_2);
if (x_3 == 1)
{
lean_object* x_4; 
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0;
return x_4;
}
else
{
lean_object* x_5; lean_object* x_6; uint8_t x_7; lean_object* x_8; 
x_5 = lean_unsigned_to_nat(1u);
x_6 = lean_nat_sub(x_1, x_5);
x_7 = lean_nat_dec_eq(x_6, x_2);
lean_dec(x_6);
x_8 = lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1;
return x_8;
}
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_flipKernel(x_1);
lean_dec(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; lean_object* x_4; 
x_1 = lean_unsigned_to_nat(1u);
x_2 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___boxed), 1, 0);
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo;
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_pathLaw___redArg(x_3, x_2, x_1);
return x_4;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; lean_object* x_4; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___boxed), 1, 0);
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo;
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_pathLaw___redArg(x_3, x_2, x_1);
return x_4;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0;
return x_1;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_half___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_half___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_half___closed__2);
lp_sixbirdsnogo_SixBirdsNoGo_half = _init_lp_sixbirdsnogo_SixBirdsNoGo_half();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_half);
lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1___closed__1();
lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_dirac___nativeDecide__1();
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1___closed__0();
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__1();
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__2);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__3);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__4);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__5);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__6);
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__7 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2___closed__7();
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo___nativeDecide__2();
lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo = _init_lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_uniformTwo);
lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_flipKernel___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw = _init_lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_oneStepPathLaw);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
