// Lean compiler output
// Module: SixBirdsNoGo.FiniteKLDPIExample
// Imports: public import Init public import SixBirdsNoGo.FiniteKLDPI public import SixBirdsNoGo.FiniteProbabilityCoreExample
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
uint8_t l_Rat_instDecidableLe(lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0___boxed(lean_object*, lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer;
lean_object* l_Nat_cast___at___00Dyadic_toRat_spec__0(lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2;
static uint8_t lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__1;
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(0u);
x_2 = l_Nat_cast___at___00Dyadic_toRat_spec__0(x_1);
return x_2;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__1() {
_start:
{
lean_object* x_1; uint8_t x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0;
x_2 = l_Rat_instDecidableLe(x_1, x_1);
return x_2;
}
}
static uint8_t _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2() {
_start:
{
uint8_t x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__1;
return x_1;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0;
return x_3;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0___boxed(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0(x_1, x_2);
lean_dec_ref(x_2);
lean_dec_ref(x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0() {
_start:
{
lean_object* x_1; 
x_1 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___lam__0___boxed), 2, 0);
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0;
return x_1;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPI(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPIExample(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPI(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2___closed__1();
lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___nativeDecide__2();
lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer = _init_lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_zeroLogLayer);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
