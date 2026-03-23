// Lean compiler output
// Module: SixBirdsNoGo.ArrowDPIExample
// Imports: public import Init public import SixBirdsNoGo.ArrowDPI public import SixBirdsNoGo.FiniteKLDPIExample public import SixBirdsNoGo.FiniteProbabilityCoreExample
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
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0;
lean_object* l_instDecidableEqRat___boxed(lean_object*, lean_object*);
static uint8_t lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__2;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1;
extern lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw;
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0(lean_object*, lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1;
uint8_t l_instDecidableEqProd___redArg(lean_object*, lean_object*, lean_object*, lean_object*);
uint8_t l_instDecidableEqList___redArg(lean_object*, lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0;
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_reversePathLaw___redArg(lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___boxed(lean_object*);
lean_object* lean_nat_mod(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_collapseObs(lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___boxed(lean_object*, lean_object*);
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_instDecidableEqPathState___boxed(lean_object*, lean_object*, lean_object*, lean_object*);
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_unsigned_to_nat(1u);
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_mod(x_2, x_1);
return x_3;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_collapseObs(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0;
return x_2;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_collapseObs(x_1);
lean_dec(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_instDecidableEqPathState___boxed), 4, 2);
lean_closure_set(x_2, 0, x_1);
lean_closure_set(x_2, 1, x_1);
return x_2;
}
}
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; lean_object* x_4; uint8_t x_5; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0;
x_4 = lean_alloc_closure((void*)(l_instDecidableEqRat___boxed), 2, 0);
x_5 = l_instDecidableEqProd___redArg(x_3, x_4, x_1, x_2);
return x_5;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___boxed(lean_object* x_1, lean_object* x_2) {
_start:
{
uint8_t x_3; lean_object* x_4; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0(x_1, x_2);
x_4 = lean_box(x_3);
return x_4;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0() {
_start:
{
lean_object* x_1; 
x_1 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___boxed), 2, 0);
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw;
x_2 = lean_unsigned_to_nat(2u);
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_reversePathLaw___redArg(x_2, x_1);
return x_3;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__2() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; uint8_t x_4; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw;
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0;
x_4 = l_instDecidableEqList___redArg(x_3, x_2, x_1);
return x_4;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1() {
_start:
{
uint8_t x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__2;
return x_1;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPIExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPIExample(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPIExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_collapseObs___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___lam__0___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1___closed__2();
lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_twoStepPathLaw__reversible___nativeDecide__1__1();
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
